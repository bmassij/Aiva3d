"""Parametric hollow enclosure (shell) template."""

from __future__ import annotations

import cadquery as cq

from cad.utilities.validation import assert_valid_solid


def build_enclosure(
    length: float = 100.0,
    width: float = 50.0,
    height: float = 20.0,
    wall: float = 3.0,
    corner_radius: float = 2.0,
) -> cq.Workplane:
    outer = cq.Workplane("XY").box(length, width, height)
    if corner_radius > 0:
        outer = outer.edges("|Z").fillet(corner_radius)
    inner = (
        cq.Workplane("XY")
        .box(length - 2 * wall, width - 2 * wall, height - wall)
        .translate((0, 0, wall / 2))
    )
    enclosure = outer.cut(inner)
    assert_valid_solid(enclosure, "enclosure")
    return enclosure
