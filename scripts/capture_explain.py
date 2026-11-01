#!/usr/bin/env python3
"""
capture_explain.py — Planes de ejecución para la sección 5 del reporte:
  MongoDB:    explain("executionStats") del pipeline
  PostgreSQL: EXPLAIN (ANALYZE, BUFFERS) de la consulta (texto y JSON)

Se ejecuta por motor y perfil (run_benchmarks.sh explain), con el contenedor recreado con los
límites del perfil y la caché del SO limpia. Incluye además la consulta EXPLORATORIA de Q2 sin
LIMIT (ADR-003, decisión 13), fuera de la matriz y fuera del CSV, para mostrar qué ocurre cuando
el motor sí tiene que ordenar todo el conjunto.
"""
import argparse
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from benchmark_runner import db  # noqa: E402

SHORT = {"PROFILE_A_BASELINE": "A", "PROFILE_B_MEDIUM": "B", "PROFILE_C_SEVERE": "C"}


def strip_limit_mongo(p):
    return [s for s in p if "$limit" not in s]


def strip_limit_sql(sql):
    return re.sub(r"\s*LIMIT\s+\d+\s*;?\s*$", ";", sql.strip(), flags=re.I)


def mongo_explain(pipeline, allow_disk):
    c = db.mongo_client(socketTimeoutMS=None)
    try:
        cmd = {"aggregate": db.COLLECTION, "pipeline": pipeline, "cursor": {}}
        if allow_disk is not None:
            cmd["allowDiskUse"] = allow_disk
        t = time.time()
        res = c[db.MONGO_DB].command({"explain": cmd, "verbosity": "executionStats"})
        return {"ok": True, "segundos": round(time.time() - t, 3), "explain": res}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": repr(e), "code": getattr(e, "code", None)}
    finally:
        c.close()


def pg_explain(sql, work_mem):
    out = {}
    try:
        with db.pg_connect() as conn:
            if work_mem:
                conn.execute(f"SET work_mem = '{work_mem}'")
            body = sql.strip().rstrip(";")
            t = time.time()
            txt = conn.execute(f"EXPLAIN (ANALYZE, BUFFERS) {body}").fetchall()
            out["segundos"] = round(time.time() - t, 3)
            out["texto"] = "\n".join(r[0] for r in txt)
            js = conn.execute(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {body}").fetchone()[0]
            out["json"] = js
            out["ok"] = True
    except Exception as e:  # noqa: BLE001
        out.update({"ok": False, "error": repr(e)})
    return out


def summarize_mongo(res):
    s = json.dumps(res.get("explain", {}), default=str)
    return {"usedDisk": '"usedDisk": true' in s, "COLLSCAN": "COLLSCAN" in s, "IXSCAN": "IXSCAN" in s,
            "error": res.get("error")}


def summarize_pg(res):
    t = res.get("texto", "")
    m = re.search(r"Sort Method: ([^\n]+)", t)
    return {"sort_method": m.group(1).strip() if m else None, "external_merge": "external merge" in t,
            "temp_buffers": "temp read" in t or "temp written" in t, "seq_scan": "Seq Scan" in t,
            "index_scan": "Index Scan" in t or "Bitmap Index Scan" in t, "error": res.get("error")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", required=True, choices=["mongodb", "postgresql"])
    ap.add_argument("--profile", required=True)
    ap.add_argument("--results", default=os.environ.get("RESULTS_DIR", "results"))
    a = ap.parse_args()
    out_dir = os.path.join(a.results, "explain")
    os.makedirs(out_dir, exist_ok=True)
    db.wait_ready(a.engine)
    resumen = {}
    for qid in ["Q1", "Q2_V1", "Q2_V2"]:
        q, opts = db.load_query(a.engine, qid)
        cases = [(qid, q)]
        if qid.startswith("Q2"):
            cases.append((f"{qid}_EXPLORATORIA_SIN_LIMIT",
                          strip_limit_mongo(q) if a.engine == "mongodb" else strip_limit_sql(q)))
        for name, query in cases:
            if a.engine == "mongodb":
                res = mongo_explain(query, opts["allowDiskUse"])
                summ = summarize_mongo(res)
            else:
                res = pg_explain(query, opts["work_mem"])
                summ = summarize_pg(res)
            base = f"{a.engine}_{SHORT.get(a.profile, a.profile)}_{name}"
            with open(os.path.join(out_dir, base + ".json"), "w", encoding="utf-8") as f:
                json.dump({"query": query, "opciones": opts, "resultado": res}, f, default=str, indent=2)
            if a.engine == "postgresql" and res.get("texto"):
                with open(os.path.join(out_dir, base + ".txt"), "w", encoding="utf-8") as f:
                    f.write(res["texto"] + "\n")
            resumen[name] = summ
            print(f"[explain] {base}: {summ}")
    with open(os.path.join(out_dir, f"{a.engine}_{SHORT.get(a.profile, a.profile)}_resumen.json"), "w",
              encoding="utf-8") as f:
        json.dump(resumen, f, indent=2, default=str)


if __name__ == "__main__":
    main()
