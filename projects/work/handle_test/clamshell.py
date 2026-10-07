"""
Two-part clamshell grip: split on the XY plane (Z = 0) around the existing rod.

Lock: short L-notches (inkepingen) with a small slider. Slide the tab into the
slot, then click it one way into the side pocket so it cannot slide back.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import cadquery as cq

from cad.utilities.validation import assert_valid_solid, solid_volume
from projects.work.handle_test.design_constants import (
    EXPLODE_GAP_Z_MM,
    SLIDER_CLEARANCE_MM,
    SLIDER_CLICK_MM,
    SLIDER_HEIGHT_MM,
    SLIDER_LENGTH_MM,
    SLIDER_T_STATIONS,
    SLIDER_WIDTH_MM,
)
from projects.work.handle_test.materials import CLICK_HARD, HARD_PRINT, SOFT_PRINT
from projects.work.handle_test.model import (
    build_hard_core,
    build_soft_outer_shell,
    sample_path_frame,
)
from projects.work.handle_test.one_way_lock import place_lock_set, union_placed
from projects.work.handle_test.parameters import HandleParameters, default_parameters


@dataclass(frozen=True)
class ClamshellParts:
    hard_plus: cq.Workplane
    hard_minus: cq.Workplane
    soft_plus: cq.Workplane
    soft_minus: cq.Workplane
    rails_male: cq.Workplane
    rails_female_cutter: cq.Workplane
    click_male: cq.Workplane
    click_female_cutter: cq.Workplane


def _inplane_normal(tangent: tuple[float, float, float]) -> tuple[float, float]:
    tx, ty, _ = tangent
    nlen = math.hypot(-ty, tx)
    if nlen <= 1e-9:
        return (1.0, 0.0)
    return (-ty / nlen, tx / nlen)


def _place(local: cq.Workplane, ox: float, oy: float, tx: float, ty: float) -> cq.Workplane:
    deg = math.degrees(math.atan2(ty, tx))
    return local.rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), deg).translate((ox, oy, 0.0))


def _wall_mid(params: HandleParameters) -> float:
    return 0.5 * (params.inner_cut_radius_mm + params.outer_radius_mm)


def _stations(params: HandleParameters) -> list[tuple[float, float, float, float, float, float]]:
    """(ox, oy, tx, ty, nx, ny) for each slider: two path stations × both wall sides."""
    mid = _wall_mid(params)
    out: list[tuple[float, float, float, float, float, float]] = []
    for t in SLIDER_T_STATIONS:
        origin, tangent = sample_path_frame(params.centerline_points_mm, float(t))
        nx, ny = _inplane_normal(tangent)
        tx, ty = float(tangent[0]), float(tangent[1])
        for sign in (-1.0, 1.0):
            ox = origin[0] + nx * sign * mid
            oy = origin[1] + ny * sign * mid
            out.append((ox, oy, tx, ty, nx * sign, ny * sign))
    return out


def _entry_slot(*, clearance: float) -> cq.Workplane:
    length = SLIDER_LENGTH_MM + 2.0 * clearance
    width = SLIDER_WIDTH_MM + 2.0 * clearance
    height = SLIDER_HEIGHT_MM + clearance
    return cq.Workplane("XY").box(length, width, height, centered=(False, True, False))


def _side_pocket(*, clearance: float) -> cq.Workplane:
    length = SLIDER_LENGTH_MM + 2.0 * clearance
    width = SLIDER_WIDTH_MM + 2.0 * clearance
    height = SLIDER_HEIGHT_MM + clearance
    click = SLIDER_CLICK_MM + clearance
    pocket_len = length * 0.55
    return (
        cq.Workplane("XY")
        .box(pocket_len, click + width * 0.25, height, centered=(False, False, False))
        .translate((length - pocket_len, width / 2.0 - width * 0.12, 0.0))
    )


def _neck(*, clearance: float) -> cq.Workplane:
    length = SLIDER_LENGTH_MM + 2.0 * clearance
    width = (SLIDER_WIDTH_MM + 2.0 * clearance) * 0.72
    height = SLIDER_HEIGHT_MM + clearance
    pocket_len = length * 0.55
    neck_len = length * 0.42
    return (
        cq.Workplane("XY")
        .box(neck_len, width, height, centered=(False, True, False))
        .translate((length - pocket_len - neck_len * 0.45, 0.0, 0.0))
    )


def _union_placed(locals_fn, params: HandleParameters) -> cq.Workplane:
    solids: list[cq.Workplane] = []
    for ox, oy, tx, ty, _nx, _ny in _stations(params):
        solids.append(_place(locals_fn(), ox, oy, tx, ty))
    fused = solids[0]
    for extra in solids[1:]:
        fused = fused.union(extra)
    return fused


def _male_sliders(params: HandleParameters) -> cq.Workplane:
    return _union_placed(lambda: _neck(clearance=0.0), params)


def _male_hooks(params: HandleParameters) -> cq.Workplane:
    return _union_placed(lambda: _side_pocket(clearance=0.0), params)


def _female_notches(params: HandleParameters) -> cq.Workplane:
    def local() -> cq.Workplane:
        return _entry_slot(clearance=SLIDER_CLEARANCE_MM).union(
            _side_pocket(clearance=SLIDER_CLEARANCE_MM)
        )

    return _union_placed(local, params)


def _split_z(workpiece: cq.Workplane, keep_positive: bool) -> cq.Workplane:
    bb = workpiece.val().BoundingBox()
    cx = 0.5 * (bb.xmin + bb.xmax)
    cy = 0.5 * (bb.ymin + bb.ymax)
    sx = max(bb.xmax - bb.xmin, 10.0) + 80.0
    sy = max(bb.ymax - bb.ymin, 10.0) + 80.0
    z_shift = 100.0 if keep_positive else -100.0
    box = cq.Workplane("XY").box(sx, sy, 200.0).translate((cx, cy, z_shift))
    return workpiece.intersect(box)


def build_clamshell(params: HandleParameters | None = None) -> ClamshellParts:
    """Hard + soft halves; L-notch aligns, one-way pawls lock (reset pin to open)."""
    params = params or default_parameters()
    hard = build_hard_core(params)
    soft = build_soft_outer_shell(params)
    sliders = _male_sliders(params)
    hooks = _male_hooks(params)
    notches = _female_notches(params)
    lock_stations = [
        ((ox, oy), math.degrees(math.atan2(ty, tx)))
        for ox, oy, tx, ty, _nx, _ny in _stations(params)
    ]
    pawls = union_placed([place_lock_set(xy, yaw, male=True) for xy, yaw in lock_stations])
    pockets = union_placed([place_lock_set(xy, yaw, male=False) for xy, yaw in lock_stations])

    hard_plus = _split_z(hard, True)
    hard_minus = _split_z(hard, False)
    soft_plus = _split_z(soft, True).cut(notches).cut(pockets)
    soft_minus = _split_z(soft, False).union(sliders).union(hooks).union(pawls)

    assert_valid_solid(hard_plus, "hard_plus")
    assert_valid_solid(hard_minus, "hard_minus")
    assert_valid_solid(soft_plus, "soft_plus")
    assert_valid_solid(soft_minus, "soft_minus")
    assert_valid_solid(sliders, "sliders")
    assert_valid_solid(pawls, "pawls")
    return ClamshellParts(
        hard_plus=hard_plus,
        hard_minus=hard_minus,
        soft_plus=soft_plus,
        soft_minus=soft_minus,
        rails_male=sliders,
        rails_female_cutter=notches,
        click_male=pawls,
        click_female_cutter=pockets,
    )


def validate_clamshell(parts: ClamshellParts, params: HandleParameters) -> dict:
    vols = {
        "hard_plus": solid_volume(parts.hard_plus),
        "hard_minus": solid_volume(parts.hard_minus),
        "soft_plus": solid_volume(parts.soft_plus),
        "soft_minus": solid_volume(parts.soft_minus),
        "slider": solid_volume(parts.rails_male),
        "hook": solid_volume(parts.click_male),
    }
    hard_sym = abs(vols["hard_plus"] - vols["hard_minus"]) / max(vols["hard_plus"], 1e-6)
    rails_ok = vols["soft_minus"] > vols["soft_plus"]
    hook_visible = vols["hook"] >= 40.0
    return {
        "volumes_mm3": vols,
        "hard_volume_rel_delta": round(hard_sym, 4),
        "hard_halves_symmetric": hard_sym <= 0.04,
        "rails_on_minus_half": rails_ok,
        "hook_visible": hook_visible,
        "all_checks_pass": hard_sym <= 0.04
        and rails_ok
        and hook_visible
        and all(v > 0 for v in vols.values()),
        "assembly": (
            "Press halves together: sliders align, one-way pawls click behind a shoulder. "
            "No glue. It will not pull apart. Service only: 2 mm reset pin in the side holes."
        ),
        "parameters": params.summary(),
    }


def click_sphere_centers_mm(params: HandleParameters) -> list[tuple[float, float, float]]:
    """Locked hook pocket centres (for drawing labels)."""
    length = SLIDER_LENGTH_MM
    width = SLIDER_WIDTH_MM
    click = SLIDER_CLICK_MM
    height = SLIDER_HEIGHT_MM
    pocket_len = length * 0.55
    local_x = length - pocket_len * 0.5
    local_y = width / 2.0 + click * 0.45
    out: list[tuple[float, float, float]] = []
    for ox, oy, tx, ty, nx, ny in _stations(params):
        wx = ox + tx * local_x - ty * local_y
        wy = oy + ty * local_x + tx * local_y
        out.append((wx, wy, height * 0.55))
    return out


def rail_paths_mm(params: HandleParameters) -> list[list[tuple[float, float, float]]]:
    """Short entry-slot centre lines for drawing overlays."""
    length = SLIDER_LENGTH_MM
    paths: list[list[tuple[float, float, float]]] = []
    for ox, oy, tx, ty, _nx, _ny in _stations(params):
        paths.append(
            [
                (ox, oy, SLIDER_HEIGHT_MM * 0.4),
                (ox + tx * length, oy + ty * length, SLIDER_HEIGHT_MM * 0.4),
            ]
        )
    return paths


def exploded_clamshell(params: HandleParameters | None = None, gap_z_mm: float | None = None) -> dict:
    params = params or default_parameters()
    parts = build_clamshell(params)
    gap = float(EXPLODE_GAP_Z_MM if gap_z_mm is None else gap_z_mm)

    def up(wp: cq.Workplane, dz: float) -> cq.Workplane:
        return wp.translate((0.0, 0.0, dz))

    return {
        "params": params,
        "parts": parts,
        "workpieces": [
            (up(parts.soft_plus, gap), SOFT_PRINT["color"], SOFT_PRINT["label"] + " +Z", 0.38),
            (up(parts.hard_plus, gap), HARD_PRINT["color"], HARD_PRINT["label"] + " +Z", 0.95),
            (up(parts.soft_minus, -gap), SOFT_PRINT["color"], SOFT_PRINT["label"] + " -Z", 0.38),
            (up(parts.hard_minus, -gap), HARD_PRINT["color"], HARD_PRINT["label"] + " -Z", 0.95),
            (up(parts.rails_male, -gap), CLICK_HARD["color"], "Kleine slider", 1.0),
            (up(parts.click_male, -gap), "#e53e3e", "Eenrichtings-pawl (resetpin)", 1.0),
        ],
        "click_centers": [(x, y, z - gap) for x, y, z in click_sphere_centers_mm(params)],
        "rail_paths": [[(x, y, z - gap) for x, y, z in path] for path in rail_paths_mm(params)],
        "gap_z_mm": gap,
    }
