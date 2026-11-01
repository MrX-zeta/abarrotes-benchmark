#!/usr/bin/env python3
"""Carga data/pedidos.ndjson en PostgreSQL: pedidos(id UUID PRIMARY KEY, data JSONB) vía COPY,
y después crea el B-Tree sobre la fecha extraída (config/postgresql/indexes.sql)."""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from benchmark_runner import db  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/pedidos.ndjson")
    a = ap.parse_args()
    db.wait_ready("postgresql")
    t = time.time()
    with db.pg_connect() as conn:
        with open(os.path.join(db.ROOT, "config", "postgresql", "init.sql"), encoding="utf-8") as f:
            conn.execute(f.read())
        conn.execute("TRUNCATE pedidos")
        n = 0
        with conn.cursor() as cur:
            with cur.copy("COPY pedidos (id, data) FROM STDIN") as cp, open(a.data, encoding="utf-8") as f:
                for line in f:
                    line = line.rstrip("\n")
                    pid = line[len('{"pedido_id":"'):len('{"pedido_id":"') + 36]
                    cp.write_row((pid, line))
                    n += 1
                    if n % 100_000 == 0:
                        print(f"  postgresql: {n:,}", flush=True)
        with open(os.path.join(db.ROOT, "config", "postgresql", "indexes.sql"), encoding="utf-8") as f:
            sql = "\n".join(l for l in f.read().splitlines() if not l.strip().startswith("--"))
            for stmt in (s.strip() for s in sql.split(";")):
                if stmt:
                    conn.execute(stmt)
        cnt = conn.execute("SELECT count(*) FROM pedidos").fetchone()[0]
        bad = conn.execute("SELECT count(*) FROM pedidos WHERE id::text <> data->>'pedido_id'").fetchone()[0]
        idx = [r[0] for r in conn.execute("SELECT indexname FROM pg_indexes WHERE tablename='pedidos'")]
    if bad:
        sys.exit(f"ERROR: {bad} filas con id distinto de data->>'pedido_id'")
    print(json.dumps({"engine": "postgresql", "documentos": cnt, "indices": sorted(idx),
                      "segundos": round(time.time() - t, 1)}))


if __name__ == "__main__":
    main()
