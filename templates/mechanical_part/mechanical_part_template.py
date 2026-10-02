"""Generic mechanical part: flanged cylinder with key slot."""

from __future__ import annotations

import cadquery as cq

from cad.utilities.validation import assert_valid_solid


def build_mechanical_part(
    body_diameter: float = 40.0,
    body_height: float = 25.0,
    flange_diameter: float = 55.0,
    flange_thickness: float = 5.0,
    slot_width: float = 8.0,
    slot_depth: float = 12.0,
) -> cq.Workplane:
    part = cq.Workplane("XY").circle(body_diameter / 2).extrude(body_height)
    flange = cq.Workplane("XY").circle(flange_diameter / 2).extrude(flange_thickness)
    part = part.union(flange)
    slot = (
        cq.Workplane("XY")
        .center(0, 0)
        .rect(slot_width, body_diameter)
        .extrude(slot_depth)
    )
    part = part.cut(slot)
    assert_valid_solid(part, "mechanical_part")
    return part
