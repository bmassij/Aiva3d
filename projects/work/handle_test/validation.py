"""Handle-specific validation and verification metrics."""

from __future__ import annotations

from pathlib import Path
from typing import Any, List

import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Plane
from OCP.TopAbs import TopAbs_FACE
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS

from cad.utilities.validation import assert_valid_solid, solid_volume
from projects.work.handle_test.design_constants import (
    GRIP_LENGTH_MM,
    GRIP_OUTER_DIAMETER_MM,
    HARD_CORE_DIAMETER_MM,
    HARD_SOFT_CLEARANCE_MM,
    SOFT_INNER_RADIUS_MM,
    SOFT_OUTER_RADIUS_MM,
    SOFT_WALL_NOMINAL_MM,
    TOL_CAP_NORMAL_DOT,
    TOL_DIAMETER_MM,
    TOL_LENGTH_MM,
    TOL_WALL_MM,
)
from projects.work.handle_test.model import path_end_tangents_for_validation
from projects.work.handle_test.parameters import HandleParameters
from projects.work.handle_test.measurements_loader import load_measurements_doc
from projects.work.handle_test.reference_dimensions import load_reference_dimensions


def bounding_box_mm(workpiece: cq.Workplane) -> dict[str, float]:
    bb = workpiece.val().BoundingBox()
    return {
        "xmin": float(bb.xmin),
        "xmax": float(bb.xmax),
        "ymin": float(bb.ymin),
        "ymax": float(bb.ymax),
        "zmin": float(bb.zmin),
        "zmax": float(bb.zmax),
        "size_x": float(bb.xmax - bb.xmin),
        "size_y": float(bb.ymax - bb.ymin),
        "size_z": float(bb.zmax - bb.zmin),
    }


def _check(
    name: str,
    expected: float,
    actual: float,
    tolerance: float,
    source: str,
) -> dict[str, Any]:
    delta = abs(actual - expected)
    return {
        "name": name,
        "expected": expected,
        "actual": round(actual, 3),
        "tolerance": tolerance,
        "delta": round(delta, 3),
        "pass": delta <= tolerance,
        "source": source,
    }


def validate_parameter_radii(params: HandleParameters) -> dict[str, Any]:
    params.validate_relationships()
    checks: List[dict[str, Any]] = [
        _check(
            "hard_core_radius_mm",
            HARD_CORE_DIAMETER_MM / 2.0,
            params.core_radius_mm,
            0.05,
            "reference_measurements.json",
        ),
        _check(
            "soft_inner_radius_mm",
            SOFT_INNER_RADIUS_MM,
            params.soft_inner_radius_mm,
            0.05,
            "core_radius + clearance",
        ),
        _check(
            "soft_outer_radius_mm",
            SOFT_OUTER_RADIUS_MM,
            params.outer_radius_mm,
            0.05,
            "grip OD / 2",
        ),
        _check(
            "soft_wall_thickness_mm",
            SOFT_WALL_NOMINAL_MM,
            params.soft_wall_thickness_mm,
            TOL_WALL_MM,
            "outer_radius - soft_inner_radius",
        ),
        _check(
            "hard_soft_clearance_mm",
            HARD_SOFT_CLEARANCE_MM,
            params.clearance_mm,
            0.05,
            "design_constants.HARD_SOFT_CLEARANCE_MM",
        ),
    ]
    return {"design_checks": checks, "all_checks_pass": all(c["pass"] for c in checks)}


def _planar_face_normals(shape) -> List[tuple[float, float, float, float, float, float]]:
    out: List[tuple[float, float, float, float, float, float]] = []
    exp = TopExp_Explorer(shape, TopAbs_FACE)
    while exp.More():
        surf = BRepAdaptor_Surface(TopoDS.Face_s(exp.Current()))
        if surf.GetType() == GeomAbs_Plane:
            pln = surf.Plane()
            loc = pln.Location()
            ax = pln.Axis().Direction()
            out.append((loc.X(), loc.Y(), loc.Z(), ax.X(), ax.Y(), ax.Z()))
        exp.Next()
    return out


