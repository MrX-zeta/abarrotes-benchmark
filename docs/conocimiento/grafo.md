# Grafo de conocimiento del proyecto

Relaciona las preguntas del playbook (M1–M3) con las decisiones, los componentes, los archivos y las evidencias que las responden. La versión para procesar con código está en `grafo.json` (nodos con tipo y archivo; aristas con relación).

```mermaid
graph LR
  subgraph Preguntas
    M1["Latencia P95/P99 bajo límites de CPU y memoria"]
    M2["Buffers de orden/agrupación: spill u OOM"]
    M3["Huella de CPU y memoria por 1 000 documentos"]
  end
  subgraph Decisiones
    ENT["Entrevista (original + complementada)"]
    ADR1["Criterios de interpretación"]
    ADR2["Dominio y equivalencia"]
    ADR3["Decisiones operativas"]
  end
  subgraph Datos
    ESQ["Colección pedidos"]
    GEN["Generador de 500 000 pedidos"]
    VER["Verificación del dataset"]
  end
  subgraph Experimento
    MDB["MongoDB 8.0.34 (WiredTiger)"]
    PG["PostgreSQL 17.11 (JSONB)"]
    PRF["Perfiles A/B/C"]
    DC["docker-compose.yml"]
    Q1["Q1 unwind-filtro-agrupación (CPU)"]
    Q2V1["Q2_V1 Top-1000 (allowDiskUse false / 4MB)"]
    Q2V2["Q2_V2 Top-1000 (allowDiskUse true / 64MB)"]
    RUN["Runner multiproceso"]
    ORQ["Orquestación de la matriz (162 corridas)"]
  end
  subgraph Medición
    TEL["cAdvisor + Node Exporter + Prometheus (1 s)"]
    CG["Lectura directa del cgroup (respaldo)"]
    CSV["mediciones.csv (esquema 8.2)"]
    META["benchmark_metadata.json"]
    EXP["Planes explain / EXPLAIN ANALYZE"]
  end
  subgraph Entregables
    AN["Análisis: tablas, M3, figuras"]
    EVI["Evidencias baseline / spill / OOM"]
    REP["Reporte de 7 secciones"]
  end
  ENT -->|justifica| ESQ
  ADR2 -->|define| ESQ
  ESQ -->|especifica| GEN
  GEN -->|verificado_por| VER
  GEN -->|carga| MDB
  GEN -->|carga| PG
  ADR3 -->|configura| PRF
  PRF -->|parametriza| DC
  DC -->|limita| MDB
  DC -->|limita| PG
  ADR2 -->|define| Q1
  ADR2 -->|define| Q2V1
  ADR1 -->|define| Q2V1
  ADR1 -->|define| Q2V2
  Q1 -->|responde| M1
  Q1 -->|responde| M3
  Q2V1 -->|responde| M2
  Q2V2 -->|responde| M2
  ORQ -->|ejecuta| RUN
  RUN -->|ejecuta| Q1
  RUN -->|ejecuta| Q2V1
  RUN -->|ejecuta| Q2V2
  TEL -->|mide| RUN
  CG -->|respalda| RUN
  RUN -->|produce| CSV
  ADR1 -->|interpreta| CSV
  ORQ -->|produce| META
  ORQ -->|produce| EXP
  CSV -->|alimenta| AN
  AN -->|produce| EVI
  AN -->|alimenta| REP
  EXP -->|respalda| REP
  EVI -->|respalda| REP
  M1 -->|respondida_en| REP
  M2 -->|respondida_en| REP
  M3 -->|respondida_en| REP
```

## Cómo leerlo

- **Trazabilidad hacia atrás:** desde `REP` se llega a la evidencia (`CSV`, `EXP`, `EVI`), al runner que la produjo, a las consultas y, por último, a las decisiones (ADR) y a la entrevista.
- **Cobertura:** cada pregunta M1–M3 tiene al menos una consulta que la responde y termina en el reporte.
- Requisito → archivo: `entregables/CHECKLIST.md`.
