"""
Runner de una corrida (una repetición de una configuración).

Modelo de carga (ADR-003): lazo cerrado, N procesos (uno por cliente, cada uno con su propia
conexión), sin pausas. Fases: warmup (no se registra) -> medición (se registra) . El cooldown
lo hace run_benchmarks.sh. Una consulta solo cuenta si empezó y terminó dentro de la ventana.

Durante toda la corrida se muestrean cada 1 s los contadores cgroup del contenedor del motor;
al final se consultan los KPIs en Prometheus. Todo se guarda en results/raw/<run_id>.json;
finalize.py convierte ese archivo en la fila del CSV.

Uso (dentro del contenedor runner):
  python -m benchmark_runner.runner --engine mongodb --profile PROFILE_A_BASELINE \
      --query-id Q1 --concurrency 10 --run-number 1 --run-id <id> --container-id <docker id>
"""
import argparse
import json
import multiprocessing as mp
import os
import sys
import time
import traceback

from . import cgroup, db, prom

ERROR_BACKOFF_S = 0.5


def worker(idx, engine, query_id, ready_q, start_ev, t0_val, t_end_val, out_q):
    recs = []
    ex = None
    try:
        ex = db.executor(engine, query_id)
        ready_q.put(("ok", idx))
    except Exception as e:  # noqa: BLE001
        ready_q.put(("fail", f"{idx}: {e!r}"))
    start_ev.wait()
    t0, t_end = t0_val.value, t_end_val.value
    while time.time() < t0:
        time.sleep(0.001)
    while True:
        st = time.time()
        if st >= t_end:
            break
        try:
            if ex is None:
                ex = db.executor(engine, query_id)
            ex.run(t_end - st)
            recs.append((st, time.time(), "ok", None))
        except Exception as e:  # noqa: BLE001
            en = time.time()
            kind, code = (ex.classify(e) if ex else ("error", None))
            if kind == "timeout" and en >= t_end - 1.0:
                kind = "cut"  # cortada por el fin de la ventana: no es falla
            recs.append((st, en, kind, str(code) if code is not None else type(e).__name__))
            if kind == "error":
                # Conexión posiblemente rota (p. ej. reinicio del motor tras OOM): reconectar.
                try:
                    if ex:
                        ex.close()
                except Exception:  # noqa: BLE001
                    pass
                ex = None
                time.sleep(ERROR_BACKOFF_S)
    if ex:
        ex.close()
    out_q.put((idx, recs))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", required=True, choices=["mongodb", "postgresql"])
    ap.add_argument("--profile", required=True)
    ap.add_argument("--query-id", required=True, choices=["Q1", "Q2_V1", "Q2_V2"])
    ap.add_argument("--concurrency", type=int, required=True)
    ap.add_argument("--run-number", type=int, required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--container-id", required=True)
    ap.add_argument("--warmup", type=int, default=int(os.environ.get("WARMUP_S", 60)))
    ap.add_argument("--measure", type=int, default=int(os.environ.get("MEASURE_S", 300)))
    ap.add_argument("--results", default=os.environ.get("RESULTS_DIR", "results"))
    a = ap.parse_args()

    raw_dir = os.path.join(a.results, "raw")
    os.makedirs(raw_dir, exist_ok=True)
    out_path = os.path.join(raw_dir, f"{a.run_id}.json")
    container_name = f"bench-{a.engine}"
    raw = {"run_id": a.run_id, "engine": a.engine, "profile": a.profile, "query_id": a.query_id,
           "concurrency": a.concurrency, "run_number": a.run_number, "container_id": a.container_id,
           "warmup_s": a.warmup, "measure_s": a.measure, "exception": None}

    try:
        return _run(a, raw, out_path, container_name)
    except Exception:  # noqa: BLE001  — siempre se deja el JSON crudo: la corrida no se pierde en silencio
        raw["exception"] = traceback.format_exc()
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(raw, f)
        print(f"[runner] {a.run_id}: EXCEPCIÓN\n{raw['exception']}")
        return 2


def _run(a, raw, out_path, container_name):
    cg = cgroup.Cgroup(a.container_id)
    raw["limits"] = cg.limits()
    raw["cgroup_found"] = cg.path is not None

    ctx = mp.get_context("fork")
    ready_q, out_q = ctx.Queue(), ctx.Queue()
    start_ev = ctx.Event()
    t0_val, t_end_val = ctx.Value("d", 0.0), ctx.Value("d", 0.0)
    procs = [ctx.Process(target=worker, args=(i, a.engine, a.query_id, ready_q, start_ev,
                                               t0_val, t_end_val, out_q), daemon=True)
             for i in range(a.concurrency)]
    for p in procs:
        p.start()

    fails = []
    for _ in procs:
        status, info = ready_q.get(timeout=120)
        if status != "ok":
            fails.append(info)
    raw["worker_connect_failures"] = fails

    t0 = time.time() + 1.0
    t_ms = t0 + a.warmup
    t_end = t_ms + a.measure
    t0_val.value, t_end_val.value = t0, t_end
    raw.update({"t0": t0, "t_measure_start": t_ms, "t_end": t_end})
    start_ev.set()

    samples = []
    spill_start = spill_end = None
    next_tick = t0
    try:
        while True:
            now = time.time()
            if now >= t_end:
                break
            if spill_start is None and now >= t_ms:
                try:
                    spill_start = db.spill_counters(a.engine)
                except Exception as e:  # noqa: BLE001
                    spill_start = {"error": repr(e)}
            s = cg.sample()
            samples.append([now] + ([s[k] for k in ("rss_bytes", "mem_current_bytes", "throttled_s",
                                                      "cpu_usage_s", "oom_kill", "nr_throttled")]
                                    if s else [None] * 6))
            next_tick += 1.0
            time.sleep(max(0.0, min(next_tick, t_end) - time.time()))

        # Muestra final exacta en t_end.
        s = cg.sample()
        samples.append([time.time()] + ([s[k] for k in ("rss_bytes", "mem_current_bytes", "throttled_s",
                                                         "cpu_usage_s", "oom_kill", "nr_throttled")]
                                        if s else [None] * 6))
        records = []
        deadline = time.time() + 60
        for _ in procs:
            try:
                _, recs = out_q.get(timeout=max(1, deadline - time.time()))
                records.extend(recs)
            except Exception:  # noqa: BLE001
                raw.setdefault("workers_lost", 0)
                raw["workers_lost"] += 1
        for p in procs:
            p.join(timeout=5)
            if p.is_alive():
                p.terminate()
        try:
            spill_end = db.spill_counters(a.engine)
        except Exception as e:  # noqa: BLE001
            spill_end = {"error": repr(e)}

        time.sleep(3)  # margen para el último scrape de Prometheus (1 s)
        raw["prometheus"] = prom.collect(a.container_id, t_ms, t_end)
        raw["records"] = records
    except Exception:  # noqa: BLE001
        raw["exception"] = traceback.format_exc()
        for p in procs:
            if p.is_alive():
                p.terminate()
    raw["samples_cols"] = ["t", "rss_bytes", "mem_current_bytes", "throttled_s", "cpu_usage_s",
                           "oom_kill", "nr_throttled"]
    raw["samples"] = samples
    raw["spill_start"], raw["spill_end"] = spill_start, spill_end

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(raw, f)
    ok = sum(1 for r in raw.get("records", []) if r[2] == "ok" and r[0] >= t_ms and r[1] <= t_end)
    print(f"[runner] {a.run_id}: {ok} consultas completadas en la ventana -> {out_path}")
    return 0 if raw["exception"] is None else 2


if __name__ == "__main__":
    sys.exit(main())
