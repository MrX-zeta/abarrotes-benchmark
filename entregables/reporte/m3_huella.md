# M3 — Huella por cada 1 000 documentos procesados

Definición (ADR-003): documentos procesados = consultas completadas × 500 000 (cada consulta evalúa la colección completa). CPU = segundos de CPU del cgroup del motor en la ventana de 300 s. Memoria = max_rss_mb / 500. Mediana de las repeticiones.

| Motor | Perfil | Consulta | Conc. | CPU ms / 1 000 docs | RSS MB / 1 000 docs |
|---|---|---|---|---|---|
| mongodb | A | Q1 | 1 | 6.885 | 1.8182 |
| mongodb | A | Q1 | 10 | 7.739 | 1.9279 |
| mongodb | A | Q1 | 50 | 9.555 | 2.2794 |
| mongodb | A | Q2_V1 | 1 | 1.798 | 1.8886 |
| mongodb | A | Q2_V1 | 10 | 1.879 | 1.9870 |
| mongodb | A | Q2_V1 | 50 | 1.908 | 2.2542 |
| mongodb | A | Q2_V2 | 1 | 1.760 | 1.8942 |
| mongodb | A | Q2_V2 | 10 | 1.811 | 1.9813 |
| mongodb | A | Q2_V2 | 50 | 1.914 | 2.2570 |
| mongodb | B | Q1 | 1 | 8.238 | 1.4519 |
| mongodb | B | Q1 | 10 | 9.672 | 1.5183 |
| mongodb | B | Q1 | 50 | 11.983 | 1.7129 |
| mongodb | B | Q2_V1 | 1 | 22.618 | 1.3424 |
| mongodb | B | Q2_V1 | 10 | 11.996 | 1.3716 |
| mongodb | B | Q2_V1 | 50 | 8.574 | 1.6729 |
| mongodb | B | Q2_V2 | 1 | 21.859 | 1.3487 |
| mongodb | B | Q2_V2 | 10 | 11.993 | 1.3665 |
| mongodb | B | Q2_V2 | 50 | 8.344 | 1.6736 |
| mongodb | C | Q1 | 1 | 8.957 | 0.9032 |
| mongodb | C | Q1 | 10 | 11.525 | 0.9421 |
| mongodb | C | Q1 | 50 | — | 1.1920 |
| mongodb | C | Q2_V1 | 1 | 35.294 | 0.8154 |
| mongodb | C | Q2_V1 | 10 | 29.957 | 0.8490 |
| mongodb | C | Q2_V1 | 50 | 11.991 | 1.1557 |
| mongodb | C | Q2_V2 | 1 | 35.276 | 0.8212 |
| mongodb | C | Q2_V2 | 10 | 20.018 | 0.8487 |
| mongodb | C | Q2_V2 | 50 | 11.994 | 1.1643 |
| postgresql | A | Q1 | 1 | 21.173 | 0.2024 |
| postgresql | A | Q1 | 10 | 27.306 | 1.1645 |
| postgresql | A | Q1 | 50 | 563.129 | 4.1010 |
| postgresql | A | Q2_V1 | 1 | 4.877 | 0.0699 |
| postgresql | A | Q2_V1 | 10 | 5.015 | 0.3613 |
| postgresql | A | Q2_V1 | 50 | 5.247 | 1.1972 |
| postgresql | A | Q2_V2 | 1 | 4.890 | 0.0699 |
| postgresql | A | Q2_V2 | 10 | 5.071 | 0.3613 |
| postgresql | A | Q2_V2 | 50 | 5.224 | 1.1981 |
| postgresql | B | Q1 | 1 | 21.366 | 0.2020 |
| postgresql | B | Q1 | 10 | 41.303 | 1.1585 |
| postgresql | B | Q1 | 50 | — | 3.6273 |
| postgresql | B | Q2_V1 | 1 | 5.195 | 0.0700 |
| postgresql | B | Q2_V1 | 10 | 5.529 | 0.3593 |
| postgresql | B | Q2_V1 | 50 | 6.845 | 1.1899 |
| postgresql | B | Q2_V2 | 1 | 5.283 | 0.0700 |
| postgresql | B | Q2_V2 | 10 | 5.717 | 0.3595 |
| postgresql | B | Q2_V2 | 50 | 6.891 | 1.1910 |
| postgresql | C | Q1 | 1 | 29.443 | 0.2013 |
| postgresql | C | Q1 | 10 | 149.576 | 1.1521 |
| postgresql | C | Q1 | 50 | — | 1.9782 |
| postgresql | C | Q2_V1 | 1 | 5.310 | 0.0700 |
| postgresql | C | Q2_V1 | 10 | 7.049 | 0.3580 |
| postgresql | C | Q2_V1 | 50 | 11.282 | 1.1884 |
| postgresql | C | Q2_V2 | 1 | 5.350 | 0.0699 |
| postgresql | C | Q2_V2 | 10 | 6.731 | 0.3580 |
| postgresql | C | Q2_V2 | 50 | 11.451 | 1.1883 |
