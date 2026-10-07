"""Run FreeCAD operations via FreeCADCmd subprocess (no live GUI required)."""

from __future__ import annotations

import json
import os
import subprocess
import textwrap
from pathlib import Path
from typing import Any, Dict, Optional

from aiva3d.freecad.fcstd_view import ensure_visible_camera
from aiva3d.freecad.protocol import BridgeResponse

DEFAULT_FREECAD_CMD = Path(r"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe")


def detect_freecad_cmd() -> Optional[Path]:
    env = os.environ.get("FREECAD_CMD")
    if env and Path(env).exists():
        return Path(env)
    if DEFAULT_FREECAD_CMD.exists():
        return DEFAULT_FREECAD_CMD
    for candidate in (
        Path(r"C:\Program Files\FreeCAD 0.21\bin\freecadcmd.exe"),
        Path("/usr/bin/freecadcmd"),
        Path("/Applications/FreeCAD.app/Contents/MacOS/FreeCADCmd"),
    ):
        if candidate.exists():
            return candidate
    return None


def _run_script(exe: Path, script: str, timeout: float = 180.0) -> tuple[int, str, str]:
    proc = subprocess.run(
        [str(exe), "-c", script],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return proc.returncode, proc.stdout, proc.stderr


def sync_document_cmd(payload: Dict[str, Any], fcstd_path: Path, document_name: str = "Aiva3D_Handle") -> BridgeResponse:
    """Create or update FCStd from STEP paths using FreeCADCmd."""
    exe = detect_freecad_cmd()
    if exe is None:
        return BridgeResponse(
            success=False,
            command="UPDATE_HANDLE",
            message="FreeCADCmd not found",
            error="Set FREECAD_CMD or install FreeCAD",
        )

    steps = payload["steps"]
    meta_path = payload.get("metadata_path", "")
    fcstd_path.parent.mkdir(parents=True, exist_ok=True)
    parts = [
        ("reference_step", "OriginalMetalHandle", "Reference", False),
        ("hard_step", "HardCore", "Production", True),
        ("soft_step", "SoftGrip", "Production", True),
        ("hard_plus_step", "HardPlus", "Clamshell", True),
        ("hard_minus_step", "HardMinus", "Clamshell", True),
        ("soft_plus_step", "SoftPlus", "Clamshell", True),
        ("soft_minus_step", "SoftMinus", "Clamshell", True),
        ("rails_step", "RailsMale", "ClickSystem", True),
        ("click_step", "ClickLatch", "ClickSystem", True),
    ]
    parts_json = json.dumps(parts)
    steps_json = json.dumps(steps)

    script = textwrap.dedent(
        f"""
import json
import FreeCAD as App
import Part

doc = App.newDocument("{document_name}")
groups = {{
    "Reference": doc.addObject("App::DocumentObjectGroup", "Reference"),
    "Production": doc.addObject("App::DocumentObjectGroup", "Production"),
    "Clamshell": doc.addObject("App::DocumentObjectGroup", "Clamshell"),
    "ClickSystem": doc.addObject("App::DocumentObjectGroup", "ClickSystem"),
    "Metadata": doc.addObject("App::DocumentObjectGroup", "Metadata"),
}}
steps = json.loads(r'''{steps_json}''')
parts = json.loads(r'''{parts_json}''')
meta_path = r"{meta_path}"
colors = {{}}
material_notes = {{}}
if meta_path:
    with open(meta_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    colors = data.get("MaterialColors") or {{}}
    material_notes = data.get("Materials") or {{}}
else:
    data = {{}}

def _color(obj, rgb):
    try:
        obj.ViewObject.ShapeColor = tuple(float(x) for x in rgb)
    except Exception:
        pass

def _load_step(path, label, group_name, production, material):
    shape = Part.read(path)
    obj = doc.addObject("Part::Feature", label)
    obj.Shape = shape
    groups[group_name].addObject(obj)
    if not hasattr(obj, "ProductionPart"):
        obj.addProperty("App::PropertyBool", "ProductionPart", "Aiva3D", "")
    obj.ProductionPart = production
    if not hasattr(obj, "Material"):
        obj.addProperty("App::PropertyString", "Material", "Design", "")
    obj.Material = material
    if not hasattr(obj, "MaterialLabel"):
        obj.addProperty("App::PropertyString", "MaterialLabel", "Design", "")
    note = material_notes.get(material) or {{}}
    obj.MaterialLabel = str(note.get("label") or material)
    rgb = colors.get(label)
    if rgb:
        _color(obj, rgb)
        if label in ("SoftGrip", "SoftPlus", "SoftMinus"):
            try:
                obj.ViewObject.Transparency = 40
            except Exception:
                pass
    return obj

loaded = []
for key, label, group_name, production in parts:
    path = steps.get(key)
    if not path:
        continue
    material = "hard_print"
    if "Soft" in label:
        material = "varishore_foam"
    elif "OriginalMetal" in label or "Metal" in label:
        material = "existing_metal"
    elif label in ("RailsMale", "ClickLatch"):
        material = "click_hard"
    _load_step(path, label, group_name, production, material)
    loaded.append(label)

hard = doc.getObject("HardCore")
soft = doc.getObject("SoftGrip")
if hard is not None:
    if not hasattr(hard, "GripLength"):
        hard.addProperty("App::PropertyLength", "GripLength", "Design", "")
    hard.GripLength = float(data.get("GripLength", 130.0))
    if not hasattr(hard, "HardCoreDiameter"):
        hard.addProperty("App::PropertyLength", "HardCoreDiameter", "Design", "")
    hard.HardCoreDiameter = float(data.get("HardCoreDiameter", 11.1))
if soft is not None:
    if not hasattr(soft, "GripOuterDiameter"):
        soft.addProperty("App::PropertyLength", "GripOuterDiameter", "Design", "")
    soft.GripOuterDiameter = float(data.get("GripOuterDiameter", 30.0))
    if not hasattr(soft, "SoftWallNominal"):
        soft.addProperty("App::PropertyLength", "SoftWallNominal", "Design", "")
    soft.SoftWallNominal = float(data.get("SoftWallNominal", 9.2))

explode_z = {{
    "HardPlus": 32.0,
    "SoftPlus": 32.0,
    "HardMinus": -32.0,
    "SoftMinus": -32.0,
    "RailsMale": -32.0,
    "ClickLatch": -32.0,
    "OriginalMetalHandle": 0.0,
}}
for name, dz in explode_z.items():
    obj = doc.getObject(name)
    if obj is None:
        continue
    pl = obj.Placement
    pl.Base.z = pl.Base.z + dz
    obj.Placement = pl
for hide_name in ("HardCore", "SoftGrip", "OriginalMetalHandle"):
    obj = doc.getObject(hide_name)
    if obj is None:
        continue
    try:
        obj.ViewObject.Visibility = False
    except Exception:
        pass

doc.recompute()
doc.saveAs(r"{fcstd_path}")
print("OK", json.dumps(loaded))
"""
    )
    code, out, err = _run_script(exe, script, timeout=300.0)
    if code != 0 or not fcstd_path.exists():
        return BridgeResponse(
            success=False,
            command="UPDATE_HANDLE",
            message="FreeCADCmd sync failed",
            error=err or out,
        )
    ensure_visible_camera(fcstd_path)
    return BridgeResponse(
        success=True,
        command="UPDATE_HANDLE",
        message="Aiva3D handle synchronized via FreeCADCmd",
        objects=["HardCore", "SoftGrip", "HardPlus", "SoftPlus", "RailsMale", "ClickLatch"],
        extra={"stdout": out.strip(), "path": str(fcstd_path)},
    )


def verify_fcstd_objects(fcstd_path: Path) -> BridgeResponse:
    exe = detect_freecad_cmd()
    if exe is None or not fcstd_path.exists():
        return BridgeResponse(success=False, command="GET_STATUS", message="Cannot verify", error="missing")
    script = textwrap.dedent(
        f"""
import FreeCAD as App
doc = App.openDocument(r"{fcstd_path}")
names = sorted([o.Name for o in doc.Objects])
print(json.dumps(names))
"""
    )
    script = "import json\n" + script
    code, out, err = _run_script(exe, script)
    if code != 0:
        return BridgeResponse(success=False, command="GET_STATUS", message="verify failed", error=err or out)
    try:
        line = next((ln for ln in out.strip().splitlines() if ln.startswith("[")), out.strip())
        names = json.loads(line)
    except json.JSONDecodeError:
        names = []
    expected = {"OriginalMetalHandle", "HardCore", "SoftGrip"}
    ok = expected.issubset(set(names))
    return BridgeResponse(
        success=ok,
        command="GET_STATUS",
        message="FCStd object check",
        objects=names,
        error=None if ok else f"missing {expected - set(names)}",
    )
