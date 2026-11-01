# Equivalencia con el playbook

La tabla campo por campo y consulta por consulta es la decisión aprobada en
[`../decisiones/ADR-002-dominio-y-equivalencia.md`](../decisiones/ADR-002-dominio-y-equivalencia.md).

Resumen de las propiedades estructurales que se conservan:

| Propiedad del playbook | Cómo se cumple |
|---|---|
| 500 000 registros JSON | `synthetic_data_generator.py` (verificado) |
| 3 niveles de anidamiento | `sucursal.ubicacion.coordenadas` |
| Promedio de 3 ítems por registro | `lineas[]`, promedio 2.997 |
| Identificador UUID con índice | `pedido_id` / PK `id UUID` |
| Fecha ISO-8601 con índice | `creado_en` / B-Tree sobre `data->>'creado_en'` |
| Q1: unwind → filtro > 50 → group (2 claves) con sum, avg, count | Idéntica, sobre `lineas`, ciudad y categoría |
| Q2: filtro estado + fecha → sort desc sin índice → Top-1000 → project | Idéntica, sobre `estado`, `creado_en`, `pago.total_final` |
| Variantes de memoria de Q2 | `Q2_V1` (false / 4MB) y `Q2_V2` (true / 64MB) |
