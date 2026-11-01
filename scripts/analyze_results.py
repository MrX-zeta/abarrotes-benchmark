#!/usr/bin/env python3
"""
analyze_results.py — Consolida y resume las mediciones para el reporte (playbook 8.3).

Entradas : results/csv/mediciones.csv, results/raw/*.json, results/plan.csv
Salidas  :
  entregables/mediciones.csv                      CSV consolidado (esquema 8.2 intacto)
  entregables/reporte/tablas_resumen.md           Sección 3: mediana [mín–máx] por configuración + estados
  entregables/reporte/m3_huella.md                M3: CPU y memoria por cada 1 000 documentos
  entregables/reporte/figuras/*.png               Sección 4: P99 vs concurrencia, throttling vs QPS, curva RSS
  entregables/evidencias/baseline/verificacion_baseline.md   Sección 2
  entregables/evidencias/spill_oom/eventos.md     Sección 6: corridas con spill / oom / error y su evidencia

Resumen de repeticiones (ADR-001): mediana de las 3 observaciones con rango mínimo–máximo;
estados y disk_spill como frecuencias.
"""
import argparse
import glob
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

COLS = ["timestamp_epoch", "engine", "profile", "query_id", "concurrency", "run_number",
        "throughput_qps", "latency_p50_ms", "latency_p95_ms", "latency_p99_ms",
        "cpu_throttled_seconds", "max_rss_mb", "disk_spill", "status"]
NUM = ["throughput_qps", "latency_p50_ms", "latency_p95_ms", "latency_p99_ms", "cpu_throttled_seconds", "max_rss_mb"]
PROFILES = ["PROFILE_A_BASELINE", "PROFILE_B_MEDIUM", "PROFILE_C_SEVERE"]
QUERIES = ["Q1", "Q2_V1", "Q2_V2"]
ENGINES = ["mongodb", "postgresql"]
COLORS = {"mongodb": "#2a7a52", "postgresql": "#33608f"}
DOCS = 500_000


def fmt(x, nd=1):
    return "—" if pd.isna(x) else f"{x:,.{nd}f}"


