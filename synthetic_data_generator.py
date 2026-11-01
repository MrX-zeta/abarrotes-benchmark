#!/usr/bin/env python3
"""
synthetic_data_generator.py — Dataset sintético de pedidos de la tienda de abarrotes.

Genera N pedidos (por defecto 500 000) en formato NDJSON (un documento JSON por línea).
El MISMO archivo se carga en MongoDB y en PostgreSQL, por lo que ambos motores
reciben exactamente los mismos datos. Determinista: misma semilla => mismo archivo.

Propiedades exigidas por el playbook (ver docs/decisiones/ADR-002):
  * 500 000 registros, JSON, 3 niveles de anidamiento, ~3 elementos por arreglo.
  * Identificador UUID (pedido_id) y fecha ISO-8601 (creado_en, UTC con 'Z').

Calibración documentada en ADR-003:
  * precio_unitario ~ log-normal (mediana 38 MXN, sigma 0.75) => ~36 % de líneas > 50.
  * creado_en entre 2025-01-01 y 2026-10-31, fines de semana con peso x2 => ~45 % >= 2026-01-01.
  * estado = "entregado" en ~70 % de los pedidos.

Uso:
  python synthetic_data_generator.py --out data/pedidos.ndjson [--n 500000] [--seed 20261031]
"""
import argparse
import hashlib
import json
import math
import random
import sys
import uuid
from datetime import date, datetime, timedelta, timezone

DEFAULT_N = 500_000
DEFAULT_SEED = 20261031

# --- Catálogos del dominio (entrevista: Q2, Q5, Q22) -------------------------------------------

CATEGORIAS = {
    "Alimentos": ["Enlatados", "Instantáneos", "Embutidos", "Abarrotes secos", "Lácteos"],
    "Bebidas": ["Refrescos", "Agua", "Jugos", "Energéticas"],
    "Limpieza": ["Lavandería", "Cocina", "Pisos", "Desinfectantes"],
    "Aseo personal": ["Higiene bucal", "Cuidado del cabello", "Jabones", "Papel higiénico"],
    "Golosinas": ["Chocolates", "Dulces", "Galletas"],
    "Frituras": ["Papas", "Totopos", "Cacahuates", "Chicharrones"],
}

# Sucursales ficticias en 12 ciudades de Chiapas (coordenadas y CP aproximados).
SUCURSALES = [
    ("SUC-01", "Sucursal Tuxtla Centro", "Tuxtla Gutiérrez", "29000", 16.7528, -93.1152, 3.0),
    ("SUC-02", "Sucursal Tapachula", "Tapachula", "30700", 14.9031, -92.2575, 2.0),
    ("SUC-03", "Sucursal San Cristóbal", "San Cristóbal de las Casas", "29200", 16.7370, -92.6376, 1.6),
    ("SUC-04", "Sucursal Comitán", "Comitán de Domínguez", "30000", 16.2510, -92.1342, 1.2),
    ("SUC-05", "Sucursal Palenque", "Palenque", "29960", 17.5097, -91.9822, 0.9),
    ("SUC-06", "Sucursal Chiapa de Corzo", "Chiapa de Corzo", "29160", 16.7071, -93.0122, 0.9),
    ("SUC-07", "Sucursal Villaflores", "Villaflores", "30470", 16.2333, -93.2667, 0.8),
    ("SUC-08", "Sucursal Ocosingo", "Ocosingo", "29950", 16.9070, -92.0947, 0.7),
    ("SUC-09", "Sucursal Tonalá", "Tonalá", "30500", 16.0889, -93.7556, 0.7),
    ("SUC-10", "Sucursal Cintalapa", "Cintalapa", "30400", 16.6968, -93.7208, 0.6),
    ("SUC-11", "Sucursal Huixtla", "Huixtla", "30640", 15.1389, -92.4636, 0.6),
    ("SUC-12", "Sucursal Pichucalco", "Pichucalco", "29520", 17.5103, -93.1172, 0.5),
]

