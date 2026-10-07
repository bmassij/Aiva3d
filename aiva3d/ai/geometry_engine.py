"""Deterministic conversion from vision landmarks to CAD specifications."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from aiva3d.ai.types import CadSpecification


def pixel_scale_from_grid(*, mm_per_px_x: float, mm_per_px_y: Optional[float] = None) -> Tuple[float, float]:
    """Return (sx, sy) mm per pixel from calibrated grid."""
    sy = mm_per_px_y if mm_per_px_y is not None else mm_per_px_x
    return float(mm_per_px_x), float(sy)


def centerline_pixels_to_mm(
    points_px: Sequence[Tuple[float, float]],
    *,
    origin_px: Tuple[float, float],
    mm_per_px_x: float,
    mm_per_px_y: float,
    y_up: bool = True,
) -> List[Tuple[float, float]]:
    """Convert image (u, v) points to mm coordinates relative to origin."""
    ox, oy = origin_px
    out: List[Tuple[float, float]] = []
    for u, v in points_px:
        mm_x = (u - ox) * mm_per_px_x
        dv = (v - oy) * mm_per_px_y
        mm_y = -dv if y_up else dv
        out.append((round(mm_x, 3), round(mm_y, 3)))
    return out


def landmarks_to_cad_specification(
    vision_payload: Mapping[str, Any],
    *,
    part_description: str,
    extra_constraints: Optional[List[str]] = None,
) -> CadSpecification:
    """
    Build a text specification for the CadQuery model from vision/engine outputs.

    ``vision_payload`` is expected to carry measured values (not hard-coded guesses),
    e.g. from ``reference_measurements.json`` or a future Qwen3-VL JSON schema.
    """
    dimensions: Dict[str, float] = {}
    for key in (
        "grip_length_mm",
        "grip_outer_diameter_mm",
        "tuinslang_span_vertical_mm",
        "inner_diameter_mm",
        "outer_diameter_mm",
        "arc_radius_mm",
        "arc_length_mm",
    ):
        val = vision_payload.get(key)
        if isinstance(val, (int, float)):
            dimensions[key.replace("_mm", "")] = float(val)

    nested = vision_payload.get("dimensions")
    if isinstance(nested, Mapping):
        for k, v in nested.items():
            if isinstance(v, (int, float)):
                dimensions[str(k)] = float(v)

    constraints = list(extra_constraints or [])
    constraints.append(
        "All numeric values above are measured or calculated in Python; do not invent alternate dimensions."
    )
    if vision_payload.get("uncertainty"):
        constraints.append(f"Vision uncertainty: {vision_payload['uncertainty']}")

    return CadSpecification(
        description=part_description,
        units=str(vision_payload.get("units") or "mm"),
        constraints=constraints,
        dimensions=dimensions,
        metadata={"vision_source": vision_payload.get("source", "geometry_engine")},
    )
