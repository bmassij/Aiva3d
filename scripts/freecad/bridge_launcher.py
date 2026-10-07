"""Run with FreeCADCmd to start the Aiva3D HTTP bridge (blocks until process exits)."""
from __future__ import annotations

import runpy
import time
from pathlib import Path

runpy.run_path(str(Path(__file__).resolve().parent / "aiva3d_bridge_server.py"))
time.sleep(999999)
