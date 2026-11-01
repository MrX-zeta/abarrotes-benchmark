# CHECKLIST de entregables

Cada requisito del playbook → archivo que lo cumple → estado.
Estados: ⬜ pendiente · ✅ cumplido y verificado. Matriz oficial completada el 1 nov 2026 (162/162). Se actualiza al cerrar cada tarea.

## A. Repositorio de código (playbook 8.1)

| Requisito | Archivo / carpeta | Estado |
|---|---|---|
| docker-compose con perfiles de recursos parametrizados | `docker-compose.yml`, `profiles/` | ✅ probado |
| Generador del dataset de 500 000 documentos | `synthetic_data_generator.py` | ✅ verificado (500 000 docs, 3 niveles, 3.0 líneas) |
| Runner (Python multiproceso) | `benchmark_runner/` | ✅ probado |
| Agregaciones MongoDB y SQL PostgreSQL | `queries/` | ✅ probadas en ambos motores |
| Automatización de la matriz de mediciones | `run_benchmarks.sh` | ✅ probado (reanudable) |

## B. CSV de mediciones (playbook 8.2)

| Requisito | Archivo | Estado |
|---|---|---|
| Esquema exacto de 14 columnas | `benchmark_runner/csv_writer.py` (valida columnas y estados) | ✅ |
| 162 filas (54 configuraciones × 3 repeticiones) | `entregables/mediciones.csv` | ✅ 162/162 |
| `status` ∈ ok / spill / oom / error | `benchmark_runner/finalize.py` | ✅ probado |
| Celda piloto validada antes de la matriz | `results/pilot/` | ✅ |

## C. Reporte de métricas (playbook 8.3) — `entregables/reporte/reporte_metricas.md`

| # | Sección | Evidencia (se genera sola) | Estado |
|---|---|---|---|
| 1 | Host y entorno Docker | `results/host/host_info.txt`, `results/versions.txt` | ✅ |
| 2 | Método y verificación del baseline | ADR-001/003, `entregables/evidencias/baseline/verificacion_baseline.md`, `results/limits/` | ✅ |
| 3 | Resultados consolidados | `entregables/reporte/tablas_resumen.md` | ✅ |
| 4 | Análisis gráfico | `entregables/reporte/figuras/` (P99 vs concurrencia, throttling vs QPS, curva RSS) | ✅ |
| 5 | Planes de ejecución | `results/explain/` | ✅ |
| 6 | Interpretación: memoria, spill, throttling | `entregables/evidencias/spill_oom/eventos.md` + secciones 3–5 | ✅ |
| 7 | Recomendaciones técnicas | Secciones 3–6 | ✅ |
| — | M3: huella por 1 000 documentos | `entregables/reporte/m3_huella.md` | ✅ |

## D. Evidencias complementarias

| Requisito | Archivo / carpeta | Estado |
|---|---|---|
| Límites Docker realmente aplicados por corrida | `results/limits/*.pre.json`, `.post.json` + `limits` en `results/raw/` | ✅ |
| Versiones exactas | `results/versions.txt` | ✅ |
| Logs de motores (spill / OOM) | `results/logs/` | ✅ |
| Series de RSS y throttling por corrida | `results/raw/<run_id>.json` (Prometheus + cgroup) | ✅ |
| Ficha técnica del experimento | `entregables/benchmark_metadata.json` | ✅ |
| Verificación del dataset | `results/dataset_verification.json` | ✅ |

## E. Documentación del proyecto

| Requisito | Archivo | Estado |
|---|---|---|
| Reglas de trabajo | `CLAUDE.md` | ✅ |
| README y guía de ejecución | `README.md`, `docs/GUIA_EJECUCION.md` | ✅ |
| ADR-001 criterios de interpretación | `docs/decisiones/ADR-001-criterios-de-interpretacion.md` | ✅ |
| ADR-002 dominio y equivalencia | `docs/decisiones/ADR-002-dominio-y-equivalencia.md` | ✅ |
| ADR-003 decisiones operativas | `docs/decisiones/ADR-003-decisiones-operativas.md` | ✅ |
| Esquema, equivalencia y consultas | `docs/diseno/` | ✅ |
| Transcripción literal del playbook | `docs/playbook/` | ✅ |
| Entrevista complementada | `docs/proyecto/entrevista_complementada.md` | ✅ |
| Correcciones de contradicciones | `docs/proyecto/correcciones.md` | ✅ |
| Grafo de conocimiento | `docs/conocimiento/` | ✅ |

## F. Preguntas del revisor

- ✅ ¿Cuántas repeticiones y cómo se resumen? → 3; mediana con rango mín–máx (ADR-001)
- ✅ ¿Qué cuello de botella muestra el plan en Q1 y en Q2? → `results/explain/`
- ✅ ¿Hubo spill u OOM? ¿Dónde y con qué evidencia? → `eventos.md`
- ✅ ¿El baseline está libre de contención? → `verificacion_baseline.md`