def cell(g, col, nd=1):
    v = g[col].dropna()
    if v.empty:
        return "—"
    return f"{fmt(v.median(), nd)} [{fmt(v.min(), nd)}–{fmt(v.max(), nd)}]"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results")
    ap.add_argument("--out", default="entregables")
    a = ap.parse_args()
    rep_dir = os.path.join(a.out, "reporte")
    fig_dir = os.path.join(rep_dir, "figuras")
    for d in (fig_dir, os.path.join(a.out, "evidencias", "baseline"), os.path.join(a.out, "evidencias", "spill_oom")):
        os.makedirs(d, exist_ok=True)

    df = pd.read_csv(os.path.join(a.results, "csv", "mediciones.csv"))
    assert list(df.columns) == COLS, f"El CSV no tiene el esquema 8.2: {list(df.columns)}"
    # Si una corrida se finalizó dos veces, se conserva la última fila.
    df = df.drop_duplicates(subset=["engine", "profile", "query_id", "concurrency", "run_number"], keep="last")
    df["disk_spill"] = df["disk_spill"].astype(str).str.lower().eq("true")
    order = {(e, p, q, c, r): i for i, (e, p, q, c, r) in enumerate(
        [(e, p, q, c, r) for e in ENGINES for p in PROFILES for q in QUERIES for c in (1, 10, 50) for r in (1, 2, 3)])}
    df["_o"] = [order.get(k, 1e9) for k in zip(df.engine, df.profile, df.query_id, df.concurrency, df.run_number)]
    df = df.sort_values("_o").drop(columns="_o")
    out_csv = os.path.join(a.out, "mediciones.csv")
    df_out = df.copy()
    df_out["disk_spill"] = df_out["disk_spill"].map({True: "true", False: "false"})
    df_out.to_csv(out_csv, index=False, columns=COLS, lineterminator="\n", float_format="%.3f")
    # pandas puede escribir los booleanos como TRUE/FALSE: se normalizan a true/false (mismo formato que el runner).
    with open(out_csv, encoding="utf-8") as f:
        lines = f.read().splitlines()
    fixed = [lines[0]] + [",".join(c.lower() if i == 12 else c for i, c in enumerate(l.split(","))) for l in lines[1:]]
    with open(out_csv, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(fixed) + "\n")

    # Datos extra de los JSON crudos (CPU usada, consultas ok, notas).
    extra = {}
    for p in glob.glob(os.path.join(a.results, "raw", "*.json")):
        try:
            with open(p, encoding="utf-8") as f:
                r = json.load(f)
        except Exception:  # noqa: BLE001
            continue
        fin = r.get("final") or {}
        extra[(r["engine"], r["profile"], r["query_id"], r["concurrency"], r["run_number"])] = {
            "cpu_usage_s": fin.get("cpu_usage_s_ventana"), "ok": fin.get("consultas_ok"),
            "notas": fin.get("notas", []), "fuente": fin.get("fuente_kpis"), "run_id": r["run_id"],
            "samples": r.get("samples"), "cols": r.get("samples_cols"), "t_ms": r.get("t_measure_start"),
            "t0": r.get("t0"), "t_end": r.get("t_end")}

    # ---------------------------------------------------------------- Sección 3: tablas resumen
    n_exp = 162
    lines = ["# Resultados consolidados (sección 3)", "",
             f"Filas en el CSV: **{len(df)}** de {n_exp} esperadas. Valores: mediana [mín–máx] de las repeticiones (ADR-001).", "",
             "Estados: " + ", ".join(f"`{k}`={v}" for k, v in df.status.value_counts().items()), ""]
    for q in QUERIES:
        lines += [f"## {q}", "",
                  "| Motor | Perfil | Conc. | n | QPS | P50 ms | P95 ms | P99 ms | Throttling s | RSS máx MB | Spill | Estados |",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for p in PROFILES:
            for e in ENGINES:
                for c in (1, 10, 50):
                    g = df[(df.engine == e) & (df.profile == p) & (df.query_id == q) & (df.concurrency == c)]
                    if g.empty:
                        continue
                    est = ", ".join(f"{k}:{v}" for k, v in g.status.value_counts().items())
                    lines.append(f"| {e} | {p.split('_')[1]} | {c} | {len(g)} | {cell(g, 'throughput_qps', 2)} | "
                                 f"{cell(g, 'latency_p50_ms')} | {cell(g, 'latency_p95_ms')} | {cell(g, 'latency_p99_ms')} | "
                                 f"{cell(g, 'cpu_throttled_seconds', 2)} | {cell(g, 'max_rss_mb')} | "
                                 f"{int(g.disk_spill.sum())}/{len(g)} | {est} |")
        lines.append("")
    with open(os.path.join(rep_dir, "tablas_resumen.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    # ---------------------------------------------------------------- M3: huella por 1 000 documentos
    m3 = ["# M3 — Huella por cada 1 000 documentos procesados", "",
          "Definición (ADR-003): documentos procesados = consultas completadas × 500 000 (cada consulta evalúa "
          "la colección completa). CPU = segundos de CPU del cgroup del motor en la ventana de 300 s. "
          "Memoria = max_rss_mb / 500. Mediana de las repeticiones.", "",
          "| Motor | Perfil | Consulta | Conc. | CPU ms / 1 000 docs | RSS MB / 1 000 docs |", "|---|---|---|---|---|---|"]
    for e in ENGINES:
        for p in PROFILES:
            for q in QUERIES:
                for c in (1, 10, 50):
                    vals, rss = [], []
                    for r in (1, 2, 3):
                        x = extra.get((e, p, q, c, r))
                        row = df[(df.engine == e) & (df.profile == p) & (df.query_id == q) & (df.concurrency == c) & (df.run_number == r)]
                        if x and x.get("cpu_usage_s") and x.get("ok"):
                            vals.append(1000 * x["cpu_usage_s"] / (x["ok"] * DOCS / 1000))
                        if not row.empty and not pd.isna(row.max_rss_mb.iloc[0]):
                            rss.append(row.max_rss_mb.iloc[0] / (DOCS / 1000))
                    if vals or rss:
                        m3.append(f"| {e} | {p.split('_')[1]} | {q} | {c} | "
                                  f"{fmt(np.median(vals), 3) if vals else '—'} | {fmt(np.median(rss), 4) if rss else '—'} |")
    with open(os.path.join(rep_dir, "m3_huella.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(m3) + "\n")

    med = df.groupby(["engine", "profile", "query_id", "concurrency"])[NUM].median().reset_index()

    # ---------------------------------------------------------------- Figura: P99 vs concurrencia
    fig, axes = plt.subplots(len(QUERIES), len(PROFILES), figsize=(13, 10), sharex=True)
    for i, q in enumerate(QUERIES):
        for j, p in enumerate(PROFILES):
            ax = axes[i][j]
            has = False
            for e in ENGINES:
                g = med[(med.engine == e) & (med.profile == p) & (med.query_id == q)].sort_values("concurrency")
                g = g[g.latency_p99_ms > 0]
                if not g.empty:
                    has = True
                    ax.plot(g.concurrency, g.latency_p99_ms, marker="o", color=COLORS[e], label=e)
            ax.set_xscale("log")
            ax.set_xlim(0.8, 65)
            ax.set_xticks([1, 10, 50], ["1", "10", "50"])
            if has:
                ax.set_yscale("log")
            else:
                ax.text(0.5, 0.5, "sin consultas completadas", ha="center", va="center", transform=ax.transAxes, color="#888")
            ax.grid(alpha=0.3, which="both")
            ax.set_title(f"{q} · {p.replace('PROFILE_', '')}", fontsize=10)
            if j == 0:
                ax.set_ylabel("P99 (ms, log)")
            if i == len(QUERIES) - 1:
                ax.set_xlabel("Clientes concurrentes")
    axes[0][0].legend()
    fig.suptitle("Latencia P99 vs concurrencia (mediana de 3 repeticiones)")
    fig.tight_layout()
    fig.savefig(os.path.join(fig_dir, "p99_vs_concurrencia.png"), dpi=130)
    plt.close(fig)

    # ---------------------------------------------------------------- Figura: throttling vs QPS
    fig, axes = plt.subplots(1, len(QUERIES), figsize=(14, 4.5))
    markers = {"PROFILE_A_BASELINE": "o", "PROFILE_B_MEDIUM": "s", "PROFILE_C_SEVERE": "^"}
    for i, q in enumerate(QUERIES):
        ax = axes[i]
        for e in ENGINES:
            for p in PROFILES:
                g = df[(df.engine == e) & (df.profile == p) & (df.query_id == q)]
                ax.scatter(g.cpu_throttled_seconds, g.throughput_qps, color=COLORS[e], marker=markers[p],
                           alpha=0.75, label=f"{e} · {p.split('_')[1]}")
        ax.set_title(q)
        ax.set_xlabel("Throttling CFS en la ventana (s)")
        ax.set_ylabel("Throughput (QPS)")
        ax.grid(alpha=0.3)
    axes[0].legend(fontsize=7)
    fig.suptitle("Throttling de CPU vs throughput (cada punto = 1 repetición)")
    fig.tight_layout()
    fig.savefig(os.path.join(fig_dir, "throttling_vs_qps.png"), dpi=130)
    plt.close(fig)

    # ---------------------------------------------------------------- Figura: curva RSS (c=50, rep 1)
    fig, axes = plt.subplots(len(QUERIES), len(PROFILES), figsize=(13, 10), sharex=True)
    for i, q in enumerate(QUERIES):
        for j, p in enumerate(PROFILES):
            ax = axes[i][j]
            for e in ENGINES:
                x = extra.get((e, p, q, 50, 1))
                if not x or not x.get("samples"):
                    continue
                ci = {c: k for k, c in enumerate(x["cols"])}
                pts = [(s[ci["t"]] - x["t0"], s[ci["rss_bytes"]] / 1e6) for s in x["samples"] if s[ci["rss_bytes"]] is not None]
                if pts:
                    ax.plot(*zip(*pts), color=COLORS[e], label=e, lw=1.2)
            if extra:
                ax.axvspan(0, 60, color="#999", alpha=0.12)
            ax.set_title(f"{q} · {p.replace('PROFILE_', '')} · c=50", fontsize=10)
            ax.grid(alpha=0.3)
            if j == 0:
                ax.set_ylabel("RSS (MB)")
            if i == len(QUERIES) - 1:
                ax.set_xlabel("Segundos desde el inicio (sombreado = warmup)")
    axes[0][0].legend()
    fig.suptitle("Curva RSS del contenedor del motor (repetición 1, 50 clientes)")
    fig.tight_layout()
    fig.savefig(os.path.join(fig_dir, "curva_rss.png"), dpi=130)
    plt.close(fig)

    # ---------------------------------------------------------------- Sección 2: baseline
    base = df[df.profile == "PROFILE_A_BASELINE"]
    bl = ["# Verificación del baseline (perfil A, sección 2)", "",
          "Criterio: el perfil A debe estar libre de contención: throttling ≈ 0 s en la ventana de 300 s, "
          "sin spill y sin OOM.", "",
          "| Motor | Consulta | Conc. | Throttling s (mediana [mín–máx]) | Throttling / 300 s | Spill | Estados |",
          "|---|---|---|---|---|---|---|"]
    for e in ENGINES:
        for q in QUERIES:
            for c in (1, 10, 50):
                g = base[(base.engine == e) & (base.query_id == q) & (base.concurrency == c)]
                if g.empty:
                    continue
                pct = g.cpu_throttled_seconds.median() / 300 * 100 if g.cpu_throttled_seconds.notna().any() else np.nan
                bl.append(f"| {e} | {q} | {c} | {cell(g, 'cpu_throttled_seconds', 3)} | {fmt(pct, 2)} % | "
                          f"{int(g.disk_spill.sum())}/{len(g)} | {', '.join(f'{k}:{v}' for k, v in g.status.value_counts().items())} |")
    thr_ok = base.cpu_throttled_seconds.fillna(0).max() < 3 if not base.empty else False
    bl += ["", f"Throttling máximo observado en A: **{fmt(base.cpu_throttled_seconds.max(), 3)} s** "
               f"({'cumple' if thr_ok else 'REVISAR'}: umbral 1 % de la ventana = 3 s).",
           f"Corridas de A con spill: **{int(base.disk_spill.sum())}**; con oom/error: "
           f"**{int(base.status.isin(['oom', 'error']).sum())}**."]
    with open(os.path.join(a.out, "evidencias", "baseline", "verificacion_baseline.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(bl) + "\n")

    # ---------------------------------------------------------------- Sección 6: eventos
    ev = ["# Eventos de spill, OOM y error (sección 6)", "",
          "Cada fila apunta a su evidencia: `results/logs/<run_id>.log`, `results/limits/<run_id>.post.json` "
          "y `results/raw/<run_id>.json` (campo `final.notas`).", "",
          "| run_id | Estado | Spill | Notas |", "|---|---|---|---|"]
    for _, r in df[(df.status != "ok") | df.disk_spill].iterrows():
        x = extra.get((r.engine, r.profile, r.query_id, r.concurrency, r.run_number), {})
        ev.append(f"| {x.get('run_id', '?')} | {r.status} | {str(r.disk_spill).lower()} | "
                  f"{'; '.join(x.get('notas', []))[:300]} |")
    if len(ev) == 5:
        ev.append("| — | — | — | Ninguna corrida con spill, OOM o error |")
    fuentes = pd.Series([v.get("fuente") for v in extra.values()]).value_counts().to_dict()
    ev += ["", f"Fuente de los KPIs de contenedor por corrida: {fuentes}"]
    with open(os.path.join(a.out, "evidencias", "spill_oom", "eventos.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(ev) + "\n")

    print(f"consolidado: {len(df)} filas -> {out_csv}")
    print(f"tablas, M3, figuras, baseline y eventos -> {a.out}/")


if __name__ == "__main__":
    main()
