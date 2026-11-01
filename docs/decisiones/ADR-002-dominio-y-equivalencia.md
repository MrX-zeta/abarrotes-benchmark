# ADR-002 — Dominio de la tienda de abarrotes y equivalencia con el playbook

- **Estado:** aceptada
- **Contexto:** el profesor pidió que el proyecto fuera **diferente** al del playbook; el estudio posterior concatena los CSV de todos los equipos. Hay que cambiar el esquema de datos sin cambiar lo que se mide.

## Decisión

1. **Dominio:** colección/tabla `pedidos` de una cadena ficticia de abarrotes con 12 sucursales en Chiapas y pedidos en línea que se recogen en tienda (entrevista, Q8–Q9). Es el problema principal que expresó el cliente; los pedidos se leen como documento completo y crecen sin tope.
2. **Forma equivalente, campos propios (opción A).** Se conserva **operador por operador** la lógica de Q1 y Q2 del playbook; solo cambian los nombres de campo. No se usan los nombres del playbook (`customer.geo.country`, `payment.final_total`…) porque eso equivaldría a reutilizar su esquema.
3. **País → ciudad de la sucursal.** Una cadena local opera en varias ciudades, no en varios países; agrupar por país dejaría Q1 con un solo grupo. Con 12 ciudades × 6 categorías se obtienen **72 grupos reales**.
4. **Se conserva el umbral `> 50`** de Q1; lo que se calibra es la distribución de precios (ADR-003, decisión 1).

## Equivalencia de campos

| Playbook | Abarrotes | Papel en la consulta |
|---|---|---|
| colección/tabla `orders` | `pedidos` | — |
| `order_id` (UUID) | `pedido_id` (UUID v4) | Identificador con índice; PK `id UUID` en PostgreSQL |
| `timestamp` (ISO-8601) | `creado_en` (ISO-8601 UTC con `Z`) | Filtro temporal de Q2 con índice |
| `customer{id, tier, segment, geo{…coordinates}}` | `cliente{cliente_id, tipo, segmento}` + `sucursal{sucursal_id, nombre, ubicacion{estado, ciudad, cp, coordenadas{lat, lng}}}` | Nivel 3 de anidamiento: `sucursal.ubicacion.coordenadas` |
| `customer.geo.country` | `sucursal.ubicacion.ciudad` | Primera clave de agrupación de Q1 |
| `items[]{sku, category, brand, qty, price, tax_pct, discounts}` | `lineas[]{codigo_barras, nombre, categoria, subcategoria, marca, cantidad, precio_unitario, oferta{tipo, valor}}` | Arreglo que Q1 desanida (~3 elementos) |
| `items.category` | `lineas.categoria` | Segunda clave de agrupación de Q1 |
| `items.qty * items.price` | `lineas.cantidad * lineas.precio_unitario` | Importe de la línea |
| `items.price > 50` | `lineas.precio_unitario > 50` | Filtro de Q1 |
| `payment{method, status, transaction_id, gateway_latency_ms, totals}` | `pago{forma, metodo, estado, referencia, subtotal, descuento, total_final}` | — |
| `payment.status = "completed"` | `estado = "entregado"` | Filtro de Q2 (estado final del pedido) |
| `payment.final_total` | `pago.total_final` | Campo de orden de Q2, **sin índice** |
| `metadata{channel, user_agent, session_id, flags}` | `metadatos{canal, dispositivo, sesion_id, banderas{…}}` | — |
| — | `historial_estados[]{estado, fecha}` | Segundo arreglo del documento |

## Equivalencia de consultas

| Playbook | Abarrotes |
|---|---|
| Q1: `$unwind items` → `$match price > 50` → `$group {country, category}` con `$sum`, `$avg` de `qty*price` y conteo | Q1: `$unwind lineas` → `$match precio_unitario > 50` → `$group {ciudad, categoria}` con `$sum`, `$avg` de `cantidad*precio_unitario` y conteo |
| Q1 SQL: `jsonb_array_elements(data->'items')`, `WHERE price > 50`, `GROUP BY 1, 2` | Idéntica con `data->'lineas'` |
| Q2: `$match status=completed, timestamp >= 2026-01-01` → `$sort final_total -1` → `$limit 1000` → `$project` | Idéntica con `estado`, `creado_en`, `pago.total_final` |
| Q2 SQL: `WHERE … ORDER BY final_total DESC LIMIT 1000` | Idéntica; la fecha se compara como texto ISO (ADR-003, decisión 6) |
| Variantes `allowDiskUse` false/true · `work_mem` 4MB/64MB | `Q2_V1` / `Q2_V2` (ADR-001) |

Los archivos están en `queries/`.

## Consecuencias

- Cumple "proyecto diferente" y la comparación MongoDB vs PostgreSQL dentro del proyecto es válida: mismos datos, mismas consultas lógicas, mismas condiciones.
- **No** se afirma que los resultados sean comparables con los de equipos que usen otro dominio u otras consultas, aunque sus CSV tengan las mismas columnas.
