# Start the Aiva3D HTTP bridge (FreeCADCmd, one listener on 8765).
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$FreeCadCmd = $env:FREECAD_CMD
if (-not $FreeCadCmd) { $FreeCadCmd = "C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" }
if (-not (Test-Path $FreeCadCmd)) {
    Write-Error "FreeCADCmd not found at $FreeCadCmd. Set FREECAD_CMD or install FreeCAD 1.1."
}
$Launcher = Join-Path $Root "scripts\freecad\bridge_launcher.py"
Start-Process -FilePath $FreeCadCmd -ArgumentList @($Launcher) -WindowStyle Minimized
Write-Host "Bridge starting on http://127.0.0.1:8765 (FreeCADCmd). Wait ~5s, then Connect in Streamlit."
