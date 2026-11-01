#!/usr/bin/env python3
"""
verify_dataset.py — Verifica que el dataset cumple las propiedades del playbook (ADR-002/003)
y que ambos motores cargaron los mismos documentos.

Comprueba sobre el NDJSON:
  * número de documentos, profundidad máxima de anidamiento, promedio de líneas por pedido;
  * selectividad del filtro de Q1 (precio_unitario > 50) y número de grupos (ciudad x categoría);
  * candidatos de Q2 (estado = entregado y creado_en >= 2026-01-01).
Opcionalmente compara contra el conteo de MongoDB y PostgreSQL (--check-db).

Salida: JSON en stdout y en results/dataset_verification.json
"""
import argparse
import json
import os
import sys

FECHA_Q2 = "2026-01-01T00:00:00Z"


def depth(o, d=0):
    """Niveles de objeto anidado (los arreglos no suman nivel; sus elementos sí)."""
    if isinstance(o, dict):
        return max([depth(v, d + 1) for v in o.values()] + [d + 1])
    if isinstance(o, list):
        return max([depth(v, d) for v in o] + [d])
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/pedidos.ndjson")
    ap.add_argument("--out", default="results/dataset_verification.json")
    ap.add_argument("--check-db", action="store_true")
    ap.add_argument("--expected", type=int, default=500_000)
    args = ap.parse_args()

    n = lineas = lineas_q1 = q2 = max_depth = 0
    grupos = set()
    with open(args.data, encoding="utf-8") as f:
        for line in f:
            doc = json.loads(line)
            n += 1
            # Profundidad sin contar el nivel raíz del documento.
            max_depth = max(max_depth, depth(doc) - 1)
            ciudad = doc["sucursal"]["ubicacion"]["ciudad"]
            for li in doc["lineas"]:
                lineas += 1
                if li["precio_unitario"] > 50:
                    lineas_q1 += 1
                    grupos.add((ciudad, li["categoria"]))
            if doc["estado"] == "entregado" and doc["creado_en"] >= FECHA_Q2:
                q2 += 1

    res = {
        "documentos": n,
        "documentos_esperados": args.expected,
        "profundidad_maxima_anidamiento": max_depth,
        "promedio_lineas_por_pedido": round(lineas / n, 3) if n else 0,
        "lineas_totales": lineas,
        "q1_lineas_que_pasan_filtro": lineas_q1,
        "q1_selectividad_filtro_pct": round(100 * lineas_q1 / lineas, 2) if lineas else 0,
        "q1_numero_de_grupos": len(grupos),
        "q2_documentos_candidatos": q2,
        "q2_candidatos_pct": round(100 * q2 / n, 2) if n else 0,
    }

    checks = {
        "conteo_correcto": n == args.expected,
        "tres_niveles_anidamiento": max_depth >= 3,
        "promedio_aprox_3_lineas": 2.5 <= res["promedio_lineas_por_pedido"] <= 3.5,
        "selectividad_q1_entre_30_y_45": 30 <= res["q1_selectividad_filtro_pct"] <= 45,
    }

    if args.check_db:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from benchmark_runner import db
        res["mongodb_count"] = db.mongo_count()
        res["postgresql_count"] = db.pg_count()
        checks["mongodb_count_ok"] = res["mongodb_count"] == n
        checks["postgresql_count_ok"] = res["postgresql_count"] == n

    res["checks"] = checks
    res["todo_ok"] = all(checks.values())
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    sys.exit(0 if res["todo_ok"] else 1)


if __name__ == "__main__":
    main()
