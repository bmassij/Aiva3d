"""Geometry validation helpers."""

from __future__ import annotations

import cadquery as cq


def assert_valid_solid(workpiece: cq.Workplane, label: str = "model") -> None:
    """Raise if the workpiece does not contain a valid solid."""
    shape = workpiece.val()
    if shape is None:
        raise ValueError(f"{label}: no solid on workplane")
    if not shape.isValid():
        raise ValueError(f"{label}: invalid solid (OpenCascade validation failed)")


def solid_volume(workpiece: cq.Workplane) -> float:
    """Return solid volume in mm³ (CadQuery default unit is mm)."""
    assert_valid_solid(workpiece)
    return float(workpiece.val().Volume())