def validate_end_symmetry(params: HandleParameters) -> dict[str, Any]:
    """Printed grip is a mirror of itself about mid-span (identical ends)."""
    cl = params.centerline_points_mm
    if len(cl) < 3:
        return {"name": "END_SYMMETRY", "pass": False, "reason": "need 3-point arc"}
    x0, y0 = cl[0]
    x1, y1 = cl[-1]
    xm, ym = cl[len(cl) // 2]
    frames = path_end_tangents_for_validation(cl)
    t0 = frames["start"]
    t1 = frames["end"]
    x_match = abs(x0 - x1) <= 0.15
    mid_centered = abs((y0 + y1) / 2.0 - ym) <= 1.0
    tangent_mirror = abs(t0[0] + t1[0]) <= 0.08 and abs(t0[1] - t1[1]) <= 0.08
    return {
        "name": "END_SYMMETRY",
        "pass": x_match and mid_centered and tangent_mirror,
        "end_x_mm": [round(x0, 3), round(x1, 3)],
        "mid_x_mm": round(xm, 3),
        "start_tangent": [round(v, 4) for v in t0],
        "end_tangent": [round(v, 4) for v in t1],
    }


def validate_end_cap_orientation(hard: cq.Workplane, params: HandleParameters) -> dict[str, Any]:
    tangents = path_end_tangents_for_validation(params.centerline_points_mm)
    t0 = tangents["start"]
    t1 = tangents["end"]
    p0 = tangents["start_point"]
    p1 = tangents["end_point"]
    planes = _planar_face_normals(hard.val().wrapped)

    def best_cap_alignment(point: list[float], tangent: list[float]) -> float:
        """End-cap plane normals are parallel to the path tangent (|n·t| → 1)."""
        best = 0.0
        px, py, pz = point
        for lx, ly, lz, nx, ny, nz in planes:
            dist = abs(lx - px) + abs(ly - py) + abs(lz - pz)
            if dist > 36.0:
                continue
            dot = abs(nx * tangent[0] + ny * tangent[1] + nz * tangent[2])
            best = max(best, dot)
        return best

    start_dot = best_cap_alignment(p0, t0)
    end_dot = best_cap_alignment(p1, t1)
    min_align = 1.0 - TOL_CAP_NORMAL_DOT
    passed = start_dot >= min_align and end_dot >= min_align
    return {
        "name": "END_CAP_PERPENDICULAR_TO_PATH",
        "pass": passed,
        "start_cap_abs_n_dot_t": round(start_dot, 4),
        "end_cap_abs_n_dot_t": round(end_dot, 4),
        "min_required_abs_n_dot_t": round(min_align, 4),
    }


def validate_handle_pair(hard: cq.Workplane, soft: cq.Workplane, params: HandleParameters) -> dict[str, Any]:
    assert_valid_solid(hard, "hard_core")
    assert_valid_solid(soft, "soft_outer")
    v_hard = solid_volume(hard)
    v_soft = solid_volume(soft)
    if v_hard <= 0 or v_soft <= 0:
        raise ValueError("volumes must be positive")
    if params.soft_wall_thickness_mm <= 0:
        raise ValueError("soft wall thickness must be positive")

    bb_hard = bounding_box_mm(hard)
    bb_soft = bounding_box_mm(soft)
    cl = params.centerline_points_mm
    grip_y_span = max(p[1] for p in cl) - min(p[1] for p in cl)
    param_stats = validate_parameter_radii(params)

    checks: List[dict[str, Any]] = [
        _check(
            "grip_length_mm",
            GRIP_LENGTH_MM,
            grip_y_span,
            TOL_LENGTH_MM,
            "reference_measurements.json (13 × 10 mm tuinslang span)",
        ),
        _check(
            "hard_core_diameter_mm",
            HARD_CORE_DIAMETER_MM,
            bb_hard["size_z"],
            TOL_DIAMETER_MM,
            "reference_measurements.json photo_grid_counts_verified",
        ),
        _check(
            "soft_outer_envelope_z_mm",
            GRIP_OUTER_DIAMETER_MM,
            bb_soft["size_z"],
            TOL_DIAMETER_MM + 2.0,
            "nominal OD (bbox includes bow; relaxed tol)",
        ),
    ]
    checks.extend(param_stats["design_checks"])
    cap_check = validate_end_cap_orientation(hard, params)
    end_sym = validate_end_symmetry(params)

    return {
        "solid_count": 2,
        "hard_volume_mm3": v_hard,
        "soft_volume_mm3": v_soft,
        "parameter_summary": params.summary(),
        "hard_bbox": bb_hard,
        "soft_bbox": bb_soft,
        "grip_span_y_mm": grip_y_span,
        "max_outer_width_x_mm": bb_soft["size_x"],
        "design_checks": checks,
        "end_cap_check": cap_check,
        "end_symmetry": end_sym,
        "all_checks_pass": all(c["pass"] for c in checks) and cap_check["pass"] and end_sym["pass"],
    }


def validate_grip_position_on_reference_handle(
    hard: cq.Workplane,
    params: HandleParameters,
    reference: cq.Workplane | None = None,
) -> dict[str, Any]:
    """
    GRIP_POSITION_ON_REFERENCE_HANDLE — production grip lies on the reference grip leg (Y span, axis).
    """
    dims = load_reference_dimensions(params.centerline_points_mm)
    cl = dims.grip_centerline_points_mm
    y0 = min(p[1] for p in cl)
    y1 = max(p[1] for p in cl)
    bb_hard = bounding_box_mm(hard)
    grip_y_span = y1 - y0
    overlap = min(bb_hard["ymax"], y1) - max(bb_hard["ymin"], y0)
    y_span_ok = overlap >= GRIP_LENGTH_MM - 35.0
    axis_ok = abs(bb_hard["xmin"]) <= 28.0 and bb_hard["size_x"] <= 52.0
    length_ok = abs(grip_y_span - GRIP_LENGTH_MM) <= 2.5
    ref_ok = True
    if reference is not None:
        try:
            assert_valid_solid(reference, "metal_rod_context")
            ref_vol = solid_volume(reference)
            ref_ok = ref_vol > 0
        except Exception as exc:  # noqa: BLE001
            ref_ok = False
            ref_err = str(exc)
        else:
            ref_err = ""
    else:
        ref_err = ""
    passed = y_span_ok and axis_ok and length_ok and ref_ok
    return {
        "name": "GRIP_POSITION_ON_REFERENCE_HANDLE",
        "pass": passed,
        "grip_centerline_y_mm": [y0, y1],
        "hard_bbox": bb_hard,
        "checks": {
            "y_span_on_leg": y_span_ok,
            "near_grip_leg_axis_x0": axis_ok,
            "grip_length_mm": length_ok,
            "reference_solid_valid": ref_ok,
        },
        "reference_error": ref_err,
    }


def validate_reference_handle(reference: cq.Workplane) -> dict[str, Any]:
    """Reference geometry checks — valid geometry, documented dimensions present."""
    shape = reference.val()
    if shape.ShapeType() == "Compound":
        children = shape.Solids()
        if not children:
            raise ValueError("original_metal_handle: empty compound")
        for i, solid in enumerate(children):
            wp = cq.Workplane().newObject([solid])
            assert_valid_solid(wp, f"original_metal_handle_part_{i}")
    else:
        assert_valid_solid(reference, "original_metal_handle")
    dims = load_reference_dimensions()
    bb = bounding_box_mm(reference)
    loop_w = next((r.value_mm for r in dims.records if r.name == "metal_loop_plan_width_mm"), None)
    loop_h = next((r.value_mm for r in dims.records if r.name == "metal_loop_plan_height_mm"), None)
    doc = load_measurements_doc()
    items = {m["name"]: m for m in doc.get("all_measurements") or []}
    rope_w = items.get("metal_loop_rope_plan_width_mm", {}).get("value_mm")
    if rope_w:
        loop_w = float(rope_w)
    # Plan bbox includes rod radius; compare outer span to loop rope width when available.
    width_tol = 28.0 if rope_w else 35.0
    height_tol = 28.0
    expected_w = float(rope_w) if rope_w else loop_w
    width_ok = expected_w is None or abs(bb["size_x"] - expected_w) <= width_tol
    height_ok = loop_h is None or abs(bb["size_y"] - float(loop_h)) <= height_tol
    return {
        "reference_volume_mm3": solid_volume(reference),
        "bbox": bb,
        "dimension_doc": dims.to_dict(),
        "bbox_vs_measured_loop": {"width_ok": width_ok, "height_ok": height_ok},
        "all_checks_pass": width_ok and height_ok,
    }


def validate_export_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path), "exists": False, "bytes": 0}
    size = path.stat().st_size
    return {"path": str(path), "exists": True, "bytes": size, "non_zero": size > 0}
