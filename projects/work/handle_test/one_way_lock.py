"""
One-way snap lock: assemble without glue; cannot pull apart afterwards.

A tapered pawl clicks behind a shoulder. A 2 mm reset pin through a hidden
hole flexes the pawl off the shoulder so the halves can be opened for service.
"""

from __future__ import annotations

import math

import cadquery as cq

from projects.work.handle_test.design_constants import (
    PAWL_CATCH_MM,
    PAWL_CLEARANCE_MM,
    PAWL_HEIGHT_MM,
    PAWL_LENGTH_MM,
    PAWL_WIDTH_MM,
    RESET_PIN_DIAMETER_MM,
)


def _pawl_profile(*, clearance: float, male: bool) -> cq.Workplane:
    """
    Local solid: +X = insertion (into the other half), +Z = proud of the split.
    Male catch lip is taller at the far end so it hooks behind a female shelf.
    """
    length = PAWL_LENGTH_MM + (2.0 * clearance if not male else 0.0)
    width = PAWL_WIDTH_MM + (2.0 * clearance if not male else 0.0)
    height = PAWL_HEIGHT_MM + (clearance if not male else 0.0)
    catch = PAWL_CATCH_MM + (clearance if not male else 0.0)
    stem_h = height - catch
    if male:
        stem = cq.Workplane("XY").box(length - catch, width, stem_h, centered=(False, True, False))
        lip = (
            cq.Workplane("XY")
            .box(catch, width, height, centered=(False, True, False))
            .translate((length - catch, 0.0, 0.0))
        )
        return stem.union(lip)
    tunnel = cq.Workplane("XY").box(length, width, stem_h + clearance, centered=(False, True, False))
    pocket = (
        cq.Workplane("XY")
        .box(catch + 1.2, width + 0.4, height + clearance, centered=(False, True, False))
        .translate((length - catch - 0.4, 0.0, 0.0))
    )
    return tunnel.union(pocket)


def pawl_male() -> cq.Workplane:
    return _pawl_profile(clearance=0.0, male=True)


def pawl_female_cutter() -> cq.Workplane:
    return _pawl_profile(clearance=PAWL_CLEARANCE_MM, male=False)


def reset_pin_cutter() -> cq.Workplane:
    """Pin axis = local Y, through the catch lip (service release)."""
    length = PAWL_LENGTH_MM
    catch = PAWL_CATCH_MM
    height = PAWL_HEIGHT_MM
    d = RESET_PIN_DIAMETER_MM + PAWL_CLEARANCE_MM
    span = PAWL_WIDTH_MM + 12.0
    return (
        cq.Workplane("XZ")
        .transformed(offset=(length - catch * 0.45, 0.0, height * 0.55))
        .circle(d / 2.0)
        .extrude(span / 2.0, both=True)
    )


def _place(local: cq.Workplane, ox: float, oy: float, yaw_deg: float) -> cq.Workplane:
    return local.rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), yaw_deg).translate((ox, oy, 0.0))


def place_lock_set(
    origin_xy: tuple[float, float],
    yaw_deg: float,
    *,
    male: bool,
) -> cq.Workplane:
    """Pawl stands in +Z (clamshell close direction); yaw orients it in the XY plane."""
    ox, oy = origin_xy
    body = pawl_male() if male else pawl_female_cutter()
    body = body.rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), -90.0)
    if not male:
        pin = reset_pin_cutter().rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), -90.0)
        body = body.union(pin)
    return _place(body, ox, oy, yaw_deg)


def union_placed(items: list[cq.Workplane]) -> cq.Workplane:
    fused = items[0]
    for extra in items[1:]:
        fused = fused.union(extra)
    return fused
