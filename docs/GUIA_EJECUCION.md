# Guía de ejecución (Windows 11 + Docker Desktop + WSL2)

Equipo de referencia: Acer con Intel i7-13620H (10 núcleos / 16 hilos), 36 GB de RAM, WSL 2.6.3.
Tiempo total: ~1 h de preparación + **~20 h de matriz** + ~15 min de explain + análisis.

## 0. Preparar Windows (una sola vez)

1. **Docker Desktop** instalado con el backend **WSL 2**. En una terminal de PowerShell, `docker version` debe mostrar *Client* y *Server*.
2. **Ubuntu en WSL:** `wsl --install -d Ubuntu` (si no lo tienes). Luego, en Docker Desktop → *Settings → Resources → WSL integration*, activa **Ubuntu**.
3. **Recursos de la VM.** Crea o edita `C:\Users\brian\.wslconfig`:
   ```ini
   [wsl2]
   memory=24GB
   processors=16
   swap=0
   ```
   Después, en PowerShell, ejecuta `wsl --shutdown` y vuelve a abrir Docker Desktop.
4. **Energía:** conectada a la corriente, plan de **Alto rendimiento** (o "Mejor rendimiento"), **suspensión: nunca** (incluido al cerrar la tapa) y **actualizaciones de Windows en pausa** durante una semana.
5. Cierra todo lo que no sea necesario (navegador, juegos, etc.). Cualquier otro proceso compite por la CPU.

## Atajo: lanzadores de doble clic

En la raíz del proyecto hay lanzadores que hacen los pasos anteriores y guardan su salida en `results/`, para revisarla después:

| Archivo | Qué hace | Duración |
|---|---|---|
| `INICIAR_00_preparar_windows.bat` | Revisa Docker y Ubuntu, escribe `.wslconfig` (guarda un respaldo), quita la suspensión con corriente, reinicia WSL y Docker Desktop, y verifica. Log: `results/windows_00_preparar.log` | ~3 min |
| `INICIAR_01_setup_y_piloto.bat` | `check` → `setup` → `smoke` → `pilot`. Log: `results/consola_01_preparacion.log` | ~45 min |
| `INICIAR_02_matriz_completa.bat` | `all`: 162 corridas + explain + análisis. **No cerrar la ventana.** | ~20 h |
| `INICIAR_03_ver_avance.bat` | Muestra el avance de la matriz | instantáneo |

## 1. Abrir el proyecto en Ubuntu

```bash
cd "/mnt/c/Users/brian/UPchiapas/Septimo Cuatri/Optativa I/U2/2026.C3.EVA02/abarrotes-benchmark"
cp -n .env.example .env
bash run_benchmarks.sh check
```

`check` debe mostrar **cgroups v2**, **16 CPUs** y alrededor de **24 GiB**. Si muestra otra cosa, revisa el paso 0.3.

## 2. Preparación (~20–30 min)

```bash
bash run_benchmarks.sh setup
```

Este paso descarga las imágenes, construye el runner, levanta la telemetría, registra el host y las versiones, genera los 500 000 pedidos, los verifica, los carga en ambos motores y crea el plan de 162 corridas.

## 3. Prueba rápida (~8 min)

```bash
bash run_benchmarks.sh smoke
```

Corre ambos motores con las 3 consultas en ventanas cortas y muestra el CSV. Revisa que haya 6 filas con las 14 columnas. Que algunas salgan `error` por "ninguna consulta completada" es normal con ventanas de 30 s.

## 4. Celda piloto con tiempos oficiales (~8 min)

```bash
bash run_benchmarks.sh pilot
```

Corre MongoDB · perfil C · Q1 · 10 clientes con 60 s de warmup + 300 s de medición + 60 s de cooldown. Revisa `results/pilot/csv/mediciones.csv`. **Si el CSV se ve bien, lanza la matriz.**

## 5. Matriz completa + explain + análisis (~20 h)

```bash
bash run_benchmarks.sh all 2>&1 | tee -a results/consola_matriz.log
```

- **Deja abierta esa ventana de Ubuntu.**
- Para ver el avance desde otra ventana: `bash run_benchmarks.sh status`.
- Si se interrumpe (corte de luz, reinicio), vuelve a ejecutar el mismo comando: **reanuda** desde la última corrida terminada.
- Prometheus queda en http://localhost:9090 por si quieres ver las métricas en vivo.

## 6. Al terminar

`all` deja listo lo siguiente:

- `entregables/mediciones.csv`: CSV consolidado (esquema 8.2).
- `entregables/reporte/tablas_resumen.md`, `m3_huella.md` y `figuras/*.png`.
- `entregables/evidencias/baseline/verificacion_baseline.md` y `spill_oom/eventos.md`.
- `results/explain/`: planes de ejecución.

Con eso se redactan las 7 secciones de `entregables/reporte/reporte_metricas.md`.

## Problemas frecuentes

| Síntoma | Causa / solución |
|---|---|
| `range of CPUs is from 0.01 to N` | La VM tiene menos de 4 CPUs: revisa `.wslconfig` y ajusta `DB_CPUSET` en `.env`. |
| `docker: command not found` en Ubuntu | Falta activar la integración WSL de Docker Desktop (paso 0.2). |
| `$'\r': command not found` | El archivo se guardó con saltos de línea de Windows. Ejecuta `sed -i 's/\r$//' run_benchmarks.sh scripts/*.sh`. |
| La matriz se detuvo | Vuelve a ejecutar `bash run_benchmarks.sh all`; las corridas terminadas se omiten. |
| `prometheus sin datos` en las notas | No afecta: los KPIs se toman del cgroup (mismos contadores). Queda registrado en cada corrida. |
