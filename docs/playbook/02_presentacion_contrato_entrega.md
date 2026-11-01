# Presentación — contrato de entrega (guía del experimento)

> **Transcripción literal** de `playbook_sesion.pdf` (13 diapositivas). Se conserva el texto original **sin resumir ni modificar**. Solo se reconstruyeron las ligaduras tipográficas que la extracción automática pierde (fi, fl, ff) y se adaptó el formato a Markdown.
> Las diapositivas 5, 9 y 12 tienen en el PDF original un espacio en blanco donde iría una tabla o figura; se indica como *[espacio en blanco en el original]*.
> Los recuadros **«Nota del equipo»** no forman parte del original: señalan brevemente dónde surgieron dudas y qué alternativa se eligió, con la decisión que la documenta.

---

## Diapositiva 1/13

**Medición de métricas en bases documentales**
MongoDB frente a PostgreSQL JSONB bajo contención

Ingeniería en Tecnologías de la Información e Innovación Digital
IT2iD
Universidad Politécnica de Chiapas · IT2iD
2026

## Diapositiva 2/13 — Recorrido de la sesión

**Pregunta guía**
¿Qué hay que medir, cómo se ejecuta y qué evidencia entregar para que un estudio posterior (y un revisor) puedan reproducir y cuestionar el resultado?

Qué medimos → Cómo se corre → Ejemplo de celda → Qué entregar

**Al salir**
Entender la matriz Mongo/Postgres × perfiles × Q1/Q2 × concurrencia, y el CSV/reporte que alimenta un estudio.

## Diapositiva 3/13 — Qué van a hacer (en una frase)

**Actividad**
Comparar MongoDB (documentos) y PostgreSQL JSONB al ejecutar agregaciones JSON anidadas, con límites estrictos de CPU y memoria (Docker cgroups v2).

- Dataset: 500 000 órdenes con ∼3 niveles de anidamiento.
- Dos cargas: Q1 (unwind + group) y Q2 (sort + Top-K).
- Tres perfiles: baseline / media / severa.
- Tres concurrencias: 1, 10, 50.

**No es probar si arranca**
Cada corrida produce métricas numeradas (latencia, QPS, throttling, RSS, spill, OOM) en un CSV homogéneo.

> **Nota del equipo.** Por indicación del profesor, el dataset son 500 000 **pedidos de una tienda de abarrotes** (esquema propio, 3 niveles, ~3 líneas por pedido) en lugar de las órdenes del playbook → ADR-002.

## Diapositiva 4/13 — Preguntas que responden las métricas

- **M1** ¿Cómo cambian P95/P99 al limitar CPU y memoria?
- **M2** ¿Qué motor gestiona mejor buffers antes de spill o OOM?
- **M3** ¿Cuál es la huella de CPU/memoria por cada 1 000 documentos?

| Para el equipo | Para el estudio |
|---|---|
| Guían qué celdas priorizar y qué contraste reportar. | Son las mismas preguntas que un revisor pedirá justificar con datos. |

## Diapositiva 5/13 — Perfiles de recursos (ejemplo operativo)

*[espacio en blanco en el original]*

**Qué anotar siempre**
`profile`, límites Docker reales, versión del motor y si hubo spill/OOM. Sin eso, la celda no sirve para el estudio.

> **Nota del equipo.** Los límites reales del kernel se registran en cada corrida (`results/limits/`, `results/raw/`). Para que la comparación fuera neutral, la caché de cada motor se fijó al 25 % del límite, y el motor, el runner y la telemetría se separaron en núcleos distintos → ADR-003.

## Diapositiva 6/13 — Ejemplo Q1: saturación de CPU

Desanidar items, filtrar price > 50, agrupar por país y categoría.

| MongoDB (idea) | PostgreSQL (idea) |
|---|---|
| `$unwind items` | `jsonb_array_elements` |
| `$match price > 50` | `+ WHERE price > 50` |
| `$group by country, category` | `+ GROUP BY country, category` |

**Métrica a mirar**
Throughput y P95/P99; en severa, tiempo CFS throttled.

> **Nota del equipo.** Una cadena local no opera en varios países, así que «país» se sustituyó por la **ciudad de la sucursal** (72 grupos reales). Se conservaron los mismos operadores y el umbral > 50 → ADR-002.

