"""
finalize.py — Convierte results/raw/<run_id>.json en la fila del CSV (playbook 8.2) aplicando
ADR-001 (criterios) y ADR-003 (decisiones operativas).

  throughput_qps        consultas ok iniciadas y terminadas dentro de la ventana / duración
  latency_p50/95/99_ms  percentiles (numpy, método lineal) sobre TODAS las consultas ok de todos los clientes
  cpu_throttled_seconds diferencia fin - inicio de container_cpu_cfs_throttled_seconds_total en la ventana
  max_rss_mb            máximo de container_memory_rss en la ventana / 1 000 000
  disk_spill            true si el motor volcó a disco temporal en la ventana
  status                oom > error > spill > ok

Fuente: Prometheus/cAdvisor si tiene datos; si no, lectura directa del cgroup (mismos contadores).
La fuente usada queda en el JSON crudo ("final.fuente_kpis").
"""
import argparse
import json
import os
import re
import sys

import numpy as np

from . import csv_writer

MAX_FAIL_FRACTION = 0.05


def _window(samples, cols, t_ms, t_end):
    i = {c: k for k, c in enumerate(cols)}
    return [s for s in samples if t_ms - 0.5 <= s[i["t"]] <= t_end + 0.5], i


def compute(raw, inspect=None, log_text=""):
    t_ms, t_end = raw.get("t_measure_start"), raw.get("t_end")
    measure = raw.get("measure_s")
    notes = []
    recs = raw.get("records", [])
    in_win = [r for r in recs if t_ms is not None and r[0] >= t_ms and r[1] <= t_end]
    ok_lat = [(r[1] - r[0]) * 1000.0 for r in recs if r[2] == "ok" and t_ms is not None
              and r[0] >= t_ms and r[1] <= t_end]
    started = [r for r in recs if t_ms is not None and t_ms <= r[0] <= t_end]
    failed = [r for r in started if r[2] in ("error", "timeout")]
    cut = [r for r in started if r[2] == "cut"]
    err_codes = sorted({str(r[3]) for r in failed})

    # ----- KPIs de contenedor
    samples, idx = _window(raw.get("samples", []), raw.get("samples_cols", []), t_ms or 0, t_end or 0)
    valid = [s for s in samples if s[idx["throttled_s"]] is not None] if samples else []
    cg_thr = cg_rss = None
    counter_reset = False
    oom_kills = 0
    if valid:
        thr = [s[idx["throttled_s"]] for s in valid]
        cpu = [s[idx["cpu_usage_s"]] for s in valid if s[idx["cpu_usage_s"]] is not None]
        counter_reset = any(b < a for a, b in zip(thr, thr[1:])) or any(b < a for a, b in zip(cpu, cpu[1:]))
        cg_thr = thr[-1] - thr[0]
        rss = [s[idx["rss_bytes"]] for s in valid if s[idx["rss_bytes"]] is not None]
        cg_rss = max(rss) if rss else None
        oom = [s[idx["oom_kill"]] or 0 for s in valid]
        oom_kills = max(oom) - oom[0]
        cpu_used = (cpu[-1] - cpu[0]) if len(cpu) > 1 else None
    else:
        cpu_used = None
    missing_samples = bool(samples) and len(valid) < len(samples)

    p = raw.get("prometheus") or {}
    fuente = "cgroup"
    thr_s = cg_thr
    rss_b = cg_rss
    if p.get("available"):
        if (p.get("throttled_resets") or 0) > 0 or p["throttled_end_s"] < p["throttled_start_s"]:
            counter_reset = True
        else:
            fuente = "prometheus"
            thr_s = p["throttled_end_s"] - p["throttled_start_s"]
            rss_b = p["rss_max_bytes"]
    else:
        notes.append("prometheus sin datos: KPIs tomados del cgroup")

    # ----- Spill
    spill = False
    ss, se = raw.get("spill_start") or {}, raw.get("spill_end") or {}
    for k, v in se.items():
        if isinstance(v, (int, float)) and isinstance(ss.get(k), (int, float)) and v > ss[k]:
            if k in ("temp_files", "temp_bytes") or "spill" in k.lower() or "useddisk" in k.lower():
                spill = True
                notes.append(f"spill: {k} {ss[k]} -> {v}")
    if raw.get("engine") == "postgresql" and re.search(r"temporary file:", log_text):
        spill = True
        notes.append("spill: log 'temporary file'")
    if raw.get("engine") == "mongodb" and re.search(r'"usedDisk"\s*:\s*true', log_text):
        spill = True
        notes.append("spill: log usedDisk:true")

    # ----- OOM
    oom = oom_kills > 0
    st = (inspect or {}).get("State", {}) if inspect else {}
    if st.get("OOMKilled"):
        oom = True
        notes.append("docker inspect: OOMKilled")
    if inspect and not st.get("Running", True):
        oom = oom or st.get("ExitCode") == 137
        notes.append(f"contenedor detenido (ExitCode={st.get('ExitCode')})")
    if re.search(r"terminated by signal 9|Out of memory: Killed", log_text):
        oom = True
        notes.append("log: proceso terminado por señal 9 (OOM killer)")
    if counter_reset or missing_samples:
        notes.append("reinicio de contador o cgroup desaparecido durante la ventana")
        if not oom:
            oom = bool(st.get("OOMKilled")) or st.get("ExitCode") == 137

    # ----- Error
    error = False
    if raw.get("exception"):
        error = True
        notes.append("excepción del runner")
    if not ok_lat:
        error = True
        notes.append("ninguna consulta completada dentro de la ventana")
    if started and len(failed) / len(started) > MAX_FAIL_FRACTION:
        error = True
        notes.append(f"{len(failed)}/{len(started)} consultas fallidas (> {MAX_FAIL_FRACTION:.0%}); códigos {err_codes}")
    if (counter_reset or missing_samples) and not oom:
        error = True

    status = "oom" if oom else "error" if error else "spill" if spill else "ok"

    lat = np.array(ok_lat) if ok_lat else None
    row = {
        "timestamp_epoch": int(t_ms) if t_ms else None,
        "engine": raw["engine"],
        "profile": raw["profile"],
        "query_id": raw["query_id"],
        "concurrency": raw["concurrency"],
        "run_number": raw["run_number"],
        "throughput_qps": (len(ok_lat) / measure) if measure else None,
        "latency_p50_ms": float(np.percentile(lat, 50)) if lat is not None else None,
        "latency_p95_ms": float(np.percentile(lat, 95)) if lat is not None else None,
        "latency_p99_ms": float(np.percentile(lat, 99)) if lat is not None else None,
        "cpu_throttled_seconds": float(thr_s) if thr_s is not None and not counter_reset else None,
        "max_rss_mb": (float(rss_b) / 1_000_000) if rss_b is not None else None,
        "disk_spill": spill,
        "status": status,
    }
    extra = {
        "fuente_kpis": fuente,
        "consultas_ok": len(ok_lat),
        "consultas_iniciadas_en_ventana": len(started),
        "consultas_fallidas": len(failed),
        "consultas_cortadas_fin_ventana": len(cut),
        "codigos_error": err_codes,
        "cpu_usage_s_ventana": cpu_used,
        "oom_kill_delta": oom_kills,
        "cgroup_throttled_s": cg_thr,
        "cgroup_rss_max_bytes": cg_rss,
        "notas": notes,
    }
    return row, extra


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--results", default=os.environ.get("RESULTS_DIR", "results"))
    a = ap.parse_args()

    raw_path = os.path.join(a.results, "raw", f"{a.run_id}.json")
    with open(raw_path, encoding="utf-8") as f:
        raw = json.load(f)
    inspect = None
    ip = os.path.join(a.results, "limits", f"{a.run_id}.post.json")
    if os.path.exists(ip):
        with open(ip, encoding="utf-8") as f:
            data = json.load(f)
            inspect = data[0] if isinstance(data, list) and data else None
    log_text = ""
    lp = os.path.join(a.results, "logs", f"{a.run_id}.log")
    if os.path.exists(lp):
        with open(lp, encoding="utf-8", errors="replace") as f:
            log_text = f.read()

    row, extra = compute(raw, inspect, log_text)
    raw["final"] = {"row": row, **extra}
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(raw, f)

    csv_writer.write_single(os.path.join(a.results, "csv", f"{a.run_id}.csv"), row)
    csv_writer.append(os.path.join(a.results, "csv", "mediciones.csv"), row)
    print(f"[finalize] {a.run_id}: status={row['status']} qps={row['throughput_qps']} "
          f"p99={row['latency_p99_ms']} thr={row['cpu_throttled_seconds']} rss_mb={row['max_rss_mb']} "
          f"spill={row['disk_spill']} fuente={extra['fuente_kpis']} notas={extra['notas']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
