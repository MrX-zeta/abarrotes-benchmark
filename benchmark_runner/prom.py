"""Consultas a Prometheus (fuente principal de los KPIs de contenedor, playbook sección 7).

Nota de nombres: el KPI `container_memory_rss_bytes` del playbook corresponde a la métrica
`container_memory_rss` de cAdvisor (unidad: bytes). `container_cpu_cfs_throttled_seconds_total`
tiene el mismo nombre en cAdvisor.
"""
import os

import requests

URL = os.environ.get("PROMETHEUS_URL", "http://localhost:9090")


def _instant(expr, t):
    r = requests.get(f"{URL}/api/v1/query", params={"query": expr, "time": t}, timeout=10)
    r.raise_for_status()
    res = r.json()["data"]["result"]
    if not res:
        return None
    return float(res[0]["value"][1])


def _range(expr, start, end, step=1):
    r = requests.get(f"{URL}/api/v1/query_range",
                     params={"query": expr, "start": start, "end": end, "step": step}, timeout=30)
    r.raise_for_status()
    res = r.json()["data"]["result"]
    if not res:
        return []
    return [(float(t), float(v)) for t, v in res[0]["values"]]


def collect(container_id, t_start, t_end):
    """KPIs del contenedor en la ventana de medición [t_start, t_end] (epoch s).

    cAdvisor corre en modo cgroup crudo (ver docker-compose.yml): el contenedor se identifica por
    la etiqueta id="/docker/<container_id>" (o ".../docker-<id>.scope" con el driver systemd).
    """
    sel = f'{{id=~".*{container_id}.*"}}'
    win = max(1, int(round(t_end - t_start)))
    out = {"available": False}
    try:
        thr_start = _instant(f"container_cpu_cfs_throttled_seconds_total{sel}", t_start)
        thr_end = _instant(f"container_cpu_cfs_throttled_seconds_total{sel}", t_end)
        resets = _instant(f"resets(container_cpu_cfs_throttled_seconds_total{sel}[{win}s])", t_end)
        rss_max = _instant(f"max_over_time(container_memory_rss{sel}[{win}s])", t_end)
        out.update({
            "throttled_start_s": thr_start,
            "throttled_end_s": thr_end,
            "throttled_resets": resets,
            "rss_max_bytes": rss_max,
            "rss_series": _range(f"container_memory_rss{sel}", t_start, t_end),
            "throttled_series": _range(f"container_cpu_cfs_throttled_seconds_total{sel}", t_start, t_end),
        })
        out["available"] = thr_start is not None and thr_end is not None and rss_max is not None
    except Exception as e:  # noqa: BLE001
        out["error"] = repr(e)
    return out
