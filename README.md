# abarrotes-benchmark

Benchmark de **MongoDB** contra **PostgreSQL (JSONB)** almacenando los mismos pedidos en formato JSON, con **CPU y memoria limitadas a propósito** (contenedores con cgroups v2) para ver cuál se comporta mejor cuando le falta capacidad.

Práctica de *Bases de Datos en la Nube*. El dominio es ficticio: una tienda de abarrotes con varias sucursales y pedidos en línea que el cliente recoge en tienda (producto de una dinámica de entrevista en clase).

## Qué se mide

| Métrica | Pregunta |
|---|---|
| **M1** Latencia P95 / P99 | ¿Cuánto empeoran las consultas más lentas al recortar CPU y memoria? |
| **M2** Buffers, spill y OOM | ¿Cada motor volca a disco temporal (*spill*) o falla por memoria (*OOM*) al ordenar o agrupar? |
| **M3** Huella por 1 000 documentos | ¿Cuánta CPU y memoria gasta cada motor por cada 1 000 documentos procesados? |

## Diseño del experimento

- **Datos:** 500 000 pedidos sintéticos, 3 niveles de anidamiento, ~3 líneas por pedido.
- **Consultas:** Q1 (desanidar líneas → filtrar → agrupar; estresa CPU) y Q2 (filtrar → ordenar → Top-1000 sin índice de orden; estresa memoria, en dos variantes `Q2_V1` / `Q2_V2`).
- **Perfiles:** A 4 CPU / 4 GB · B 2 CPU / 2 GB · C 1 CPU / 1 GB, sin swap.
- **Concurrencia:** 1, 10 y 50 clientes.
- **Matriz:** 36 celdas base × 3 repeticiones; con variantes de Q2, 54 configuraciones y **162 ejecuciones**.
- **Ciclo por corrida:** flush de caché → warmup 60 s → medición 300 s → cooldown 60 s.
- **Telemetría:** cAdvisor, Node Exporter y Prometheus a 1 s.

Criterios de interpretación: [`docs/decisiones/ADR-001-criterios-de-interpretacion.md`](docs/decisiones/ADR-001-criterios-de-interpretacion.md).

## Requisitos del entorno

- Linux con **cgroups v2** (`stat -fc %T /sys/fs/cgroup/` debe responder `cgroup2fs`). En Windows/macOS, Docker Desktop corre en una VM (WSL2): los límites y el throttling se miden ahí, y debe anotarse en el reporte.
- Docker Engine + Compose v2, con imágenes de **versión fija**.
- Python 3.11+ (`pymongo`, `psycopg`, `numpy`, `pandas`, `matplotlib`, `requests`).
- Permisos de root en el host para `drop_caches`.
- ~10 GB libres de disco.

## Estructura

```
abarrotes-benchmark/
├── CLAUDE.md                    Reglas y restricciones de trabajo
├── docker-compose.yml           perfiles parametrizados
├── synthetic_data_generator.py  dataset de 500 000 pedidos
├── run_benchmarks.sh            automatiza la matriz
├── benchmark_runner/            runner Python multiproceso
├── queries/{mongodb,postgresql}/  consultas Q1 y Q2
├── profiles/                    perfiles A, B y C
├── config/                      mongod.conf, postgresql.conf, prometheus.yml
├── scripts/                     carga, verificación, explain, spill/OOM, host
├── docs/
│   ├── playbook/                transcripción literal (solo lectura)
│   ├── proyecto/                entrevista, operaciones y patrones de acceso
│   ├── diseno/                  esquema, equivalencia con el playbook, consultas
│   ├── decisiones/              ADRs
│   └── conocimiento/            grafo de conocimiento
├── data/                        dataset generado (ignorado por git)
├── results/                     salidas crudas de las corridas
└── entregables/                 CSV consolidado, evidencias y reporte
```

## Cómo se ejecuta

Paso a paso para Windows + WSL2: [`docs/GUIA_EJECUCION.md`](docs/GUIA_EJECUCION.md).

```bash
bash run_benchmarks.sh check     # Docker, cgroups v2, CPUs, memoria
bash run_benchmarks.sh setup     # imágenes, telemetría, dataset, carga, plan  (~25 min)
bash run_benchmarks.sh smoke     # prueba rápida de ambos motores               (~8 min)
bash run_benchmarks.sh pilot     # celda piloto con tiempos oficiales          (~8 min)
bash run_benchmarks.sh all       # 162 corridas + explain + análisis           (~20 h, reanudable)
bash run_benchmarks.sh status    # avance
```

El avance contra los requisitos se lleva en [`entregables/CHECKLIST.md`](entregables/CHECKLIST.md).

## Estado

**Experimento terminado.** La matriz oficial se ejecutó del 31 de octubre de 2026 (12:53) al 1 de noviembre de 2026 (16:21) en una laptop Intel i7-13620H con Docker Desktop + WSL2 (cgroups v2): **162 de 162 ejecuciones**, más los planes de ejecución y el análisis.

| Entregable | Archivo |
|---|---|
| CSV de mediciones (esquema 8.2) | [`entregables/mediciones.csv`](entregables/mediciones.csv) |
| Reporte de métricas (7 secciones) | [`entregables/reporte/reporte_metricas.pdf`](entregables/reporte/reporte_metricas.pdf) · [Markdown](entregables/reporte/reporte_metricas.md) |
| Evidencias de baseline, spill/OOM y planes | [`entregables/evidencias/`](entregables/evidencias/) |
| Ficha técnica del experimento | [`entregables/benchmark_metadata.json`](entregables/benchmark_metadata.json) |

Las incidencias durante la corrida (cambio del modo de energía y un apagón entre dos corridas) y su verificación están en el anexo de la [ADR-003](docs/decisiones/ADR-003-decisiones-operativas.md).
