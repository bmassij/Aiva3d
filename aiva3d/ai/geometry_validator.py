"""Validate B-rep metrics against a CAD specification."""

from __future__ import annotations

from typing import Dict, Optional

from aiva3d.ai.types import CadSpecification, GeometryValidationResult


def validate_geometry_against_spec(
    metrics: GeometryValidationResult,
    spec: CadSpecification,
    *,
    bbox_tolerance_mm: float = 2.0,
    require_single_solid: bool = True,
) -> GeometryValidationResult:
    errors = list(metrics.errors)
    warnings = list(metrics.warnings)

    if not metrics.valid:
        return GeometryValidationResult(
            valid=False,
            solid_count=metrics.solid_count,
            bbox=metrics.bbox,
            volume=metrics.volume,
            center_of_mass=metrics.center_of_mass,
            errors=errors or ["Execution did not produce valid geometry."],
            warnings=warnings,
        )

    if require_single_solid and metrics.solid_count != 1:
        errors.append(
            f"Expected exactly one solid, got solid_count={metrics.solid_count}."
        )

    for key, expected in spec.dimensions.items():
        actual = _dimension_from_bbox(key, metrics.bbox)
        if actual is None:
            warnings.append(f"No bbox mapping for dimension key {key!r}.")
            continue
        if abs(actual - expected) > bbox_tolerance_mm:
            errors.append(
                f"Dimension {key}: expected ~{expected} mm, measured ~{actual:.2f} mm "
                f"(tolerance {bbox_tolerance_mm} mm)."
            )

    return GeometryValidationResult(
        valid=len(errors) == 0,
        solid_count=metrics.solid_count,
        bbox=metrics.bbox,
        volume=metrics.volume,
        center_of_mass=metrics.center_of_mass,
        errors=errors,
        warnings=warnings,
    )


def _dimension_from_bbox(key: str, bbox: Dict[str, float]) -> Optional[float]:
    k = key.lower()
    if k in ("x", "width", "diameter", "od", "outer_diameter"):
        return bbox.get("x")
    if k in ("y", "depth", "length", "height"):
        return bbox.get("y")
    if k in ("z", "thickness", "height_z"):
        return bbox.get("z")
    if k.endswith("_mm"):
        return _dimension_from_bbox(k.replace("_mm", ""), bbox)
    return None
