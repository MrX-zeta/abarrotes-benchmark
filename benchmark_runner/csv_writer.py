"""Escritura del CSV con el esquema EXACTO del playbook 8.2 (no se agregan ni renombran columnas)."""
import csv
import os

COLUMNS = [
    "timestamp_epoch", "engine", "profile", "query_id", "concurrency", "run_number",
    "throughput_qps", "latency_p50_ms", "latency_p95_ms", "latency_p99_ms",
    "cpu_throttled_seconds", "max_rss_mb", "disk_spill", "status",
]
STATUSES = ("ok", "spill", "oom", "error")


def _fmt(v, nd=3):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        return f"{v:.{nd}f}"
    return str(v)


def validate(row):
    assert list(row.keys()) == COLUMNS, f"columnas inválidas: {list(row.keys())}"
    assert row["status"] in STATUSES, row["status"]
    assert row["engine"] in ("mongodb", "postgresql")
    assert row["query_id"] in ("Q1", "Q2_V1", "Q2_V2")


def append(path, row):
    validate(row)
    new = not os.path.exists(path) or os.path.getsize(path) == 0
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        if new:
            w.writerow(COLUMNS)
        w.writerow([_fmt(row[c]) for c in COLUMNS])


def write_single(path, row):
    if os.path.exists(path):
        os.remove(path)
    append(path, row)
