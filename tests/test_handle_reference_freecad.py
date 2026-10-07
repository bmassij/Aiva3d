"""Reference handle reconstruction and FreeCAD integration tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from aiva3d.freecad.bridge import FreeCADConnection
from aiva3d.freecad.cmd_runner import detect_freecad_cmd, verify_fcstd_objects
from aiva3d.freecad.document_builder import build_sync_payload
from projects.work.handle_test.design_constants import (
    GRIP_LENGTH_MM,
    GRIP_OUTER_DIAMETER_MM,
    HARD_CORE_DIAMETER_MM,
)
from projects.work.handle_test.model import build
from projects.work.handle_test.parameters import default_parameters
from projects.work.handle_test.reference_dimensions import Confidence, load_reference_dimensions
from projects.work.handle_test.reference_geometry import build_original_metal_handle, reference_metadata
from projects.work.handle_test.validation import (
    validate_grip_position_on_reference_handle,
    validate_reference_handle,
)


def test_reference_dimensions_documented():
    dims = load_reference_dimensions()
    names = {r.name for r in dims.records}
    assert "metal_loop_plan_width_mm" in names
    assert any(r.confidence == Confidence.UNKNOWN for r in dims.records)
    assert dims.unknown_limitations


def test_reference_geometry_valid():
    params = default_parameters()
    ref = build_original_metal_handle(params.centerline_points_mm)
    stats = validate_reference_handle(ref)
    assert stats["reference_volume_mm3"] > 0
    assert stats["all_checks_pass"]


def test_grip_position_on_reference():
    params = default_parameters()
    hard, soft = build(params)
    ref = build_original_metal_handle(params.centerline_points_mm)
    pos = validate_grip_position_on_reference_handle(hard, params, ref)
    assert pos["name"] == "GRIP_POSITION_ON_REFERENCE_HANDLE"
    assert pos["pass"]


def test_sync_payload_paths_exist(tmp_path):
    params = default_parameters()
    payload = build_sync_payload(params, tmp_path)
    for key in ("reference_step", "hard_step", "soft_step", "metal_loop_step"):
        p = Path(payload["steps"][key])
        assert p.exists() and p.stat().st_size > 0
    meta = payload["metadata"]
    assert meta["GripLength"] == GRIP_LENGTH_MM
    assert meta["GripOuterDiameter"] == GRIP_OUTER_DIAMETER_MM
    assert meta["HardCoreDiameter"] == HARD_CORE_DIAMETER_MM


def test_reference_metadata_role():
    meta = reference_metadata()
    assert meta["role"] == "reference_only"


def test_freecad_cmd_sync_if_available(tmp_path):
    if detect_freecad_cmd() is None:
        return
    params = default_parameters()
    conn = FreeCADConnection()
    conn.connect()
    fcstd = tmp_path / "test_handle.FCStd"
    resp = conn.sync_model(params, fcstd, work_dir=tmp_path / "steps")
    assert resp.success, resp.error or resp.message
    verify = verify_fcstd_objects(fcstd)
    assert verify.success
