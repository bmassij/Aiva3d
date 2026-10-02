"""Parametric L-bracket template (not a final design)."""

from __future__ import annotations

import cadquery as cq

from cad.utilities.validation import assert_valid_solid


def build_bracket(
    leg_a_length: float = 60.0,
    leg_b_length: float = 50.0,
    width: float = 30.0,
    thickness: float = 4.0,
    hole_diameter: float = 4.2,
    hole_inset: float = 10.0,
) -> cq.Workplane:
    profile = cq.Workplane("XZ").polyline(
        [(0, 0), (leg_a_length, 0), (leg_a_length, thickness), (thickness, thickness), (thickness, leg_b_length), (0, leg_b_length)]
    ).close()
    bracket = profile.extrude(width).translate((-width / 2, 0, 0))

    for z in (hole_inset, leg_b_length - hole_inset):
        bracket = (
            bracket.faces(">Y")
            .workplane(centerOption="CenterOfMass")
            .center(0, z)
            .hole(hole_diameter)
        )
    bracket = (
        bracket.faces(">X")
        .workplane(centerOption="CenterOfMass")
        .center(0, hole_inset)
        .hole(hole_diameter)
    )
    assert_valid_solid(bracket, "bracket")
    return bracket
