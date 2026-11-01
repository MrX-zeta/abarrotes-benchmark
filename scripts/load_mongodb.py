#!/usr/bin/env python3
"""Carga data/pedidos.ndjson en MongoDB (colección pedidos) y crea los índices del playbook:
índice simple en la fecha (creado_en ~ timestamp) y en el identificador (pedido_id ~ order_id)."""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from benchmark_runner import db  # noqa: E402

BATCH = 5000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/pedidos.ndjson")
    a = ap.parse_args()
    db.wait_ready("mongodb")
    client = db.mongo_client(socketTimeoutMS=None)
    coll = client[db.MONGO_DB][db.COLLECTION]
    coll.drop()
    t = time.time()
    batch, n = [], 0
    with open(a.data, encoding="utf-8") as f:
        for line in f:
            batch.append(json.loads(line))
            if len(batch) == BATCH:
                coll.insert_many(batch, ordered=False)
                n += len(batch)
                batch = []
                if n % 100_000 == 0:
                    print(f"  mongodb: {n:,}", flush=True)
    if batch:
        coll.insert_many(batch, ordered=False)
        n += len(batch)
    coll.create_index([("pedido_id", 1)], unique=True, name="idx_pedido_id")
    coll.create_index([("creado_en", 1)], name="idx_creado_en")
    print(json.dumps({"engine": "mongodb", "documentos": coll.count_documents({}),
                      "indices": sorted(coll.index_information()), "segundos": round(time.time() - t, 1)}))
    client.close()


if __name__ == "__main__":
    main()
