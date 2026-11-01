# ADR-003 — Decisiones operativas del experimento

- **Estado:** aceptada
- **Criterio aplicado a cada duda:** lo que respete más el playbook, sea neutral entre motores, se pueda verificar y tome menos tiempo.
- **Validación:** todo el flujo (generación, carga, runner, finalize, explain, análisis) se probó de punta a punta en un entorno Docker local antes de la corrida oficial.

## Datos

1. **Precios.** Se conserva el umbral `> 50` de Q1. `precio_unitario` sigue una log-normal (mediana 38 MXN, σ = 0.75, acotada a 6–300). Verificado: **36.4 %** de las líneas pasa el filtro.
2. **Fechas.** `creado_en` entre 2025-01-01 y 2026-10-31, horario 08:00–16:00 local, fines de semana con peso ×2 (saturación de fin de semana, entrevista Q8). Con `estado = "entregado"` en ~70 % de los pedidos, Q2 tiene **159 208 candidatos (31.8 %)**.
3. **Semilla fija** `20261031`. El generador escribe un solo `data/pedidos.ndjson` (736 MB) que cargan ambos motores; su SHA-256 queda en `data/pedidos.ndjson.sha256` y en `entregables/benchmark_metadata.json`.

## Configuración de los motores

4. **Mismo presupuesto de caché: 25 % del límite** del contenedor. Todo lo demás con sus valores por defecto, documentados.

   | Perfil | Límite | WiredTiger `cacheSizeGB` | PostgreSQL `shared_buffers` |
   |---|---|---|---|
   | A | 4096m | 1 | 1GB |
   | B | 2048m | 0.5 | 512MB |
   | C | 1024m | 0.25 | 256MB |

   Valores por defecto que se conservan: `work_mem` 4MB en Q1, límite de memoria de `$sort` de MongoDB (100 MB), `allowDiskUse` por defecto en Q1, workers paralelos y JIT de PostgreSQL. `log_temp_files = 0` solo agrega registro en el log (para detectar spill), no cambia el comportamiento.
5. **Versiones fijas:** MongoDB 8.0.34, PostgreSQL 17.11, cAdvisor v0.52.1, Prometheus v3.5.0, Node Exporter v1.9.1, runner en Python 3.12 (pymongo 4.19.0, psycopg 3.3.6). Los digests exactos quedan en `results/versions.txt`.
6. **Fechas e índice.** Fechas como texto ISO-8601 UTC con `Z` en ambos motores. En PostgreSQL se indexa la expresión de texto `(data->>'creado_en')`, que es inmutable, en una base inicializada con `--locale=C`, así que la comparación es binaria como en MongoDB. Índices: MongoDB `{pedido_id: 1}` único y `{creado_en: 1}`; PostgreSQL PK `id UUID` y B-Tree sobre la fecha extraída.

## Cómo mide el runner

7. **Lazo cerrado sin pausas.** N procesos, cada uno con su propia conexión; cada cliente lanza la siguiente consulta en cuanto termina la anterior. `throughput_qps` = consultas completadas en la ventana ÷ 300 s.
8. **Percentiles sobre todas las latencias juntas** de las consultas que empiezan y terminan dentro de la ventana de 300 s (`numpy.percentile`, método lineal).
9. **Sin timeout artificial.** El límite de cada consulta es el tiempo que queda de la ventana (`statement_timeout` / `maxTimeMS`). Un timeout fijo de 60 s convertiría la contención en errores falsos. Una consulta cortada por el fin de la ventana no cuenta como falla. Si fallan más del 5 % de las consultas iniciadas, o si **ninguna** termina dentro de la ventana, la repetición queda `status = error` y la nota lo explica. Con 50 clientes en el perfil C es un resultado esperado y se reporta como saturación.
10. **`timestamp_epoch`** = inicio de la ventana de medición (segundos Unix, UTC).

## Estados y detección

11. **Error de memoria de MongoDB** (código 292, `$sort` excede su límite sin `allowDiskUse`) → falla de consulta → `error` si supera el 5 %. No es `oom` (el contenedor sigue vivo) ni `spill`.
12. **Detección de spill:**
    - PostgreSQL: diferencia de `pg_stat_database.temp_files` en la ventana, más las líneas `temporary file` del log.
    - MongoDB: diferencia de los contadores de spill de `serverStatus`, más `usedDisk: true` en el log.

    **Detección de OOM:** diferencia de `memory.events: oom_kill` del cgroup, `OOMKilled` / código de salida 137 en `docker inspect`, y `terminated by signal 9` en el log. Esto último cubre el caso de PostgreSQL, donde el kernel mata un backend pero el contenedor sobrevive.
13. **Top-K sin spill.** Con `LIMIT 1000` ambos motores ordenan en memoria (en PostgreSQL, `top-N heapsort`). Se reporta tal cual. Además, `run_benchmarks.sh explain` corre una **consulta exploratoria sin LIMIT**, fuera de la matriz y del CSV, cuyos planes quedan en `results/explain/`.

