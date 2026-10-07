# FreeCAD integration (Aiva3D)

Aiva3D talks to FreeCAD **locally only**. FreeCAD is optional; STEP/STL/3MF export remains the standalone workflow.

## Methods

| Mode | When | Mechanism |
|------|------|-----------|
| **HTTP bridge** | FreeCAD GUI running | `scripts/freecad/aiva3d_bridge_server.py` listens on `127.0.0.1:8765`; Aiva3D posts JSON commands (`PING`, `UPDATE_HANDLE`, `SAVE_DOCUMENT`, …). |
| **FreeCADCmd** | No GUI / batch | `aiva3d/freecad/cmd_runner.py` runs a `-c` script with `freecadcmd.exe` (Windows default: `C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe`). Override with env `FREECAD_CMD`. |

Importing `FreeCAD` into the Aiva3D venv is **not** required and is often incompatible with CadQuery’s Python. Detection uses the installed FreeCAD binary.

## Document layout

```
Aiva3D_Handle
├── Reference / OriginalMetalHandle
├── Production / HardCore, SoftGrip
└── Metadata / Measurements
```

## UI

Streamlit panel: **Connect FreeCAD**, **Create/Update**, **Save**, **Open export folder**.

Live viewport test: start the bridge in FreeCAD, change grip OD in the UI, click **Update FreeCAD**.

## Bridge startup (Windows)

**Option A — FreeCAD GUI (live 3D view):** Python console → `runpy.run_path(r"...\aiva3d_bridge_server.py")`. Console must show `v2026-03-03-v3` and `Bridge self-test OK`.

**Option B — headless (no FreeCAD window):** `powershell -File scripts/start_freecad_bridge.ps1` then open `projects/work/handle_test/exports/handle_assembly.FCStd` in FreeCAD after **Create in FreeCAD**.

After **Connect**, the UI caption must include `bridge 2026-03-03-v3`. If you see `Unknown document 'Aiva3D_Handle'`, an **old** listener is still on port 8765 — quit FreeCAD completely, stop any `freecadcmd` bridge, start the script once again.

If the 3D canvas is empty but objects appear in the tree: switch to **Part** workbench and **View → Standard views → Fit all**. Headless `.FCStd` saves used to clip the camera (`farDistance` smaller than the camera distance); `aiva3d/freecad/fcstd_view.py` rewrites that camera after batch save. Open `handle_assembly.FCStd` or `handle_zichtbaar.FCStd`, not `.FCBak`.

## Code entry points

- `aiva3d/freecad/bridge.py` — connection orchestration
- `aiva3d/freecad/document_builder.py` — STEP + metadata payload
- `scripts/build_freecad_handle.py` — CLI FCStd build