## Diapositiva 7/13 — Ejemplo Q2: estrés de buffer (Top-K)

Filtrar completadas, ordenar por `final_total`, Top-1000.

- Mongo: `allowDiskUse` false/true.
- Postgres: `work_mem` 4 MB / 64 MB.

**Ejemplo de lectura (ficticio, formato)**
Perfil C, concurrencia 50, `allowDiskUse:false` ⇒ spill o fallo.
Misma celda con disco permitido ⇒ termina, pero baja QPS.

**Para el revisor**
Hay que reportar ambas variantes: sin spill y con spill (o OOM).

> **Nota del equipo.** El CSV no admite columnas nuevas, así que las variantes se identifican en `query_id` como `Q2_V1` (false / 4 MB) y `Q2_V2` (true / 64 MB) → ADR-001. Con `LIMIT 1000` ningún motor volcó a disco; esto se demostró con una consulta exploratoria sin LIMIT → ADR-003, reporte sección 5.

## Diapositiva 8/13 — Una celda de la matriz (qué es una medición)

Motor × Perfil × Query × Concurrencia
× 3 repeticiones

- Matriz: 2 × 3 × 2 × 3 = 36 celdas; cada una × 3 repeticiones.
- Ciclo: flush caché → warmup 60 s → medición 300 s → cooldown 60 s.

**Producto mínimo por celda**
Una fila CSV por repetición + nota de estado (ok/spill/oom/error).

> **Nota del equipo.** Con las dos variantes de Q2 se ejecutaron **54 configuraciones × 3 = 162 corridas**, en orden aleatorio por bloques de repetición y recreando el contenedor en cada corrida → ADR-001 y ADR-003.

## Diapositiva 9/13 — Ejemplo de fila CSV (formato esperado)

*[espacio en blanco en el original]*

Sin columnas inventadas ni renombradas: el estudio posterior concatena todos los CSV.

> **Nota del equipo.** Se respetaron las 14 columnas del playbook 8.2. `max_rss_mb` = máximo de RSS en la ventana ÷ 1 000 000; `cpu_throttled_seconds` = diferencia del contador en la ventana; prioridad de estados `oom` > `error` > `spill` > `ok` → ADR-001.

## Diapositiva 10/13 — Qué van a entregar

| Código / scripts | Evidencia |
|---|---|
| docker-compose parametrizado | CSV con el esquema fijo |
| generador 500k | Capturas o logs de spill/OOM |
| runner (k6 o Python) | Reporte de métricas (7 secciones del playbook) |
| queries/ Mongo + SQL | |
| run_benchmarks.sh | |

**Criterio de utilidad**
Si otro equipo no puede reejecutar o un revisor no puede cuestionar P99/throttling con sus datos, la entrega está incompleta.

## Diapositiva 11/13 — Qué preguntará un revisor (anticípense)

1. ¿El baseline es comparable (mismo dataset, mismas queries)?
2. ¿Las latencias son P50/P95/P99 o solo promedios?
3. ¿Hubo throttling CFS? ¿Cuántos segundos?
4. ¿Spill a disco o OOM? ¿En qué perfil y concurrencia?
5. ¿Cuántas repeticiones y cómo se resume (media / mediana)?
6. ¿El plan de ejecución respalda el cuello de botella?

**Su reporte debe contestarlas con tablas/figuras**
No con opiniones: con filas del CSV y un plan `explain` / `EXPLAIN ANALYZE`.

> **Nota del equipo.** Repeticiones resumidas con la **mediana** y el rango mín–máx → ADR-001.

## Diapositiva 12/13 — Secciones del reporte (checklist)

*[espacio en blanco en el original]*

**Puente**
El PDF `playbook.pdf` es la especificación; estas diapos fijan el contrato de entrega.

## Diapositiva 13/13 — Cierre

- Miden bajo contención, no solo en máquina libre.
- Cada celda → filas CSV + estado + (si aplica) spill/OOM.
- El entregable alimenta un estudio y resiste preguntas de revisor.

**Siguiente paso en laboratorio**
Levantar perfiles A/B/C, correr una celda piloto (1 motor × 1 query × 1 concurrencia) y validar el CSV antes de la matriz completa.

*IT2iD | Universidad Politécnica de Chiapas · IT2iD | 2026*