## Orden de ejecución

14. **Arranque en frío real en cada repetición:** el contenedor del motor se **recrea** con el perfil (cgroup nuevo y contadores en cero), se limpia la caché del SO y luego vienen warmup → medición → cooldown. Los datos viven en volúmenes y se cargan una sola vez.
15. **Bloques por repetición:** primero las 54 configuraciones de la repetición 1 en orden aleatorio, luego las de la 2 y luego las de la 3 (semilla `20261031 + r`, orden en `results/plan.csv`). Si la corrida se interrumpe, la matriz queda completa con menos repeticiones en vez de tener huecos. `run_benchmarks.sh matrix` **reanuda** donde se quedó.

## Aislamiento y telemetría

16. **Un solo motor encendido** por corrida. **Núcleos separados** en la VM de Docker: motor `0-3`, runner `4-11`, telemetría `12-15`. El límite del playbook se sigue aplicando con `cpus`; `cpuset` solo evita que el runner y el monitoreo compitan con el motor.
17. **Sin healthchecks dentro de los motores:** un healthcheck corre dentro del cgroup y consumiría CPU y memoria del límite durante la medición. La disponibilidad se comprueba desde el runner.
18. **Swap desactivado:** `mem_swappiness: 0` (playbook) más `memswap_limit = mem_limit`. En cgroups v2 Docker ignora `mem_swappiness`; lo que garantiza que no haya swap es `memory.swap.max = 0`, y queda registrado en `limits` de cada corrida.
19. **cAdvisor en modo cgroup crudo.** Con el almacén de imágenes containerd (por defecto en Docker Desktop reciente), el *factory* `docker` de cAdvisor no identifica los contenedores. Se desactiva y cAdvisor exporta cada contenedor con la etiqueta `id="/docker/<container_id>"`, que es la que consulta el runner. Si Prometheus no tiene datos, el runner usa los mismos contadores leídos directamente del cgroup. La fuente usada en cada corrida queda en `results/raw/<run_id>.json` (`final.fuente_kpis`).
20. **Nombre del KPI de memoria.** `container_memory_rss_bytes` del playbook corresponde a la métrica `container_memory_rss` de cAdvisor (unidad: bytes).

## M3 (huella por 1 000 documentos)

21. **Documentos procesados** = consultas completadas × 500 000, porque cada consulta evalúa lógicamente la colección completa. **CPU** = segundos de CPU del cgroup del motor en la ventana. **Memoria** = `max_rss_mb` ÷ 500. La definición es la misma para ambos motores y se declara en el reporte.

## Limitaciones que se declaran en el reporte

- Docker Desktop corre en la VM de WSL2: límites, throttling y `drop_caches` se aplican en esa VM. Hyper-V no fija los vCPU a núcleos físicos, y el i7-13620H combina núcleos P y E.
- Muestreo de 1 s: picos de RSS más cortos pueden no captarse.
- Equipo portátil: rendimiento sujeto a temperatura; se ejecuta conectado a la corriente, en alto rendimiento y con la suspensión desactivada.

## Anexo — Incidencias durante la corrida oficial (31 oct – 1 nov 2026)

La matriz corrió del **31 de octubre a las 12:53** al **1 de noviembre a las 16:21** (hora de México). Se completaron las 162 ejecuciones, seguidas del explain y el análisis.

**1. Cambio del modo de energía (31 oct, ~18:04).** NitroSense pasó del modo original al modo **Performance** a mitad de la matriz. Las primeras 37 corridas comparables se hicieron con el modo original y el resto con Performance.

- *Verificación:* se comparó la latencia P50 de cada corrida contra la mediana de las otras repeticiones de su configuración. Mediana de esa proporción: **1.003** antes del cambio (n = 37; p10–p90: 0.93–1.12) y **0.998** después (n = 107; p10–p90: 0.90–1.12). No hay diferencia medible.
- *Decisión:* no se repite ninguna corrida. La configuración `mongodb_C_Q2_V2_c10` tiene una repetición atípica (r2 = 122.2 s frente a 73.3 s y 77.2 s), pero r2 se hizo con el mismo modo que r1, así que la variación no se atribuye al cambio de modo. Se conserva tal cual, sin repeticiones silenciosas.

**2. Apagón por batería (1 nov, ~04:10).** El cargador se desconectó y la laptop se apagó durante el cooldown de la corrida 124. Esa corrida (`postgresql_A_Q2_V2_c50_r3`) ya estaba guardada completa a las 04:09:32, así que **ninguna corrida quedó a medias**. Al relanzar `run_benchmarks.sh all` a las 11:45, el script retomó solo en la corrida 125.

- *Verificación:* la proporción P50 de las corridas de la madrugada (22:00–04:10) se mantuvo entre 0.86 y 1.13, sin la tendencia a la baja que habría causado la batería.
- *Decisión:* no se descarta ninguna corrida.

Ambas incidencias se declaran en la sección 1 del reporte.
