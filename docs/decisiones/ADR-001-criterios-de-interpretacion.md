# ADR-001 — Criterios de interpretación de las especificaciones del benchmark

- **Estado:** aceptada (los ajustes marcados con ◆ fueron aprobados por el equipo)
- **Contexto:** el playbook deja cuatro puntos sin precisar y el esquema del CSV no admite columnas nuevas. Se fijan criterios neutros, aplicados por igual a ambos motores, para respetar el playbook al máximo.

## Criterios

Para mantener la compatibilidad con el playbook, se conservarán las consultas originales (◆ *en su forma*: Q1 desanida, filtra y agrupa; Q2 filtra, ordena y obtiene el Top-1000 — porque el esquema de datos es distinto al del playbook), los perfiles de recursos, los niveles de concurrencia, las ventanas de ejecución, las repeticiones y el esquema de columnas CSV.

### 1. Variantes de Q2

Se identificarán mediante los valores `Q2_V1` y `Q2_V2` en la columna `query_id`.

- **V1:** `allowDiskUse: false` en MongoDB y `work_mem = 4MB` en PostgreSQL.
- **V2:** `allowDiskUse: true` en MongoDB y `work_mem = 64MB` en PostgreSQL.

◆ Q1 conserva el valor `Q1` y no tiene variantes.

Se conservarán las 36 celdas de la matriz base, pero el desglose de las variantes producirá **54 configuraciones experimentales** y **162 ejecuciones** considerando las tres repeticiones.

| Consulta | Variantes | Motores | Perfiles | Concurrencias | Configuraciones |
|---|---|---|---|---|---|
| Q1 | 1 | 2 | 3 | 3 | 18 |
| Q2 | 2 | 2 | 3 | 3 | 36 |
| **Total** | | | | | **54** → ×3 repeticiones = **162 ejecuciones** |

### 2. Memoria RSS

El campo `max_rss_mb` almacenará el máximo valor de `container_memory_rss_bytes` observado durante los 300 segundos de medición, convertido mediante la división entre 1 000 000 (MB decimales).

◆ **Limitación a declarar en el reporte:** el muestreo es de 1 s, por lo que picos más breves pueden no captarse. Como dato de apoyo (fuera del CSV) puede registrarse `memory.peak` del cgroup.

### 3. CPU throttling

El campo `cpu_throttled_seconds` almacenará la diferencia entre las lecturas inicial y final del contador `container_cpu_cfs_throttled_seconds_total`, limitadas a la ventana de medición. Los reinicios del contador deberán detectarse para evitar resultados incorrectos.

◆ **Tratamiento de un reinicio detectado:** se verifica con `docker inspect` (`OOMKilled`, código de salida 137). Si se confirma, la repetición se registra con `status = oom`; si no se explica, con `status = error`. Nunca se publica la diferencia negativa o truncada como valor válido.

### 4. Resumen de repeticiones

El CSV conservará una fila independiente por repetición. Para el reporte consolidado se utilizará la **mediana** de las tres observaciones de cada métrica numérica, acompañada del rango mínimo-máximo. Las métricas booleanas y los estados se presentarán mediante frecuencias de ocurrencia.

◆ **Prioridad de `status`** cuando en una misma repetición ocurren varios eventos: `oom` > `error` > `spill` > `ok`.

## Consecuencias

- Estas convenciones se aplican de forma uniforme a ambos motores y se mantienen documentadas para garantizar la reproducibilidad.
- Los valores `Q2_V1` / `Q2_V2` pueden no coincidir con los CSV de otros equipos si estos usan `Q2` a secas. La correspondencia queda documentada en `entregables/benchmark_metadata.json` y se informa al profesor en la entrega.
- Se ejecutan ambas variantes en todos los perfiles y concurrencias: 54 ejecuciones adicionales respecto a las 108 de la matriz base (~6 h 18 min de medición).
