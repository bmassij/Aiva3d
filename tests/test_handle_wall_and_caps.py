"""Parameter radii, soft wall thickness, and perpendicular end caps."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.STEPControl import STEPControl_Reader

from aiva3d.freecad.cmd_runner import detect_freecad_cmd, verify_fcstd_objects
from aiva3d.freecad.document_builder import build_sync_payload
from projects.work.handle_test.design_constants import (
    GRIP_LENGTH_MM,
    GRIP_OUTER_DIAMETER_MM,
    HARD_CORE_DIAMETER_MM,
    SOFT_INNER_RADIUS_MM,
    SOFT_OUTER_RADIUS_MM,
    SOFT_WALL_NOMINAL_MM,
)
from projects.work.handle_test.model import build
from projects.work.handle_test.parameters import default_parameters
from projects.work.handle_test.validation import (
    validate_end_cap_orientation,
    validate_grip_position_on_reference_handle,
    validate_handle_pair,
    validate_parameter_radii,
)
from cad.utilities.validation import solid_volume


def test_parameter_radii_and_wall():
    params = default_parameters()
    stats = validate_parameter_radii(params)
    assert stats["all_checks_pass"]
    assert abs(params.core_radius_mm - HARD_CORE_DIAMETER_MM / 2) < 0.01
    assert abs(params.soft_inner_radius_mm - SOFT_INNER_RADIUS_MM) < 0.01
    assert abs(params.outer_radius_mm - SOFT_OUTER_RADIUS_MM) < 0.01
    assert abs(params.soft_wall_thickness_mm - SOFT_WALL_NOMINAL_MM) < 0.01


def test_end_caps_perpendicular():
    params = default_parameters()
    hard, _ = build(params)
    cap = validate_end_cap_orientation(hard, params)
    assert cap["pass"], cap


def test_handle_pair_includes_caps_and_wall():
    params = default_parameters()
    hard, soft = build(params)
    stats = validate_handle_pair(hard, soft, params)
    assert stats["all_checks_pass"]
    assert stats["end_cap_check"]["pass"]


def test_step_round_trip_volume():
    params = default_parameters()
    hard, soft = build(params)
    v_live = solid_volume(hard)
    with tempfile.TemporaryDirectory() as td:
        step = Path(td) / "hard.step"
        import cadquery as cq

        cq.exporters.export(hard, str(step))
        reader = STEPControl_Reader()
        reader.ReadFile(str(step))
        reader.TransferRoots()
        sh = reader.OneShape()
        props = GProp_GProps()
        BRepGProp.VolumeProperties_s(sh, props)
        assert abs(props.Mass() - v_live) < 5.0


def test_grip_placement_after_cap_trim():
    params = default_parameters()
    hard, soft = build(params)
    ref = None
    from projects.work.handle_test.reference_geometry import build_original_metal_handle

    ref = build_original_metal_handle(params.centerline_points_mm)
    pos = validate_grip_position_on_reference_handle(hard, params, ref)
    assert pos["pass"]


def test_freecad_sync_if_available(tmp_path):
    if detect_freecad_cmd() is None:
        return
    params = default_parameters()
    payload = build_sync_payload(params, work_dir=tmp_path / "fc")
    assert Path(payload["steps"]["hard_step"]).exists()
    from aiva3d.freecad.bridge import FreeCADConnection

    conn = FreeCADConnection()
    conn.connect()
    fcstd = tmp_path / "handle.FCStd"
    resp = conn.sync_model(params, fcstd, work_dir=tmp_path / "fc2")
    assert resp.success, resp.error or resp.message
    assert verify_fcstd_objects(fcstd).success


def test_authoritative_envelope_unchanged():
    params = default_parameters()
    hard, soft = build(params)
    bb_h = hard.val().BoundingBox()
    bb_s = soft.val().BoundingBox()
    ys = [p[1] for p in params.centerline_points_mm]
    assert abs((max(ys) - min(ys)) - GRIP_LENGTH_MM) <= 2.5
    assert abs((bb_h.zmax - bb_h.zmin) - HARD_CORE_DIAMETER_MM) <= 1.0
    assert abs((bb_s.zmax - bb_s.zmin) - GRIP_OUTER_DIAMETER_MM) <= 1.0
