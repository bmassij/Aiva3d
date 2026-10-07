"""Build sync payloads (STEP paths + metadata) for FreeCAD."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Dict

import cadquery as cq

from projects.work.handle_test.design_constants import (
    GRID_SQUARE_MM,
    GRIP_LENGTH_MM,
    GRIP_OUTER_DIAMETER_MM,
    HARD_CORE_DIAMETER_MM,
    HARD_SOFT_CLEARANCE_MM,
    SOFT_WALL_NOMINAL_MM,
)
from projects.work.handle_test.measurements_loader import centerline_metadata, load_measurements_doc
from projects.work.handle_test.clamshell import build_clamshell
from projects.work.handle_test.materials import (
    CLICK_HARD,
    HARD_PRINT,
    MATERIALS,
    METAL_EXISTING,
    SOFT_PRINT,
    hex_to_rgb01,
)
from projects.work.handle_test.full_handle import build_printable_metal_handle
from projects.work.handle_test.model import build
from projects.work.handle_test.parameters import HandleParameters
from projects.work.handle_test.reference_geometry import build_metal_rod_context, reference_metadata


def _export_step(wp: cq.Workplane, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(wp, str(path))


def build_sync_payload(
    params: HandleParameters,
    work_dir: Path | None = None,
) -> Dict[str, Any]:
    """
    Export reference + production STEP files and return paths for the FreeCAD bridge.
    """
    directory = work_dir or Path(tempfile.mkdtemp(prefix="aiva3d_fc_"))
    directory.mkdir(parents=True, exist_ok=True)

    hard, soft = build(params)
    reference = build_metal_rod_context(params)
    clamshell = build_clamshell(params)

    paths = {
        "reference_step": str(directory / "metal_rod_context.step"),
        "hard_step": str(directory / "hard_core.step"),
        "soft_step": str(directory / "soft_grip.step"),
        "hard_plus_step": str(directory / "hard_plus.step"),
        "hard_minus_step": str(directory / "hard_minus.step"),
        "soft_plus_step": str(directory / "soft_plus.step"),
        "soft_minus_step": str(directory / "soft_minus.step"),
        "rails_step": str(directory / "rails_male.step"),
        "click_step": str(directory / "click_latch.step"),
        "metal_loop_step": str(directory / "metal_loop.step"),
    }
    _export_step(reference, Path(paths["reference_step"]))
    _export_step(hard, Path(paths["hard_step"]))
    _export_step(soft, Path(paths["soft_step"]))
    _export_step(clamshell.hard_plus, Path(paths["hard_plus_step"]))
    _export_step(clamshell.hard_minus, Path(paths["hard_minus_step"]))
    _export_step(clamshell.soft_plus, Path(paths["soft_plus_step"]))
    _export_step(clamshell.soft_minus, Path(paths["soft_minus_step"]))
    _export_step(clamshell.rails_male, Path(paths["rails_step"]))
    _export_step(clamshell.click_male, Path(paths["click_step"]))
    metal = build_printable_metal_handle()
    _export_step(metal, Path(paths["metal_loop_step"]))

    doc = load_measurements_doc()
    meta = {
        "source": "Photographic reconstruction",
        "grid": f"{GRID_SQUARE_MM} mm/square",
        "GripLength": GRIP_LENGTH_MM,
        "GripOuterDiameter": GRIP_OUTER_DIAMETER_MM,
        "HardCoreDiameter": HARD_CORE_DIAMETER_MM,
        "SoftWallNominal": SOFT_WALL_NOMINAL_MM,
        "Clearance": HARD_SOFT_CLEARANCE_MM,
        "Centerline": params.centerline_points_mm,
        "CenterlineNotes": centerline_metadata(doc),
        "ReferenceMetal": {
            **reference_metadata(),
            "preview_role": "metal_rod_under_mesh_only",
            "full_d_loop": "see build_original_metal_handle for lab reconstruction",
        },
        "ProductionPart": {"HardCore": True, "SoftGrip": True, "Clamshell": True, "ClickRails": True},
        "Materials": {
            key: {
                "label": spec["label"],
                "color": spec["color"],
                "rgb01": list(hex_to_rgb01(spec["color"])),
                "role": spec["role"],
            }
            for key, spec in MATERIALS.items()
        },
        "MaterialColors": {
            "OriginalMetalHandle": list(hex_to_rgb01(METAL_EXISTING["color"])),
            "HardCore": list(hex_to_rgb01(HARD_PRINT["color"])),
            "SoftGrip": list(hex_to_rgb01(SOFT_PRINT["color"])),
            "HardPlus": list(hex_to_rgb01(HARD_PRINT["color"])),
            "HardMinus": list(hex_to_rgb01(HARD_PRINT["color"])),
            "SoftPlus": list(hex_to_rgb01(SOFT_PRINT["color"])),
            "SoftMinus": list(hex_to_rgb01(SOFT_PRINT["color"])),
            "RailsMale": list(hex_to_rgb01(CLICK_HARD["color"])),
            "ClickLatch": list(hex_to_rgb01("#e53e3e")),
            "MetalLoop": list(hex_to_rgb01("#4a5568")),
        },
    }
    meta_path = directory / "aiva3d_metadata.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return {
        "work_dir": str(directory),
        "steps": paths,
        "metadata_path": str(meta_path),
        "metadata": meta,
        "parameters": params.summary(),
    }
