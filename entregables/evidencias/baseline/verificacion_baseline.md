# Verificación del baseline (perfil A, sección 2)

Criterio: el perfil A debe estar libre de contención: throttling ≈ 0 s en la ventana de 300 s, sin spill y sin OOM.

| Motor | Consulta | Conc. | Throttling s (mediana [mín–máx]) | Throttling / 300 s | Spill | Estados |
|---|---|---|---|---|---|---|
| mongodb | Q1 | 1 | 0.000 [0.000–0.000] | 0.00 % | 0/3 | ok:3 |
| mongodb | Q1 | 10 | 1.709 [0.622–1.932] | 0.57 % | 0/3 | ok:3 |
| mongodb | Q1 | 50 | 2.596 [1.815–2.818] | 0.87 % | 0/3 | ok:3 |
| mongodb | Q2_V1 | 1 | 0.000 [0.000–0.000] | 0.00 % | 0/3 | ok:3 |
| mongodb | Q2_V1 | 10 | 1.306 [0.451–1.765] | 0.44 % | 0/3 | ok:3 |
| mongodb | Q2_V1 | 50 | 1.380 [0.692–1.902] | 0.46 % | 0/3 | ok:3 |
| mongodb | Q2_V2 | 1 | 0.000 [0.000–0.000] | 0.00 % | 0/3 | ok:3 |
| mongodb | Q2_V2 | 10 | 1.641 [0.872–2.314] | 0.55 % | 0/3 | ok:3 |
| mongodb | Q2_V2 | 50 | 1.657 [0.391–1.664] | 0.55 % | 0/3 | ok:3 |
| postgresql | Q1 | 1 | 0.000 [0.000–0.000] | 0.00 % | 3/3 | spill:3 |
| postgresql | Q1 | 10 | 0.317 [0.252–0.336] | 0.11 % | 3/3 | spill:3 |
| postgresql | Q1 | 50 | 0.144 [0.139–0.166] | 0.05 % | 3/3 | spill:3 |
| postgresql | Q2_V1 | 1 | 0.000 [0.000–0.000] | 0.00 % | 0/3 | ok:3 |
| postgresql | Q2_V1 | 10 | 1.637 [1.631–2.120] | 0.55 % | 0/3 | ok:3 |
| postgresql | Q2_V1 | 50 | 2.190 [0.746–2.349] | 0.73 % | 0/3 | ok:3 |
| postgresql | Q2_V2 | 1 | 0.000 [0.000–0.000] | 0.00 % | 0/3 | ok:3 |
| postgresql | Q2_V2 | 10 | 0.842 [0.760–1.833] | 0.28 % | 0/3 | ok:3 |
| postgresql | Q2_V2 | 50 | 1.604 [0.712–1.789] | 0.53 % | 0/3 | ok:3 |

Throttling máximo observado en A: **2.818 s** (cumple: umbral 1 % de la ventana = 3 s).
Corridas de A con spill: **9**; con oom/error: **0**.
