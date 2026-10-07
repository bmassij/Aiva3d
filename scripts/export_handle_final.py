"""Production exports for handle_test → projects/work/handle_test/exports/."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import cadquery as cq

from projects.work.handle_test.clamshell import build_clamshell
from projects.work.handle_test.model import build, build_assembly_compound
from projects.work.handle_test.parameters import default_parameters
from projects.work.handle_test.validation import validate_export_file, validate_handle_pair

OUT = ROOT / "projects" / "work" / "handle_test" / "exports"


def _export_step(wp: cq.Workplane, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(wp, str(path))


def _export_stl(wp: cq.Workplane, path: Path) -> None:
    cq.exporters.export(wp, str(path), tolerance=0.1, angularTolerance=0.1)


def _export_3mf(wp: cq.Workplane, path: Path) -> None:
    import tempfile

    import trimesh

    with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as tmp:
        stl = Path(tmp.name)
    try:
        cq.exporters.export(wp, str(stl), tolerance=0.1, angularTolerance=0.1)
        mesh = trimesh.load_mesh(str(stl), process=False)
        mesh.export(str(path), file_type="3mf")
    finally:
        stl.unlink(missing_ok=True)


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

    clamshell = build_clamshell(params)
    half_files = {
        "handle_hard_plus.step": OUT / "handle_hard_plus.step",
        "handle_hard_minus.step": OUT / "handle_hard_minus.step",
        "handle_soft_plus.step": OUT / "handle_soft_plus.step",
        "handle_soft_minus.step": OUT / "handle_soft_minus.step",
    }
    _export_step(clamshell.hard_plus, half_files["handle_hard_plus.step"])
    _export_step(clamshell.hard_minus, half_files["handle_hard_minus.step"])
    _export_step(clamshell.soft_plus, half_files["handle_soft_plus.step"])
    _export_step(clamshell.soft_minus, half_files["handle_soft_minus.step"])
    feature_files = {
        "handle_rails_male.step": OUT / "handle_rails_male.step",
        "handle_click_male.step": OUT / "handle_click_male.step",
    }
    _export_step(clamshell.rails_male, feature_files["handle_rails_male.step"])
    _export_step(clamshell.click_male, feature_files["handle_click_male.step"])
    files.update(half_files)
    files.update(feature_files)

    print_dir = OUT / "print"
    print_dir.mkdir(parents=True, exist_ok=True)
    print_stls = {
        "01_hard_plus.stl": clamshell.hard_plus,
        "02_hard_minus.stl": clamshell.hard_minus,
        "03_soft_plus_varishore.stl": clamshell.soft_plus,
        "04_soft_minus_varishore_rails.stl": clamshell.soft_minus,
    }
    for name, wp in print_stls.items():
        dest = print_dir / name
        _export_stl(wp, dest)
        files[name] = dest

    from projects.work.handle_test.full_handle import build_printable_metal_handle

    metal = build_printable_metal_handle()
    metal_files = {
        "handle_metal_loop.step": OUT / "handle_metal_loop.step",
    }
    _export_step(metal, metal_files["handle_metal_loop.step"])
    files.update(metal_files)
    print_stls_metal = {
        "00_bare_metal_handle.stl": metal,
    }
    for name, wp in print_stls_metal.items():
        dest = print_dir / name
        _export_stl(wp, dest)
        files[name] = dest

    from projects.work.handle_test.clamshell import exploded_clamshell

    exploded = exploded_clamshell()
    solids = [wp.val() for wp, *_ in exploded["workpieces"]]
    compound = cq.Compound.makeCompound(solids)
    exploded_path = OUT / "handle_exploded.step"
    cq.exporters.export(compound, str(exploded_path))
    files["handle_exploded.step"] = exploded_path
    fc_dir = OUT / "freecad"
    fc_dir.mkdir(parents=True, exist_ok=True)
    for src in [
        exploded_path,
        OUT / "handle_soft_plus.step",
        OUT / "handle_soft_minus.step",
        OUT / "handle_hard_plus.step",
        OUT / "handle_hard_minus.step",
        OUT / "handle_rails_male.step",
        OUT / "handle_click_male.step",
        OUT / "handle_metal_loop.step",
    ]:
        if src.exists():
            dest = fc_dir / src.name
            dest.write_bytes(src.read_bytes())
            files[f"freecad/{src.name}"] = dest

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "validation": stats,
        "exports": {k: validate_export_file(v) for k, v in files.items()},
    }
    (OUT / "export_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not stats.get("all_checks_pass"):
        print("WARN: one or more design checks out of tolerance")
    for v in files.values():
        if not v.exists() or v.stat().st_size == 0:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
