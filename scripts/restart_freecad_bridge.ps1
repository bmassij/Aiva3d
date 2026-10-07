# Stop anything listening on 8765, then start one Aiva3D bridge (FreeCADCmd).
$ErrorActionPreference = "Stop"
$port = 8765
Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique |
    ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 2
& (Join-Path $PSScriptRoot "start_freecad_bridge.ps1")
