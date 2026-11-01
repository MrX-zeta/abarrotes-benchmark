@echo off
chcp 65001 >nul
title 01 - Setup, prueba rapida y celda piloto (~45 min)
cd /d "%~dp0"
wsl --cd "%~dp0." -- bash -c "mkdir -p results; (bash run_benchmarks.sh check && bash run_benchmarks.sh setup && bash run_benchmarks.sh smoke && bash run_benchmarks.sh pilot) 2>&1 | tee -a results/consola_01_preparacion.log"
echo.
echo Terminado. Salida en results\consola_01_preparacion.log
pause
