#!/usr/bin/env bash
# run_benchmarks.sh — Automatización de la matriz de mediciones (playbook 8.1).
#
# Uso (desde la raíz del proyecto, en una terminal Linux/WSL2 con Docker):
#   ./run_benchmarks.sh check     Verifica Docker, cgroups v2, CPUs y memoria
#   ./run_benchmarks.sh setup     Construye el runner, levanta telemetría, genera y carga el dataset, crea el plan
#   ./run_benchmarks.sh smoke     Prueba rápida (ventanas cortas) de ambos motores y las 3 consultas -> results/smoke/
#   ./run_benchmarks.sh pilot     Celda piloto con los tiempos oficiales -> results/pilot/
#   ./run_benchmarks.sh matrix    Las 162 ejecuciones (reanuda donde se quedó)
#   ./run_benchmarks.sh explain   Planes de ejecución por motor y perfil (+ consulta exploratoria sin LIMIT)
#   ./run_benchmarks.sh analyze   CSV consolidado, tablas, figuras y verificación del baseline
#   ./run_benchmarks.sh all       matrix + explain + analyze (para dejarlo corriendo)
#   ./run_benchmarks.sh status    Avance de la matriz
#
# Ciclo de cada corrida (playbook 6): recrear contenedor con el perfil -> flush de caché
# -> warmup 60 s -> medición 300 s -> cooldown 60 s. Un solo motor encendido a la vez.
set -uo pipefail
cd "$(dirname "$0")"

[ -f .env ] || cp .env.example .env

# Docker Desktop configura en WSL el ayudante de credenciales "desktop.exe"; si la interoperabilidad
# WSL->Windows falla ("exec format error"), ningún pull funciona. Las imágenes son públicas: se usa
# una copia de la configuración de Docker sin ayudante de credenciales (los plugins se conservan).
BENCH_DOCKER_CONFIG="$HOME/.docker-bench"
mkdir -p "$BENCH_DOCKER_CONFIG"
python3 - "$HOME/.docker/config.json" "$BENCH_DOCKER_CONFIG/config.json" <<'PY' 2>/dev/null || echo '{}' > "$BENCH_DOCKER_CONFIG/config.json"
import json, os, sys
src, dst = sys.argv[1], sys.argv[2]
cfg = json.load(open(src)) if os.path.exists(src) else {}
for k in ("credsStore", "credHelpers", "auths"):
    cfg.pop(k, None)
json.dump(cfg, open(dst, "w"))
PY
[ -e "$BENCH_DOCKER_CONFIG/cli-plugins" ] || { [ -d "$HOME/.docker/cli-plugins" ] && ln -s "$HOME/.docker/cli-plugins" "$BENCH_DOCKER_CONFIG/cli-plugins"; }
export DOCKER_CONFIG="$BENCH_DOCKER_CONFIG"
set -a; . ./.env; set +a

WARMUP_S=${WARMUP_S:-60}
MEASURE_S=${MEASURE_S:-300}
COOLDOWN_S=${COOLDOWN_S:-60}
RESULTS_DIR=${RESULTS_DIR:-results}
export WARMUP_S MEASURE_S COOLDOWN_S RESULTS_DIR
DC="docker compose"

mkdirs() { mkdir -p "$RESULTS_DIR"/{raw,csv,explain,logs,limits,host,prometheus}; }
mkdirs
log() { echo "[$(date '+%F %T')] $*" | tee -a "$RESULTS_DIR/run.log"; }
die() { log "ERROR: $*"; exit 1; }

load_profile() { set -a; . "profiles/$1.env"; set +a; }

runner() {
  $DC run --rm -T -e RESULTS_DIR -e WARMUP_S -e MEASURE_S runner "$@" </dev/null
}

engine_up() {  # engine profile
  local engine=$1 other
  load_profile "$2"
  [ "$engine" = mongodb ] && other=postgresql || other=mongodb
  docker rm -f "bench-$other" >/dev/null 2>&1 || true
  $DC up -d --force-recreate --no-deps "$engine" </dev/null >/dev/null 2>&1 || $DC up -d --force-recreate --no-deps "$engine" </dev/null
}

drop_caches() {
  docker run --rm --privileged alpine:3.20 sh -c 'sync; echo 3 > /proc/sys/vm/drop_caches' </dev/null
}

