@echo off
chcp 65001 >nul
title 00 - Preparar Windows para el benchmark
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0windows\00_preparar_windows.ps1"
echo.
echo Resultado guardado en results\windows_00_preparar.log
pause
