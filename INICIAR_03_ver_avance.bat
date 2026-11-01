@echo off
chcp 65001 >nul
title 03 - Avance de la matriz
cd /d "%~dp0"
wsl --cd "%~dp0." -- bash run_benchmarks.sh status
pause
