"""
Photo-based handle reconstruction: build, validate, export, FreeCAD smoke test, report.

Outputs under exports/verification/handle_test/
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import cadquery as cq

from projects.work.handle_test.model import (
    build,
    build_assembly_compound,
    build_hard_core,
    build_soft_outer_shell,
)
from projects.work.handle_test.measurements_loader import load_measurements_doc
from projects.work.handle_test.parameters import default_parameters
from projects.work.handle_test.validation import validate_export_file, validate_handle_pair

OUT = ROOT / "exports" / "verification" / "handle_test"
FREECAD_CMD = Path(r"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe")


def _export_step(workpiece: cq.Workplane, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(workpiece, str(path))


def _export_stl(workpiece: cq.Workplane, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(workpiece, str(path), tolerance=0.1, angularTolerance=0.1)


def _export_3mf(workpiece: cq.Workplane, path: Path) -> None:
    import tempfile

    import trimesh

    with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as tmp:
        stl = Path(tmp.name)
    try:
        cq.exporters.export(workpiece, str(stl), tolerance=0.1, angularTolerance=0.1)
        mesh = trimesh.load_mesh(str(stl), process=False)
        mesh.export(str(path), file_type="3mf")
    finally:
        stl.unlink(missing_ok=True)


def _freecad_step_check(step_path: Path) -> dict:
    if not FREECAD_CMD.exists():
        return {"ok": False, "error": f"FreeCADCmd not found at {FREECAD_CMD}"}
    script = f"""
import FreeCAD as App
import Part
doc = App.newDocument("check")
shape = Part.read(r"{step_path}")
if shape.isNull():
    raise RuntimeError("STEP read failed")
print("SOLIDS", len(shape.Solids))
print("VOLUME", shape.Volume)
print("BBOX", shape.BoundBox.XLength, shape.BoundBox.YLength, shape.BoundBox.ZLength)
"""
    proc = subprocess.run(
        [str(FREECAD_CMD), "-c", script],
        capture_output=True,
        text=True,
        timeout=120,
    )
    return {
        "ok": proc.returncode == 0,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip()[-500:] if proc.stderr else "",
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    params = default_parameters()
    hard, soft = build(params)
    stats = validate_handle_pair(hard, soft, params)
    complete = build_assembly_compound(params)

    files = {
        "handle_hard_core.step": OUT / "handle_hard_core.step",
        "handle_soft_outer.step": OUT / "handle_soft_outer.step",
        "handle_complete.step": OUT / "handle_complete.step",
        "handle_complete.stl": OUT / "handle_complete.stl",
        "handle_complete.3mf": OUT / "handle_complete.3mf",
    }

    _export_step(hard, files["handle_hard_core.step"])
    _export_step(soft, files["handle_soft_outer.step"])
    _export_step(complete, files["handle_complete.step"])
    _export_stl(complete, files["handle_complete.stl"])
    _export_3mf(complete, files["handle_complete.3mf"])

    export_checks = {k: validate_export_file(v) for k, v in files.items()}
    fc_hard = _freecad_step_check(files["handle_hard_core.step"])
    fc_soft = _freecad_step_check(files["handle_soft_outer.step"])
    fc_complete = _freecad_step_check(files["handle_complete.step"])

    mdoc = load_measurements_doc()
    verified = mdoc.get("photo_grid_counts_verified") or {}
    assumptions = [verified.get("notes", "centerline bow from traced sleeve")]
    unresolved = []

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "validation": stats,
        "exports": export_checks,
        "freecad": {
            "handle_hard_core": fc_hard,
            "handle_soft_outer": fc_soft,
            "handle_complete": fc_complete,
        },
        "assumptions": assumptions,
        "unresolved_parameters": unresolved,
        "visual_correspondence": {
            "grip_span_target_mm": 85,
            "grip_span_model_mm": stats["grip_span_y_mm"],
            "outer_width_target_mm": 25,
            "outer_width_model_mm": stats["max_outer_width_x_mm"],
            "notes": "Plan-view reconstruction; side photos would reduce centerline uncertainty.",
        },
    }

    report_path = OUT / "verification_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path = OUT / "verification_report.md"
    md_path.write_text(
        "# Handle reconstruction verification\n\n"
        f"- Hard/soft valid: **{stats['solid_count']} solids**\n"
        f"- Grip span Y: **{stats['grip_span_y_mm']:.2f} mm** (target ~85 mm)\n"
        f"- Outer width X: **{stats['max_outer_width_x_mm']:.2f} mm** (target ~25 mm OD envelope)\n"
        f"- FreeCAD hard STEP: `{fc_hard.get('stdout', fc_hard.get('error', ''))}`\n"
        f"- FreeCAD complete STEP: `{fc_complete.get('stdout', fc_complete.get('error', ''))}`\n",
        encoding="utf-8",
    )

    print(json.dumps(report, indent=2))
    for name, check in export_checks.items():
        if not check.get("non_zero"):
            print(f"FAIL export {name}")
            return 1
    if not all(fc.get("ok") for fc in (fc_hard, fc_soft, fc_complete)):
        print("WARN: FreeCAD check incomplete — see report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