ESTADOS = ["entregado", "cancelado", "listo_para_recoger", "en_preparacion", "recibido"]
ESTADOS_PESOS = [0.70, 0.10, 0.08, 0.06, 0.06]
FLUJO = ["recibido", "en_preparacion", "listo_para_recoger", "entregado"]

FORMAS_PAGO = ["en_tienda", "en_linea"]
METODOS = {"en_tienda": ["efectivo", "tarjeta"], "en_linea": ["tarjeta", "transferencia"]}
TIPOS_CLIENTE = ["frecuente", "ocasional", "nuevo"]
SEGMENTOS = ["hogar", "negocio", "mayoreo"]
CANALES = ["web", "app", "whatsapp"]
DISPOSITIVOS = ["movil", "escritorio", "tableta"]

FECHA_INICIO = date(2025, 1, 1)
FECHA_FIN = date(2026, 10, 31)

N_PRODUCTOS = 600
N_CLIENTES = 60_000


def build_catalog(rng: random.Random):
    """Catálogo fijo de productos; el precio base sigue una log-normal (mediana 38 MXN)."""
    productos = []
    cats = list(CATEGORIAS)
    for i in range(N_PRODUCTOS):
        cat = cats[i % len(cats)]
        sub = rng.choice(CATEGORIAS[cat])
        precio = math.exp(rng.gauss(math.log(38.0), 0.75))
        precio = round(min(max(precio, 6.0), 300.0), 2)
        productos.append({
            "codigo_barras": f"750{rng.randrange(10**9, 10**10)}",
            "nombre": f"{sub} {i:04d}",
            "categoria": cat,
            "subcategoria": sub,
            "marca": f"Marca {rng.randrange(1, 41):02d}",
            "precio": precio,
        })
    return productos


def build_days():
    """Días del rango con peso 2 en sábado y domingo (saturación de fin de semana, Q8)."""
    days, weights = [], []
    d = FECHA_INICIO
    while d <= FECHA_FIN:
        days.append(d)
        weights.append(2.0 if d.weekday() >= 5 else 1.0)
        d += timedelta(days=1)
    return days, weights


