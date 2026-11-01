"""Espera a que el motor responda (sustituye al healthcheck dentro del contenedor)."""
import argparse
import sys

from . import db

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", required=True, choices=["mongodb", "postgresql"])
    ap.add_argument("--timeout", type=int, default=180)
    a = ap.parse_args()
    n = db.wait_ready(a.engine, a.timeout)
    print(f"[ready] {a.engine}: {n} documentos")
    sys.exit(0)
