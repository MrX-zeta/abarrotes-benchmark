# Extractos de logs de spill y OOM

Extraídos de `results/logs/<run_id>.log` (logs del motor durante la corrida) y `results/limits/<run_id>.post.json` (`docker inspect` al terminar). Un archivo por corrida con spill, OOM o error.

- `mongodb_C_Q1_c50_r1.txt` — **error**, spill=FALSE, 0 líneas de log relevantes
- `mongodb_C_Q1_c50_r2.txt` — **error**, spill=FALSE, 0 líneas de log relevantes
- `mongodb_C_Q1_c50_r3.txt` — **error**, spill=FALSE, 0 líneas de log relevantes
- `mongodb_C_Q2_V1_c50_r3.txt` — **error**, spill=FALSE, 50 líneas de log relevantes
- `mongodb_C_Q2_V2_c50_r1.txt` — **error**, spill=FALSE, 50 líneas de log relevantes
- `mongodb_C_Q2_V2_c50_r3.txt` — **error**, spill=FALSE, 50 líneas de log relevantes
- `postgresql_A_Q1_c1_r1.txt` — **spill**, spill=TRUE, 637 líneas de log relevantes
- `postgresql_A_Q1_c1_r2.txt` — **spill**, spill=TRUE, 669 líneas de log relevantes
- `postgresql_A_Q1_c1_r3.txt` — **spill**, spill=TRUE, 706 líneas de log relevantes
- `postgresql_A_Q1_c10_r1.txt` — **spill**, spill=TRUE, 1434 líneas de log relevantes
- `postgresql_A_Q1_c10_r2.txt` — **spill**, spill=TRUE, 1434 líneas de log relevantes
- `postgresql_A_Q1_c10_r3.txt` — **spill**, spill=TRUE, 1412 líneas de log relevantes
- `postgresql_A_Q1_c50_r1.txt` — **spill**, spill=TRUE, 1313 líneas de log relevantes
- `postgresql_A_Q1_c50_r2.txt` — **spill**, spill=TRUE, 1270 líneas de log relevantes
- `postgresql_A_Q1_c50_r3.txt` — **spill**, spill=TRUE, 1157 líneas de log relevantes
- `postgresql_B_Q1_c1_r1.txt` — **spill**, spill=TRUE, 620 líneas de log relevantes
- `postgresql_B_Q1_c1_r2.txt` — **spill**, spill=TRUE, 614 líneas de log relevantes
- `postgresql_B_Q1_c1_r3.txt` — **spill**, spill=TRUE, 560 líneas de log relevantes
- `postgresql_B_Q1_c10_r1.txt` — **spill**, spill=TRUE, 615 líneas de log relevantes
- `postgresql_B_Q1_c10_r2.txt` — **spill**, spill=TRUE, 603 líneas de log relevantes
- `postgresql_B_Q1_c10_r3.txt` — **spill**, spill=TRUE, 631 líneas de log relevantes
- `postgresql_B_Q1_c50_r1.txt` — **oom**, spill=TRUE, 98 líneas de log relevantes
- `postgresql_B_Q1_c50_r2.txt` — **oom**, spill=TRUE, 94 líneas de log relevantes
- `postgresql_B_Q1_c50_r3.txt` — **oom**, spill=TRUE, 100 líneas de log relevantes
- `postgresql_C_Q1_c1_r1.txt` — **spill**, spill=TRUE, 358 líneas de log relevantes
- `postgresql_C_Q1_c1_r2.txt` — **spill**, spill=TRUE, 365 líneas de log relevantes
- `postgresql_C_Q1_c1_r3.txt` — **spill**, spill=TRUE, 395 líneas de log relevantes
- `postgresql_C_Q1_c10_r1.txt` — **spill**, spill=TRUE, 268 líneas de log relevantes
- `postgresql_C_Q1_c10_r2.txt` — **spill**, spill=TRUE, 274 líneas de log relevantes
- `postgresql_C_Q1_c10_r3.txt` — **error**, spill=TRUE, 248 líneas de log relevantes
- `postgresql_C_Q1_c50_r1.txt` — **oom**, spill=FALSE, 15 líneas de log relevantes
- `postgresql_C_Q1_c50_r2.txt` — **oom**, spill=FALSE, 90 líneas de log relevantes
- `postgresql_C_Q1_c50_r3.txt` — **oom**, spill=FALSE, 15 líneas de log relevantes