run_one() {  # engine profile query_id concurrency run_number run_id
  local engine=$1 profile=$2 qid=$3 conc=$4 rep=$5 rid=$6
  if [ -f "$RESULTS_DIR/csv/$rid.csv" ]; then log "omitida (ya existe): $rid"; return 0; fi
  log "INICIO $rid  [$engine $profile $qid c=$conc r=$rep]"
  engine_up "$engine" "$profile" || log "WARN: no se pudo recrear bench-$engine"
  runner python -m benchmark_runner.ready --engine "$engine" || log "WARN: $engine no respondió"
  drop_caches || log "WARN: drop_caches falló"
  local cid start_iso
  cid=$(docker inspect -f '{{.Id}}' "bench-$engine" 2>/dev/null || echo unknown)
  docker inspect "bench-$engine" > "$RESULTS_DIR/limits/$rid.pre.json" 2>/dev/null || echo '[]' > "$RESULTS_DIR/limits/$rid.pre.json"
  start_iso=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  runner python -m benchmark_runner.runner --engine "$engine" --profile "$profile" --query-id "$qid" \
    --concurrency "$conc" --run-number "$rep" --run-id "$rid" --container-id "$cid" \
    || log "WARN: el runner terminó con error en $rid (se registrará como error)"
  docker inspect "bench-$engine" > "$RESULTS_DIR/limits/$rid.post.json" 2>/dev/null || echo '[]' > "$RESULTS_DIR/limits/$rid.post.json"
  docker logs --since "$start_iso" "bench-$engine" > "$RESULTS_DIR/logs/$rid.log" 2>&1 || true
  runner python -m benchmark_runner.finalize --run-id "$rid" || log "ERROR: finalize falló en $rid"
  log "FIN $rid; cooldown ${COOLDOWN_S}s"
  sleep "$COOLDOWN_S"
}

cmd_check() {
  command -v docker >/dev/null 2>&1 || die "No existe el comando docker en esta distribución WSL. Activa Docker Desktop > Settings > Resources > WSL integration > Ubuntu (Apply & restart)."
  local i
  for i in $(seq 1 36); do docker info >/dev/null 2>&1 && break; log "Esperando a Docker Desktop ($((i * 5)) s)..."; sleep 5; done
  docker info >/dev/null 2>&1 || die "Docker no responde tras 3 min: $(docker info 2>&1 | tail -2 | tr '\n' ' ')"
  local cg ncpu mem
  cg=$(docker info -f '{{.CgroupVersion}}')
  ncpu=$(docker info -f '{{.NCPU}}')
  mem=$(docker info -f '{{.MemTotal}}')
  log "Docker $(docker version -f '{{.Server.Version}}') | cgroups v$cg | CPUs VM: $ncpu | RAM VM: $((mem / 1024 / 1024)) MiB"
  [ "$cg" = "2" ] || log "AVISO: el playbook pide cgroups v2 y Docker reporta v$cg"
  [ "$ncpu" -ge 16 ] || log "AVISO: la VM tiene $ncpu CPUs; ajusta DB_CPUSET/RUNNER_CPUSET/MONITOR_CPUSET en .env"
  [ "$((mem / 1024 / 1024 / 1024))" -ge 12 ] || log "AVISO: la VM tiene menos de 12 GiB; revisa .wslconfig"
  local free_gb
  free_gb=$(df -BG --output=avail . | tail -1 | tr -dc 0-9)
  log "Disco libre en el proyecto: ${free_gb} GB"
  log "Núcleos: motor=$DB_CPUSET runner=$RUNNER_CPUSET monitoreo=$MONITOR_CPUSET"
}

cmd_versions() {
  {
    echo "# Versiones exactas ($(date -u +%FT%TZ))"
    echo "docker_server=$(docker version -f '{{.Server.Version}}')"
    echo "compose=$($DC version --short)"
    for img in mongo:8.0.34 postgres:17.11 gcr.io/cadvisor/cadvisor:v0.52.1 prom/prometheus:v3.5.0 \
               prom/node-exporter:v1.9.1 alpine:3.20 abarrotes-runner:1.0; do
      echo "image $img $(docker image inspect -f '{{index .RepoDigests 0}}' "$img" 2>/dev/null || echo '(sin digest local)')"
    done
    echo "mongod: $(docker run --rm mongo:8.0.34 mongod --version 2>/dev/null | head -1)"
    echo "postgres: $(docker run --rm postgres:17.11 postgres --version 2>/dev/null)"
    echo "runner python libs:"; docker run --rm abarrotes-runner:1.0 pip freeze 2>/dev/null | grep -i -E 'pymongo|psycopg|numpy|pandas|matplotlib|requests'
  } > "$RESULTS_DIR/versions.txt"
  log "versiones -> $RESULTS_DIR/versions.txt"
}

