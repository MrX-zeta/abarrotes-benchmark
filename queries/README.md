# queries/

Consultas del benchmark sobre la colección/tabla `pedidos`. Replican operador por operador las del playbook (sección 5); solo cambian los nombres de campo (equivalencias en `docs/diseno/equivalencia_playbook.md`).

| query_id | MongoDB | PostgreSQL | Configuración |
|---|---|---|---|
| `Q1` | `mongodb/q1_unwind_group.json` | `postgresql/q1_unwind_group.sql` | Valores por defecto (`work_mem` 4MB, `allowDiskUse` sin fijar) |
| `Q2_V1` | `mongodb/q2_sort_topk.json` | `postgresql/q2_sort_topk.sql` | `allowDiskUse: false` / `SET work_mem = '4MB'` |
| `Q2_V2` | `mongodb/q2_sort_topk.json` | `postgresql/q2_sort_topk.sql` | `allowDiskUse: true` / `SET work_mem = '64MB'` |

`variants.json` es la fuente que lee el runner.
