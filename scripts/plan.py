#!/usr/bin/env python3
"""
plan.py — Genera el orden de ejecución de la matriz y benchmark_metadata.json.

Matriz (ADR-001): 2 motores x 3 perfiles x {Q1, Q2_V1, Q2_V2} x {1, 10, 50} = 54 configuraciones,
x 3 repeticiones = 162 ejecuciones.

Orden (ADR-003, decisión 15): por bloques de repetición. Primero las 54 configuraciones de la
repetición 1 en orden aleatorio, luego las de la 2 y luego las de la 3. Semilla fija => el orden
es reproducible y queda guardado en results/plan.csv.
"""
import argparse
import csv
import json
import os
import random
from datetime import datetime, timezone

ENGINES = ["mongodb", "postgresql"]
PROFILES = ["PROFILE_A_BASELINE", "PROFILE_B_MEDIUM", "PROFILE_C_SEVERE"]
QUERIES = ["Q1", "Q2_V1", "Q2_V2"]
CONCURRENCY = [1, 10, 50]
REPS = [1, 2, 3]
PLAN_SEED = 20261031
SHORT = {"PROFILE_A_BASELINE": "A", "PROFILE_B_MEDIUM": "B", "PROFILE_C_SEVERE": "C"}


def run_id(e, p, q, c, r):
    return f"{e}_{SHORT[p]}_{q}_c{c}_r{r}"


def read_env(path):
    out = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                out[k] = v
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results")
    ap.add_argument("--metadata", default="entregables/benchmark_metadata.json")
    a = ap.parse_args()

    configs = [(e, p, q, c) for e in ENGINES for p in PROFILES for q in QUERIES for c in CONCURRENCY]
    rows, order = [], 0
    for r in REPS:
        block = configs[:]
        random.Random(PLAN_SEED + r).shuffle(block)
        for e, p, q, c in block:
            order += 1
            rows.append({"order": order, "run_id": run_id(e, p, q, c, r), "engine": e, "profile": p,
                         "query_id": q, "concurrency": c, "run_number": r})
    os.makedirs(a.results, exist_ok=True)
    with open(os.path.join(a.results, "plan.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    with open("queries/variants.json", encoding="utf-8") as f:
        variants = json.load(f)
    variants.pop("_descripcion", None)
    sha = None
    if os.path.exists("data/pedidos.ndjson.sha256"):
        sha = open("data/pedidos.ndjson.sha256", encoding="utf-8").read().split()[0]
    versions = open(os.path.join(a.results, "versions.txt"), encoding="utf-8").read() \
        if os.path.exists(os.path.join(a.results, "versions.txt")) else None
    env = read_env(".env")
    meta = {
        "generado_en": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "descripcion": "Ficha técnica del benchmark MongoDB vs PostgreSQL JSONB (tienda de abarrotes). "
                       "Complementa al CSV sin modificar su esquema (ADR-001).",
        "query_id": {
            "Q1": {"descripcion": "Unwind, Filter & Grouping (playbook 5.1)", "config": variants["Q1"]},
            "Q2_V1": {"descripcion": "Massive Sort & Top-K, variante sin spill permitido / 4MB (playbook 5.2)",
                      "config": variants["Q2_V1"]},
            "Q2_V2": {"descripcion": "Massive Sort & Top-K, variante con spill permitido / 64MB (playbook 5.2)",
                      "config": variants["Q2_V2"]},
        },
        "perfiles": {p: read_env(f"profiles/{p}.env") for p in PROFILES},
        "nucleos": {k: env.get(k) for k in ("DB_CPUSET", "RUNNER_CPUSET", "MONITOR_CPUSET")},
        "protocolo": {"warmup_s": 60, "medicion_s": 300, "cooldown_s": 60,
                      "flush": "sync; echo 3 > /proc/sys/vm/drop_caches (contenedor privilegiado en la VM de Docker)",
                      "concurrencias": CONCURRENCY, "repeticiones": len(REPS),
                      "configuraciones": len(configs), "ejecuciones": len(rows),
                      "orden": "bloques por repetición, aleatorio dentro del bloque", "semilla_orden": PLAN_SEED},
        "dataset": {"archivo": "data/pedidos.ndjson", "documentos": 500000, "semilla": 20261031, "sha256": sha},
        "csv": {"columnas": ["timestamp_epoch", "engine", "profile", "query_id", "concurrency", "run_number",
                             "throughput_qps", "latency_p50_ms", "latency_p95_ms", "latency_p99_ms",
                             "cpu_throttled_seconds", "max_rss_mb", "disk_spill", "status"],
                "max_rss_mb": "máximo de container_memory_rss en la ventana / 1 000 000",
                "cpu_throttled_seconds": "fin - inicio de container_cpu_cfs_throttled_seconds_total en la ventana",
                "status_prioridad": "oom > error > spill > ok"},
        "versiones": versions,
        "decisiones": ["docs/decisiones/ADR-001-criterios-de-interpretacion.md",
                       "docs/decisiones/ADR-002-dominio-y-equivalencia.md",
                       "docs/decisiones/ADR-003-decisiones-operativas.md"],
    }
    os.makedirs(os.path.dirname(a.metadata), exist_ok=True)
    with open(a.metadata, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"plan: {len(rows)} ejecuciones -> {a.results}/plan.csv ; metadata -> {a.metadata}")


if __name__ == "__main__":
    main()
