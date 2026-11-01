# 00_preparar_windows.ps1 - Prepara Windows para el benchmark (pasos 0.1-0.4 de docs/GUIA_EJECUCION.md).
# Deja todo registrado en results\windows_00_preparar.log para que se pueda revisar.
$ErrorActionPreference = 'Continue'
$env:WSL_UTF8 = '1'
$root = Split-Path -Parent $PSScriptRoot
New-Item -ItemType Directory -Force -Path (Join-Path $root 'results') | Out-Null
$log = Join-Path $root 'results\windows_00_preparar.log'
Start-Transcript -Path $log -Append | Out-Null
Write-Host "=== Preparación de Windows $(Get-Date -Format s) ==="

Write-Host "`n=== 1. Docker Desktop"
$dockerExe = Join-Path $env:ProgramFiles 'Docker\Docker\Docker Desktop.exe'
if (Test-Path $dockerExe) { Write-Host "Docker Desktop instalado: $dockerExe" } else { Write-Host "FALTA: Docker Desktop no está instalado en $dockerExe" }
docker version --format 'Cliente {{.Client.Version}} / Servidor {{.Server.Version}}' 2>&1

Write-Host "`n=== 2. Distribuciones de WSL"
wsl -l -v 2>&1
$distros = (wsl -l -q 2>$null) | ForEach-Object { $_.Trim() } | Where-Object { $_ -and $_ -notlike 'docker-desktop*' }
$ubuntu = $distros | Where-Object { $_ -like 'Ubuntu*' } | Select-Object -First 1
if ($ubuntu) { Write-Host "Distribución para el benchmark: $ubuntu" } else { Write-Host "FALTA: no hay una distribución Ubuntu. Ejecuta en PowerShell: wsl --install -d Ubuntu" }

Write-Host "`n=== 3. .wslconfig (24 GB, 16 CPUs, sin swap)"
$cfg = Join-Path $env:USERPROFILE '.wslconfig'
if (Test-Path $cfg) {
  $bak = "$cfg.bak-$(Get-Date -Format yyyyMMdd-HHmmss)"
  Copy-Item $cfg $bak
  Write-Host "Respaldo del .wslconfig anterior: $bak"
  Get-Content $cfg
}
"[wsl2]`r`nmemory=24GB`r`nprocessors=16`r`nswap=0`r`n" | Set-Content -Path $cfg -Encoding ascii
Write-Host "Nuevo .wslconfig:"; Get-Content $cfg

Write-Host "`n=== 4. Energía (conectado a corriente): sin suspensión ni hibernación, tapa sin acción"
powercfg /change standby-timeout-ac 0
powercfg /change hibernate-timeout-ac 0
powercfg /setacvalueindex SCHEME_CURRENT SUB_BUTTONS LIDACTION 0
powercfg /setactive SCHEME_CURRENT
powercfg /query SCHEME_CURRENT SUB_SLEEP STANDBYIDLE 2>&1 | Select-String 'Current AC|actual de CA'

Write-Host "`n=== 5. Reinicio de WSL y Docker Desktop para aplicar .wslconfig"
Get-Process -Name 'Docker Desktop' -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep 3
wsl --shutdown
Start-Sleep 5
if (Test-Path $dockerExe) { Start-Process $dockerExe }
$ok = $false
for ($i = 0; $i -lt 60; $i++) {
  docker info --format '{{.ServerVersion}}' 2>$null | Out-Null
  if ($LASTEXITCODE -eq 0) { $ok = $true; break }
  Start-Sleep 5
}
if ($ok) { Write-Host "Docker listo." } else { Write-Host "FALTA: Docker no respondió en 5 minutos. Abre Docker Desktop manualmente." }

Write-Host "`n=== 6. Verificación"
docker info --format 'CPUs VM: {{.NCPU}} | RAM VM: {{.MemTotal}} bytes | cgroups v{{.CgroupVersion}} | Docker {{.ServerVersion}}' 2>&1
if ($ubuntu) {
  wsl -d $ubuntu -- bash -c "docker version --format 'Docker desde ${ubuntu}: {{.Server.Version}}' 2>&1 || echo 'FALTA: activa Docker Desktop > Settings > Resources > WSL integration > $ubuntu'"
}
Write-Host "`n=== Listo. Pendiente manual: pausar actualizaciones de Windows 1 semana y modo de energía 'Mejor rendimiento'."
Stop-Transcript | Out-Null