cmd_setup() {
  cmd_check
  if [ "${SKIP_PULL:-0}" != 1 ]; then
    log "Descargando imágenes y construyendo el runner"
    $DC --profile mongodb --profile postgresql --profile monitoring pull || die "no se pudieron descargar imágenes"
    docker pull alpine:3.20 >/dev/null
    $DC build runner || die "no se pudo construir el runner"
  fi
  log "Levantando telemetría (cAdvisor, Node Exporter, Prometheus)"
  $DC --profile monitoring up -d || die "telemetría"
  bash scripts/collect_host_info.sh "$RESULTS_DIR/host/host_info.txt" || log "WARN: host info incompleta"
  cmd_versions
  if [ ! -s data/pedidos.ndjson ]; then
    log "Generando dataset (500 000 pedidos)"
    runner python synthetic_data_generator.py --out data/pedidos.ndjson || die "generador"
  else
    log "Dataset ya existe: data/pedidos.ndjson"
  fi
  runner python scripts/verify_dataset.py --data data/pedidos.ndjson --out "$RESULTS_DIR/dataset_verification.json" \
    || die "el dataset no pasa la verificación"
  log "Cargando MongoDB"
  engine_up mongodb PROFILE_A_BASELINE
  runner python scripts/load_mongodb.py | tee "$RESULTS_DIR/load_mongodb.json" || die "carga mongodb"
  log "Cargando PostgreSQL"
  engine_up postgresql PROFILE_A_BASELINE
  runner python scripts/load_postgresql.py | tee "$RESULTS_DIR/load_postgresql.json" || die "carga postgresql"
  docker rm -f bench-postgresql >/dev/null 2>&1
  runner python scripts/plan.py --results "$RESULTS_DIR" || die "plan"
  log "SETUP COMPLETO. Siguiente: ./run_benchmarks.sh smoke"
}

cmd_smoke() {
  export RESULTS_DIR=results/smoke WARMUP_S=10 MEASURE_S=30 COOLDOWN_S=5
  mkdirs
  $DC --profile monitoring up -d >/dev/null 2>&1
  for engine in mongodb postgresql; do
    for q in Q1 Q2_V1 Q2_V2; do
      run_one "$engine" PROFILE_C_SEVERE "$q" 10 1 "smoke_${engine}_C_${q}_c10_r1"
    done
  done
  docker rm -f bench-mongodb bench-postgresql >/dev/null 2>&1
  echo; echo "=== results/smoke/csv/mediciones.csv ==="; cat results/smoke/csv/mediciones.csv
}

cmd_pilot() {
  export RESULTS_DIR=results/pilot
  mkdirs
  $DC --profile monitoring up -d >/dev/null 2>&1
  run_one mongodb PROFILE_C_SEVERE Q1 10 1 "pilot_mongodb_C_Q1_c10_r1"
  docker rm -f bench-mongodb >/dev/null 2>&1
  echo; echo "=== results/pilot/csv/mediciones.csv ==="; cat results/pilot/csv/mediciones.csv
}

cmd_matrix() {
  [ -f "$RESULTS_DIR/plan.csv" ] || runner python scripts/plan.py --results "$RESULTS_DIR"
  $DC --profile monitoring up -d >/dev/null 2>&1
  local total done_n
  total=$(($(wc -l < "$RESULTS_DIR/plan.csv") - 1))
  log "MATRIZ: $total ejecuciones; ya completadas: $(ls "$RESULTS_DIR"/csv/*_r[123].csv 2>/dev/null | wc -l)"
  while IFS=, read -r order rid engine profile qid conc rep <&3; do
    [ "$order" = "order" ] && continue
    run_one "$engine" "$profile" "$qid" "$conc" "$rep" "$rid"
    done_n=$(ls "$RESULTS_DIR"/csv/*_r[123].csv 2>/dev/null | wc -l)
    log "AVANCE: $done_n / $total"
  done 3< "$RESULTS_DIR/plan.csv"
  docker rm -f bench-mongodb bench-postgresql >/dev/null 2>&1
  log "MATRIZ TERMINADA"
}

cmd_explain() {
  for engine in mongodb postgresql; do
    for profile in PROFILE_A_BASELINE PROFILE_B_MEDIUM PROFILE_C_SEVERE; do
      log "explain $engine $profile"
      engine_up "$engine" "$profile"
      runner python -m benchmark_runner.ready --engine "$engine"
      drop_caches
      runner python scripts/capture_explain.py --engine "$engine" --profile "$profile" \
        || log "WARN: explain $engine $profile"
    done
  done
  docker rm -f bench-mongodb bench-postgresql >/dev/null 2>&1
}

cmd_analyze() {
  runner python scripts/analyze_results.py --results "$RESULTS_DIR"
}

cmd_status() {
  local total done_n
  total=$(($(wc -l < "$RESULTS_DIR/plan.csv") - 1))
  done_n=$(ls "$RESULTS_DIR"/csv/*_r[123].csv 2>/dev/null | wc -l)
  echo "Completadas: $done_n / $total  (restan ~$(( (total - done_n) * 7 )) min)"
  tail -n 5 "$RESULTS_DIR/run.log"
}

case "${1:-}" in
  check) cmd_check ;;
  setup) cmd_setup ;;
  smoke) cmd_smoke ;;
  pilot) cmd_pilot ;;
  matrix) cmd_matrix ;;
  explain) cmd_explain ;;
  analyze) cmd_analyze ;;
  all) cmd_matrix; cmd_explain; cmd_analyze ;;
  status) cmd_status ;;
  versions) cmd_versions ;;
  *) sed -n '2,16p' "$0"; exit 1 ;;
esac
