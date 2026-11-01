#!/usr/bin/env bash
# collect_host_info.sh — Especificaciones del host y del entorno Docker (reporte, sección 1).
# En Windows, Docker Desktop corre dentro de la VM de WSL2: los límites y el throttling se aplican
# y se miden en esa VM. Este script registra ambas capas cuando están disponibles.
OUT=${1:-results/host/host_info.txt}
mkdir -p "$(dirname "$OUT")"
{
  echo "# Host y entorno Docker — $(date -u +%FT%TZ)"
  echo
  echo "## Windows (si aplica)"
  if command -v powershell.exe >/dev/null 2>&1; then
    powershell.exe -NoProfile -Command "Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors | Format-List; Get-CimInstance Win32_ComputerSystem | Select-Object Manufacturer,Model,TotalPhysicalMemory | Format-List; Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber | Format-List" 2>/dev/null | tr -d '\r'
    WINHOME=$(wslpath "$(cmd.exe /c 'echo %USERPROFILE%' 2>/dev/null | tr -d '\r')" 2>/dev/null)
    echo "### .wslconfig"; cat "$WINHOME/.wslconfig" 2>/dev/null || echo "(no existe)"
    echo "### wsl --version"; wsl.exe --version 2>/dev/null | tr -d '\r\000'
  else
    echo "(no es WSL)"
  fi
  echo
  echo "## Linux (VM / host donde corre Docker)"
  uname -a
  echo "nproc: $(nproc)"
  lscpu 2>/dev/null | grep -E 'Model name|^CPU\(s\)|Thread|Core|Socket|MHz'
  free -m
  echo "cgroup fs (host): $(stat -fc %T /sys/fs/cgroup/ 2>/dev/null)"
  echo "swap:"; swapon --show 2>/dev/null || cat /proc/swaps
  echo
  echo "## Docker"
  docker version 2>/dev/null
  echo
  docker info 2>/dev/null
  echo
  echo "cgroup fs visto por un contenedor: $(docker run --rm alpine:3.20 stat -fc %T /sys/fs/cgroup/ 2>/dev/null)"
  echo "kernel visto por un contenedor: $(docker run --rm alpine:3.20 uname -r 2>/dev/null)"
  echo "CPUs y memoria vistos por un contenedor:"
  docker run --rm alpine:3.20 sh -c 'nproc; grep -E "MemTotal|SwapTotal" /proc/meminfo' 2>/dev/null
  echo
  echo "## Disco del proyecto"
  df -h .
} > "$OUT" 2>&1
echo "host info -> $OUT"
