"""Reusable primitive operations (mm)."""

from __future__ import annotations

import cadquery as cq


def rounded_box(
    length: float,
    width: float,
    height: float,
    corner_radius: float,
) -> cq.Workplane:
    """Rectangular block with vertical edges filleted on the top face perimeter."""
    wp = cq.Workplane("XY").box(length, width, height)
    if corner_radius > 0:
        wp = wp.edges("|Z").fillet(corner_radius)
    return wp


def mounting_holes(
    workpiece: cq.Workplane,
    hole_diameter: float,
    positions: list[tuple[float, float]],
    depth: float | None = None,
) -> cq.Workplane:
    """Cut cylindrical holes at (x, y) positions on the current workplane."""
    result = workpiece
    for x, y in positions:
        result = (
            result.faces(">Z")
            .workplane(centerOption="CenterOfMass")
            .center(x, y)
            .hole(hole_diameter, depth=depth)
        )
    return result
