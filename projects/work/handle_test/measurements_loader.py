"""Load photo-derived grip dimensions from reference_measurements.json."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, List, Tuple

from projects.work.handle_test.design_constants import (
    GRIP_ANCHOR_Y_MM,
    GRIP_LENGTH_MM,
    HARD_CORE_DIAMETER_MM,
)

PROJECT_DIR = Path(__file__).resolve().parent
MEASUREMENTS_PATH = PROJECT_DIR / "reference_measurements.json"
MM_PER_SQUARE = 10.0

__all__ = [
    "authoritative_grip",
    "centerline_sleeve_shape_mm",
    "centerline_for_cad",
    "centerline_metadata",
    "load_measurements_doc",
    "parameters_from_measurements",
    "right_leg_centerline_full_mm",
]


def load_measurements_doc() -> dict[str, Any]:
    if not MEASUREMENTS_PATH.exists():
        return {}
    return json.loads(MEASUREMENTS_PATH.read_text(encoding="utf-8"))


def authoritative_grip(doc: dict[str, Any]) -> dict[str, Any]:
    """Prefer verified grid-square counts over raw automated spans when present."""
    grip = dict(doc.get("grip") or {})
    verified = doc.get("photo_grid_counts_verified") or {}
    if verified:
        if "grip_length_squares" in verified:
            grip["length_mm"] = float(verified["grip_length_squares"]) * MM_PER_SQUARE
            grip["length_source"] = verified.get("method", "grid_square_count")
            grip["length_confidence"] = verified.get("confidence", "medium")
        if "grip_od_squares" in verified:
            grip["outer_diameter_mm"] = float(verified["grip_od_squares"]) * MM_PER_SQUARE
            grip["od_source"] = verified.get("method", "grid_square_count")
        if "core_diameter_mm" in verified:
            grip["core_diameter_mm"] = float(verified["core_diameter_mm"])
    return grip


def _scaled_sleeve_trace(
    traced: list, length_mm: float
) -> List[Tuple[float, float]]:
    y_end = max(p[1] for p in traced)
    if y_end <= 0:
        return []
    scale = length_mm / y_end
    return [(float(p[0]) * scale, float(p[1]) * scale) for p in traced]


def _grip_anchor_y_mm(doc: dict[str, Any], length_mm: float) -> float:
    grip = doc.get("grip") or {}
    if grip.get("anchor_y_mm") is not None:
        return float(grip["anchor_y_mm"])
    loop = doc.get("metal_loop") or {}
    plan_h = float(loop.get("plan_height_mm") or 0.0)
    if plan_h <= 0:
        items = {m["name"]: m for m in doc.get("all_measurements") or []}
        plan_h = float(items.get("metal_loop_rope_plan_height_mm", {}).get("value_mm") or 0.0)
    if plan_h > length_mm + 5.0:
        return round((plan_h - length_mm) / 2.0, 2)
    return GRIP_ANCHOR_Y_MM


def _loop_ellipse_axes_mm(doc: dict[str, Any]) -> tuple[float, float]:
    """INFERRED D-loop centerline semi-axes from rope-plan bbox minus rod OD."""
    loop = doc.get("metal_loop") or {}
    items = {m["name"]: m for m in doc.get("all_measurements") or []}
    plan_h = float(loop.get("plan_height_mm") or 0.0)
    if plan_h <= 0:
        plan_h = float(items.get("metal_loop_rope_plan_height_mm", {}).get("value_mm") or 168.1)
    plan_w = float(items.get("metal_loop_rope_plan_width_mm", {}).get("value_mm") or 84.9)
    rod = HARD_CORE_DIAMETER_MM
    a = max(18.0, (plan_w - rod) / 2.0)
    b = max(40.0, plan_h / 2.0)
    return a, b


def _ellipse_sleeve_three_point(doc: dict[str, Any], length_mm: float) -> List[Tuple[float, float]]:
    """
    Right-leg D-curve as a 3-point arc (local Y 0 = sleeve bottom).

    X is outward: mid-span is the rightmost point of the oval; ends sit inward.
    """
    a, b = _loop_ellipse_axes_mm(doc)
    anchor = _grip_anchor_y_mm(doc, length_mm)
    y0 = float(anchor)
    y1 = float(anchor + length_mm)
    ym = 0.5 * (y0 + y1)

    def x_from_center(y_world: float) -> float:
        ny = (y_world - b) / b
        ny = max(-0.999, min(0.999, ny))
        return a * math.sqrt(max(0.0, 1.0 - ny * ny))

    def x_outward(y_world: float) -> float:
        """0 at the oval's rightmost point; negative toward the loop interior."""
        return x_from_center(y_world) - a

    # Mirror about mid-span so both printed ends match (same X, mirrored tangent).
    x_end = round(0.5 * (x_outward(y0) + x_outward(y1)), 2)
    x_mid = round(x_outward(ym), 2)
    return [
        (x_end, 0.0),
        (x_mid, round(length_mm / 2.0, 2)),
        (x_end, round(length_mm, 2)),
    ]


