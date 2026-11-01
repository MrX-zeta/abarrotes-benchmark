@echo off
chcp 65001 >nul
title 02 - MATRIZ COMPLETA (~20 h) - NO CERRAR ESTA VENTANA
cd /d "%~dp0"
wsl --cd "%~dp0." -- bash -c "bash run_benchmarks.sh all 2>&1 | tee -a results/consola_matriz.log"
echo.
echo Matriz terminada. Salida en results\consola_matriz.log
pause
