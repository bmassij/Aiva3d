"""Build FreeCAD document (reference + production) via Aiva3D integration layer."""

from __future__ import annotations

import shutil
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from aiva3d.freecad.bridge import FreeCADConnection
from aiva3d.freecad.cmd_runner import _run_script, detect_freecad_cmd
from aiva3d.freecad.document_builder import build_sync_payload
from aiva3d.freecad.fcstd_view import ensure_visible_camera
from projects.work.handle_test.parameters import default_parameters

EXPORTS = ROOT / "projects" / "work" / "handle_test" / "exports"
FCSTD = EXPORTS / "handle_assembly.FCStd"
METAL_FCSTD = EXPORTS / "handle_metal.FCStd"
ZICHTBAAR = EXPORTS / "handle_zichtbaar.FCStd"


def _copy_named_steps(payload: dict) -> None:
    mapping = {
        "metal_loop_step": "handle_metal_loop.step",
        "hard_plus_step": "handle_hard_plus.step",
        "hard_minus_step": "handle_hard_minus.step",
        "soft_plus_step": "handle_soft_plus.step",
        "soft_minus_step": "handle_soft_minus.step",
        "rails_step": "handle_rails_male.step",
        "click_step": "handle_click_male.step",
    }
    fc_dir = EXPORTS / "freecad"
    fc_dir.mkdir(parents=True, exist_ok=True)
    for key, name in mapping.items():
        src = Path(payload["steps"][key])
        if not src.exists():
            continue
        dest = EXPORTS / name
        if src.resolve() != dest.resolve():
            dest.write_bytes(src.read_bytes())
        (fc_dir / name).write_bytes(src.read_bytes())


def _write_metal_fcstd(payload: dict) -> bool:
    exe = detect_freecad_cmd()
    if exe is None:
        print("FreeCADCmd not found; STEP files are still in exports/freecad/")
        return False
    loop = Path(payload["steps"]["metal_loop_step"]).as_posix()
    out = METAL_FCSTD.as_posix()
    script = textwrap.dedent(
        f"""
import FreeCAD as App
import Part
doc = App.newDocument("ijzeren_handvat")
shape = Part.read(r"{loop}")
solids = shape.Solids
if solids:
    fused = solids[0]
    for extra in solids[1:]:
        fused = fused.fuse(extra)
    try:
        fused = fused.removeSplitter()
    except Exception:
        pass
    shape = fused
obj = doc.addObject("Part::Feature", "IJzerenHandvat")
obj.Shape = shape
obj.Label = "IJzeren handvat (1 stuk)"
try:
    obj.ViewObject.ShapeColor = (0.45, 0.47, 0.50)
    obj.ViewObject.Visibility = True
except Exception:
    pass
doc.recompute()
doc.saveAs(r"{out}")
print("OK metal solids", len(shape.Solids) if hasattr(shape, "Solids") else 1)
"""
    )
    code, out_s, err = _run_script(exe, script, timeout=180.0)
    if code != 0 or not METAL_FCSTD.exists():
        print(err or out_s)
        return False
    ensure_visible_camera(METAL_FCSTD)
    shutil.copy2(METAL_FCSTD, ZICHTBAAR)
    shutil.copy2(METAL_FCSTD, EXPORTS / "ijzeren_handvat.FCStd")
    print("Wrote", METAL_FCSTD)
    print("Wrote", ZICHTBAAR)
    return True


def main() -> int:
    EXPORTS.mkdir(parents=True, exist_ok=True)
    payload = build_sync_payload(default_parameters(), EXPORTS)
    _copy_named_steps(payload)
    metal_ok = _write_metal_fcstd(payload)
    conn = FreeCADConnection()
    resp = conn.connect()
    if not resp.success:
        print(resp.error or resp.message)
        return 0 if metal_ok else 1
    sync = conn.sync_model(default_parameters(), FCSTD, work_dir=EXPORTS)
    print(sync.message)
    if sync.error:
        print(sync.error)
    if not sync.success:
        return 0 if metal_ok else 1
    verify = conn.verify_saved()
    print("Objects:", verify.objects)
    if FCSTD.exists():
        shutil.copy2(FCSTD, EXPORTS / "handle_greep.FCStd")
        print("Wrote", EXPORTS / "handle_greep.FCStd")
    return 0 if (verify.success and metal_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
