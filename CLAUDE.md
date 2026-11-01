# CLAUDE.md — Reglas de trabajo del proyecto

Proyecto: benchmark **MongoDB vs PostgreSQL (JSONB)** bajo límites de CPU y memoria de contenedor.
Materia: Bases de Datos en la Nube. Dominio ficticio: tienda de abarrotes (pedidos en línea con recogida en tienda).

Este archivo manda sobre cualquier suposición. Si algo aquí choca con una petición, **pregunta antes de actuar**.

---

## 1. Fuentes de verdad y prioridad

Cuando dos fuentes se contradigan, gana la de arriba:

1. `docs/playbook/` — especificación del experimento (playbook) y contrato de entrega (presentación).
2. `docs/decisiones/` — ADRs aprobadas por el equipo.
3. `docs/diseno/` — esquema de `pedidos`, consultas y equivalencias.
4. `docs/proyecto/` — entrevista, tabla de operaciones y patrones de acceso (ficticios).
5. Todo lo demás.

`docs/playbook/` es **solo lectura**: nunca se edita, resume ni reinterpreta. Los README de esa carpeta son transcripciones literales y solo se generan cuando el equipo lo pida.

## 2. Restricciones fijas del experimento (no negociables)

- **Matriz base:** 2 motores (MongoDB, PostgreSQL) × 3 perfiles (A, B, C) × 2 consultas (Q1, Q2) × 3 concurrencias (1, 10, 50) = **36 celdas**, cada una con **3 repeticiones**.
- **Perfiles:** A baseline 4.0 CPU / 4096m; B medio 2.0 CPU / 2048m; C severo 1.0 CPU / 1024m. Swap desactivado (`mem_swappiness: 0`) en los tres.
- **Ciclo de cada corrida:** flush de caché (`sync; echo 3 > /proc/sys/vm/drop_caches`, en el **host** con privilegios) → warmup 60 s → medición 300 s → cooldown 60 s.
- **Telemetría:** cAdvisor + Node Exporter + Prometheus con `scrape_interval: 1s`.
- **Un solo motor encendido por corrida.** Nunca ambos a la vez; contaminan la medición. El contenedor del motor se recrea en cada corrida (arranque en frío, contadores en cero).
- **Sin healthchecks dentro de los motores** (consumirían el límite); núcleos separados para motor, runner y telemetría (`.env`).
- **Orden:** por bloques de repetición, aleatorio con semilla dentro de cada bloque (`results/plan.csv`); `run_benchmarks.sh matrix` reanuda.
- **Variantes de Q2** (se reportan siempre ambas): V1 = `allowDiskUse: false` / `work_mem = 4MB`; V2 = `allowDiskUse: true` / `work_mem = 64MB`. Fijar `allowDiskUse` explícitamente (su valor por defecto cambia entre versiones).
- **Nombres de archivo del playbook 8.1** (no se cambian): `docker-compose.yml`, `synthetic_data_generator.py`, `benchmark_runner/`, `queries/`, `run_benchmarks.sh`.
- **Reporte:** exactamente las 7 secciones del playbook 8.3, respondidas con datos del CSV y planes `explain` / `EXPLAIN (ANALYZE, BUFFERS)`, no con opiniones.

## 3. Esquema del CSV (playbook 8.2) — intocable

Exactamente estas **14 columnas, con estos nombres y en este orden**:

```
timestamp_epoch,engine,profile,query_id,concurrency,run_number,throughput_qps,latency_p50_ms,latency_p95_ms,latency_p99_ms,cpu_throttled_seconds,max_rss_mb,disk_spill,status
```

- **Prohibido** agregar, quitar, renombrar o reordenar columnas. Los CSV de todos los equipos se concatenan.
- Una fila por repetición.
- `status` ∈ {`ok`, `spill`, `oom`, `error`}. Prioridad si coinciden varios: `oom` > `error` > `spill` > `ok`.
- `query_id` ∈ {`Q1`, `Q2_V1`, `Q2_V2`} (ver `docs/decisiones/ADR-001-criterios-de-interpretacion.md`).
- El archivo consolidado vive en `entregables/mediciones.csv`; los CSV por celda, en `results/csv/`.

## 4. Restricciones del dominio

- Por indicación del profesor, el esquema de datos **no es el del playbook**: es la colección `pedidos` de la tienda de abarrotes.
- Debe conservar las **propiedades estructurales** que hacen que Q1 y Q2 estresen lo que deben: 500 000 documentos; 3 niveles de anidamiento; ~3 elementos por arreglo; identificador tipo UUID; fecha ISO-8601; índice sobre identificador y fecha en ambos motores.
- Q1 conserva la forma **desanidar → filtrar → agrupar** (estresa CPU). Q2 conserva la forma **filtrar → ordenar → Top-1000 sin índice en el campo de orden** (estresa memoria).
- PostgreSQL: `pedidos(id UUID PRIMARY KEY, data JSONB)` + B-Tree sobre `(data->>'creado_en')` (texto ISO-8601 UTC, base con `--locale=C`).
- Equivalencia campo por campo y consulta por consulta: `docs/decisiones/ADR-002-dominio-y-equivalencia.md`. Decisiones operativas (datos, caché 25 %, runner, estados, orden, aislamiento, cAdvisor): `docs/decisiones/ADR-003-decisiones-operativas.md`.
- Toda decisión de diseño nueva que afecte resultados se registra como **ADR antes de implementarse**. Ante cualquier duda: lo que más respete el playbook, sea neutral entre motores y tome menos tiempo.

## 5. Honestidad de los datos

- **Ningún número del reporte se inventa ni se estima.** Todo sale de filas del CSV o de un plan de ejecución.
- Los ejemplos ilustrativos se marcan como **(ficticio)**.
- Si una corrida falla, se registra con `status = error`. **No se repite en silencio.** Si ninguna consulta termina dentro de la ventana (saturación), también es `error` con su nota.
- La fuente de los KPIs de cada corrida (Prometheus o cgroup) queda en `results/raw/<run_id>.json`.
- Las limitaciones (muestreo de 1 s, VM de Docker Desktop, etc.) se declaran en el reporte, no se ocultan.

## 6. Forma de trabajo

- **Primero la celda piloto** (1 motor × 1 consulta × 1 concurrencia × 1 repetición); validar el CSV; solo entonces lanzar la matriz completa.
- Antes de cambiar el alcance, el esquema del CSV o cualquier restricción de este archivo: **preguntar**.
- Idioma: documentación en español; código e identificadores técnicos tal como los define el playbook.
- Versiones de imágenes Docker **fijas** (nada de `latest`) y registradas en `results/versions.txt`.
- Sin secretos en el repositorio: solo `.env.example`.
- Los scripts van con saltos de línea **LF** (ver `.gitattributes`); el equipo trabaja en Windows y Docker corre en Linux.
- Al cerrar cada tarea se actualiza `entregables/CHECKLIST.md`.
- Los originales del proyecto ficticio (`docs/proyecto/`) no se editan; las correcciones van en `correcciones.md`.

## 7. Evidencia que debe generar cada corrida

- Límites Docker realmente aplicados (`docker inspect` + valores de `/sys/fs/cgroup`) → `results/limits/`.
- Versiones exactas de motores y herramientas → `results/versions.txt`.
- Especificaciones del host y de Docker → `results/host/host_info.txt` (con aviso si Docker corre dentro de una VM/WSL2).
- Logs de los motores para detectar spill/OOM → `results/logs/`.
- Planes de ejecución → `results/explain/`.
- Verificación de que el perfil A no tiene contención (throttling ≈ 0, sin spill) → `entregables/evidencias/baseline/`.