def iso_z(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def make_uuid(rng: random.Random) -> str:
    return str(uuid.UUID(int=rng.getrandbits(128), version=4))


def gen_pedido(rng, productos, days, day_cum, suc_cum):
    day = rng.choices(days, cum_weights=day_cum, k=1)[0]
    # Horario 08:00–16:00 local (UTC-6) => 14:00–22:00 UTC.
    secs = rng.randrange(14 * 3600, 22 * 3600)
    creado = datetime(day.year, day.month, day.day, tzinfo=timezone.utc) + timedelta(seconds=secs)

    s = rng.choices(SUCURSALES, cum_weights=suc_cum, k=1)[0]
    sucursal = {
        "sucursal_id": s[0],
        "nombre": s[1],
        "ubicacion": {
            "estado": "Chiapas",
            "ciudad": s[2],
            "cp": s[3],
            "coordenadas": {"lat": s[4], "lng": s[5]},  # nivel 3
        },
    }

    # Número de líneas: 1 + Poisson(2) acotado a 8 => promedio ~3.
    k = 1
    lam, p, L = 2.0, 1.0, math.exp(-2.0)
    while True:
        p *= rng.random()
        if p <= L:
            break
        k += 1
    n_lineas = min(k, 8)

    lineas = []
    subtotal = 0.0
    descuento = 0.0
    for prod in rng.sample(productos, n_lineas):
        cantidad = rng.choices([1, 2, 3, 4, 5, 6], weights=[40, 25, 15, 9, 6, 5], k=1)[0]
        precio = prod["precio"]
        oferta = None
        if rng.random() < 0.15:
            if rng.random() < 0.6:
                oferta = {"tipo": "porcentaje", "valor": rng.choice([5, 10, 15, 20])}
                descuento += cantidad * precio * oferta["valor"] / 100
            else:
                oferta = {"tipo": "precio_fijo", "valor": round(precio * 0.9, 2)}
                descuento += cantidad * (precio - oferta["valor"])
        subtotal += cantidad * precio
        lineas.append({
            "codigo_barras": prod["codigo_barras"],
            "nombre": prod["nombre"],
            "categoria": prod["categoria"],
            "subcategoria": prod["subcategoria"],
            "marca": prod["marca"],
            "cantidad": cantidad,
            "precio_unitario": precio,
            "oferta": oferta,
        })

    estado = rng.choices(ESTADOS, weights=ESTADOS_PESOS, k=1)[0]
    if estado == "cancelado":
        pasos = FLUJO[: rng.randrange(1, 3)] + ["cancelado"]
    else:
        pasos = FLUJO[: FLUJO.index(estado) + 1]
    historial, t = [], creado
    for e in pasos:
        historial.append({"estado": e, "fecha": iso_z(t)})
        t += timedelta(minutes=rng.randrange(5, 90))

    forma = rng.choice(FORMAS_PAGO)
    if estado == "entregado":
        estado_pago = "pagado"
    elif estado == "cancelado":
        estado_pago = "reembolsado" if forma == "en_linea" else "cancelado"
    else:
        estado_pago = "pagado" if forma == "en_linea" else "pendiente"

    subtotal = round(subtotal, 2)
    descuento = round(descuento, 2)
    pago = {
        "forma": forma,
        "metodo": rng.choice(METODOS[forma]),
        "estado": estado_pago,
        "referencia": make_uuid(rng)[:18] if forma == "en_linea" else None,
        "subtotal": subtotal,
        "descuento": descuento,
        "total_final": round(subtotal - descuento, 2),
    }

    cliente_n = rng.randrange(1, N_CLIENTES + 1)
    return {
        "pedido_id": make_uuid(rng),
        "creado_en": iso_z(creado),
        "cliente": {
            "cliente_id": f"CLI-{cliente_n:06d}",
            "tipo": rng.choices(TIPOS_CLIENTE, weights=[45, 40, 15], k=1)[0],
            "segmento": rng.choices(SEGMENTOS, weights=[80, 15, 5], k=1)[0],
        },
        "sucursal": sucursal,
        "lineas": lineas,
        "pago": pago,
        "estado": estado,
        "historial_estados": historial,
        "metadatos": {
            "canal": rng.choices(CANALES, weights=[50, 35, 15], k=1)[0],
            "dispositivo": rng.choices(DISPOSITIVOS, weights=[70, 25, 5], k=1)[0],
            "sesion_id": make_uuid(rng),
            "banderas": {"primera_compra": rng.random() < 0.08, "recoger_express": rng.random() < 0.2},
        },
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="data/pedidos.ndjson")
    ap.add_argument("--n", type=int, default=DEFAULT_N)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    productos = build_catalog(rng)
    days, day_w = build_days()
    day_cum, acc = [], 0.0
    for w in day_w:
        acc += w
        day_cum.append(acc)
    suc_cum, acc = [], 0.0
    for s in SUCURSALES:
        acc += s[6]
        suc_cum.append(acc)

    h = hashlib.sha256()
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        for i in range(args.n):
            line = json.dumps(gen_pedido(rng, productos, days, day_cum, suc_cum),
                              ensure_ascii=False, separators=(",", ":")) + "\n"
            f.write(line)
            h.update(line.encode("utf-8"))
            if (i + 1) % 100_000 == 0:
                print(f"  {i + 1:,} pedidos generados", file=sys.stderr)

    digest = h.hexdigest()
    with open(args.out + ".sha256", "w", encoding="utf-8", newline="\n") as f:
        f.write(f"{digest}  {args.out}\n")
    print(json.dumps({"out": args.out, "n": args.n, "seed": args.seed, "sha256": digest}))


if __name__ == "__main__":
    main()