def _sleeve_centerline_three_point(doc: dict[str, Any]) -> List[Tuple[float, float]]:
    """Three-point sleeve arc in leg-local Y (0 = bottom of traced sleeve span)."""
    grip = authoritative_grip(doc)
    length_mm = float(grip.get("length_mm") or GRIP_LENGTH_MM)
    return _ellipse_sleeve_three_point(doc, length_mm)


def centerline_sleeve_shape_mm(doc: dict[str, Any] | None = None) -> List[Tuple[float, float]]:
    """Sleeve arc without leg anchor (for extending the full metal loop)."""
    doc = doc or load_measurements_doc()
    return _sleeve_centerline_three_point(doc)


def centerline_for_cad(doc: dict[str, Any]) -> List[Tuple[float, float]]:
    """
    INFERRED centerline for CadQuery sweep (production grip on the right D-leg).

    Same sleeve arc shape, shifted along +Y so the mesh sits mid-leg on the photo (not at loop bottom).
    """
    length_mm = float(authoritative_grip(doc).get("length_mm") or GRIP_LENGTH_MM)
    anchor = _grip_anchor_y_mm(doc, length_mm)
    return [(x, round(y + anchor, 2)) for x, y in _sleeve_centerline_three_point(doc)]


def centerline_metadata(doc: dict[str, Any]) -> dict[str, str]:
    return {
        "method": "three_point_arc_d_leg_ellipse",
        "confidence": "inferred",
        "notes": (
            "Symmetric 3-point D-leg arc (identical end X, mid-span outward). "
            "Printed as two XY-clamshell halves: short sliders drop into L-notches, then click sideways to lock. "
            "Plan-view only; out-of-plane bend unknown."
        ),
    }


def right_leg_centerline_full_mm(
    grip_three_point: List[Tuple[float, float]],
    loop_height_mm: float,
) -> List[Tuple[float, float]]:
    """Same D-leg ellipse as the sleeved grip, spanning the full loop height."""
    if len(grip_three_point) != 3 or loop_height_mm <= 0:
        return list(grip_three_point)
    bottom, mid, top = grip_three_point
    y_grip = float(top[1])
    if y_grip <= 1e-6:
        return list(grip_three_point)
    scale = float(loop_height_mm) / y_grip
    return [
        (round(float(bottom[0]), 2), round(float(bottom[1]), 2)),
        (round(float(mid[0]), 2), round(float(mid[1]) * scale, 2)),
        (round(float(top[0]), 2), round(float(loop_height_mm), 2)),
    ]


def parameters_from_measurements() -> dict[str, Any]:
    doc = load_measurements_doc()
    grip = authoritative_grip(doc)
    length_mm = float(grip.get("length_mm") or 100.0)
    od = float(grip.get("outer_diameter_mm") or 30.0)
    core_d = float(grip.get("core_diameter_mm") or 10.0)
    return {
        "centerline_points_mm": centerline_for_cad(doc),
        "core_radius_mm": core_d / 2.0,
        "outer_radius_mm": od / 2.0,
        "grip_length_mm": length_mm,
        "outer_diameter_mm": od,
        "core_diameter_mm": core_d,
        "measurements_doc": doc,
    }
