# Consultas

Los textos exactos están en `queries/` y la correspondencia `query_id` → configuración en `queries/variants.json`.

## Q1 — Unwind, Filter & Grouping (estresa CPU)

```js
[
  { $unwind: "$lineas" },
  { $match: { "lineas.precio_unitario": { $gt: 50 } } },
  { $group: { _id: { ciudad: "$sucursal.ubicacion.ciudad", categoria: "$lineas.categoria" },
              total_revenue: { $sum: { $multiply: ["$lineas.cantidad", "$lineas.precio_unitario"] } },
              avg_revenue:   { $avg: { $multiply: ["$lineas.cantidad", "$lineas.precio_unitario"] } },
              count: { $sum: 1 } } }
]
```

```sql
SELECT data->'sucursal'->'ubicacion'->>'ciudad' AS ciudad, linea->>'categoria' AS categoria,
       SUM((linea->>'cantidad')::numeric * (linea->>'precio_unitario')::numeric) AS total_revenue,
       AVG((linea->>'cantidad')::numeric * (linea->>'precio_unitario')::numeric) AS avg_revenue,
       COUNT(*) AS count
FROM pedidos, jsonb_array_elements(data->'lineas') AS linea
WHERE (linea->>'precio_unitario')::numeric > 50
GROUP BY 1, 2;
```

## Q2 — Massive Sort & Top-K (estresa memoria)

```js
[
  { $match: { estado: "entregado", creado_en: { $gte: "2026-01-01T00:00:00Z" } } },
  { $sort: { "pago.total_final": -1 } },
  { $limit: 1000 },
  { $project: { pedido_id: 1, "cliente.cliente_id": 1, "pago.total_final": 1 } }
]
```

```sql
SELECT data->>'pedido_id' AS pedido_id, data->'cliente'->>'cliente_id' AS cliente_id,
       (data->'pago'->>'total_final')::numeric AS total_final
FROM pedidos
WHERE data->>'estado' = 'entregado' AND data->>'creado_en' >= '2026-01-01T00:00:00Z'
ORDER BY (data->'pago'->>'total_final')::numeric DESC
LIMIT 1000;
```

| query_id | MongoDB | PostgreSQL |
|---|---|---|
| `Q2_V1` | `allowDiskUse: false` | `SET work_mem = '4MB'` |
| `Q2_V2` | `allowDiskUse: true` | `SET work_mem = '64MB'` |

## Planes observados

Primero se observaron en la prueba local y luego se **confirmaron en la corrida oficial** (`results/explain/`, sección 5 del reporte):

- **Q1 en PostgreSQL** ordena para agrupar (`external merge`, spill a disco con `work_mem` 4MB) porque el planificador sobreestima las filas de `jsonb_array_elements`. MongoDB agrupa en memoria (`COLLSCAN` y `$group`).
- **Q2 en MongoDB** usa el índice `creado_en` (`IXSCAN` + `FETCH`); **PostgreSQL** prefiere `Seq Scan` y ordena con `top-N heapsort`.
- **Q2 sin LIMIT** (exploratoria): PostgreSQL con 4MB hace `external merge`; MongoDB proyecta antes de ordenar y no rebasa su límite de 100 MB.
