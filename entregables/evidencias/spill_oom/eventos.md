# Eventos de spill, OOM y error (sección 6)

Cada fila apunta a su evidencia: `results/logs/<run_id>.log`, `results/limits/<run_id>.post.json` y `results/raw/<run_id>.json` (campo `final.notas`).

| run_id | Estado | Spill | Notas |
|---|---|---|---|
| mongodb_C_Q1_c50_r1 | error | false | ninguna consulta completada dentro de la ventana |
| mongodb_C_Q1_c50_r2 | error | false | ninguna consulta completada dentro de la ventana |
| mongodb_C_Q1_c50_r3 | error | false | ninguna consulta completada dentro de la ventana |
| mongodb_C_Q2_V1_c50_r3 | error | false | ninguna consulta completada dentro de la ventana |
| mongodb_C_Q2_V2_c50_r1 | error | false | ninguna consulta completada dentro de la ventana |
| mongodb_C_Q2_V2_c50_r3 | error | false | ninguna consulta completada dentro de la ventana |
| postgresql_A_Q1_c1_r1 | spill | true | spill: temp_files 90 -> 635; spill: temp_bytes 5576491008 -> 39833329664; spill: log 'temporary file' |
| postgresql_A_Q1_c1_r2 | spill | true | spill: temp_files 185 -> 747; spill: temp_bytes 45898547200 -> 81106976768; spill: log 'temporary file' |
| postgresql_A_Q1_c1_r3 | spill | true | spill: temp_files 105 -> 704; spill: temp_bytes 6506004480 -> 43668029440; spill: log 'temporary file' |
| postgresql_A_Q1_c10_r1 | spill | true | spill: temp_files 137 -> 1427; spill: temp_bytes 9293561856 -> 102615908352; spill: log 'temporary file' |
| postgresql_A_Q1_c10_r2 | spill | true | spill: temp_files 155 -> 1427; spill: temp_bytes 11132690432 -> 96011968512; spill: log 'temporary file' |
| postgresql_A_Q1_c10_r3 | spill | true | spill: temp_files 137 -> 1405; spill: temp_bytes 9293586432 -> 95775236096; spill: log 'temporary file' |
| postgresql_A_Q1_c50_r1 | spill | true | spill: temp_files 0 -> 1306; spill: temp_bytes 0 -> 94916100096; spill: log 'temporary file' |
| postgresql_A_Q1_c50_r2 | spill | true | spill: temp_files 0 -> 1263; spill: temp_bytes 0 -> 94408622080; spill: log 'temporary file' |
| postgresql_A_Q1_c50_r3 | spill | true | spill: temp_files 0 -> 1150; spill: temp_bytes 0 -> 92760334336; spill: log 'temporary file' |
| postgresql_B_Q1_c1_r1 | spill | true | spill: temp_files 90 -> 618; spill: temp_bytes 5576671232 -> 38798073856; spill: log 'temporary file' |
| postgresql_B_Q1_c1_r2 | spill | true | spill: temp_files 105 -> 612; spill: temp_bytes 6505963520 -> 38051708928; spill: log 'temporary file' |
| postgresql_B_Q1_c1_r3 | spill | true | spill: temp_files 1240 -> 1708; spill: temp_bytes 98336940032 -> 127780790272; spill: log 'temporary file' |
| postgresql_B_Q1_c10_r1 | spill | true | spill: temp_files 0 -> 611; spill: temp_bytes 0 -> 40912363520; spill: log 'temporary file' |
| postgresql_B_Q1_c10_r2 | spill | true | spill: temp_files 0 -> 596; spill: temp_bytes 0 -> 40598290432; spill: log 'temporary file' |
| postgresql_B_Q1_c10_r3 | spill | true | spill: temp_files 0 -> 624; spill: temp_bytes 0 -> 46712315904; spill: log 'temporary file' |
| postgresql_B_Q1_c50_r1 | oom | true | spill: temp_files 0 -> 57; spill: temp_bytes 0 -> 20595802112; spill: log 'temporary file'; docker inspect: OOMKilled; log: proceso terminado por señal 9 (OOM killer); ninguna consulta completada dentro de la ventana; 121/171 consultas fallidas (> 5%); códigos ['OperationalError'] |
| postgresql_B_Q1_c50_r2 | oom | true | spill: temp_bytes 22506520576 -> 39392608256; spill: log 'temporary file'; docker inspect: OOMKilled; log: proceso terminado por señal 9 (OOM killer); ninguna consulta completada dentro de la ventana; 99/149 consultas fallidas (> 5%); códigos ['OperationalError'] |
| postgresql_B_Q1_c50_r3 | oom | true | spill: temp_files 0 -> 57; spill: temp_bytes 0 -> 8454078464; spill: log 'temporary file'; docker inspect: OOMKilled; log: proceso terminado por señal 9 (OOM killer); ninguna consulta completada dentro de la ventana; 150/200 consultas fallidas (> 5%); códigos ['OperationalError'] |
| postgresql_C_Q1_c1_r1 | spill | true | spill: temp_files 45 -> 356; spill: temp_bytes 2788294656 -> 22233448448; spill: log 'temporary file' |
| postgresql_C_Q1_c1_r2 | spill | true | spill: temp_files 60 -> 363; spill: temp_bytes 3717709824 -> 22506520576; spill: log 'temporary file' |
| postgresql_C_Q1_c1_r3 | spill | true | spill: temp_files 60 -> 393; spill: temp_bytes 3717742592 -> 24949137408; spill: log 'temporary file' |
| postgresql_C_Q1_c10_r1 | spill | true | spill: temp_files 0 -> 261; spill: temp_bytes 0 -> 20740284416; spill: log 'temporary file' |
| postgresql_C_Q1_c10_r2 | spill | true | spill: temp_files 0 -> 267; spill: temp_bytes 0 -> 20686487552; spill: log 'temporary file' |
| postgresql_C_Q1_c10_r3 | error | true | spill: temp_files 1708 -> 1949; spill: temp_bytes 127780790272 -> 145752236032; spill: log 'temporary file'; ninguna consulta completada dentro de la ventana |
| postgresql_C_Q1_c50_r1 | oom | false | docker inspect: OOMKilled; log: proceso terminado por señal 9 (OOM killer); ninguna consulta completada dentro de la ventana; 3353/3353 consultas fallidas (> 5%); códigos ['ConnectionTimeout', 'OperationalError'] |
| postgresql_C_Q1_c50_r2 | oom | false | docker inspect: OOMKilled; log: proceso terminado por señal 9 (OOM killer); ninguna consulta completada dentro de la ventana; 8882/8882 consultas fallidas (> 5%); códigos ['OperationalError'] |
| postgresql_C_Q1_c50_r3 | oom | false | docker inspect: OOMKilled; log: proceso terminado por señal 9 (OOM killer); ninguna consulta completada dentro de la ventana; 3416/3416 consultas fallidas (> 5%); códigos ['ConnectionTimeout', 'OperationalError'] |

Fuente de los KPIs de contenedor por corrida: {'prometheus': 162}
