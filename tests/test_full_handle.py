"""Full printable D-loop and one-way lock."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from projects.work.handle_test.clamshell import build_clamshell, validate_clamshell
from projects.work.handle_test.full_handle import (
    build_loop_rod,
    build_printable_metal_handle,
    loop_ellipse_from_photos,
    photo_centerline_xy,
    validate_full_handle,
)
from projects.work.handle_test.parameters import default_parameters
from projects.work.handle_test.validation import bounding_box_mm


def test_centerline_is_oval_not_stadium():
    pts = photo_centerline_xy()
    height = max(p[1] for p in pts)
    right_mid = max(p[0] for p in pts if abs(p[1] - 0.5 * height) < 10.0)
    right_q = max(p[0] for p in pts if abs(p[1] - 0.25 * height) < 10.0)
    assert right_mid > right_q + 1.5, (right_mid, right_q)


def test_loop_ellipse_matches_rope_plan():
    ell = loop_ellipse_from_photos()
    rod = build_loop_rod(ell)
    bb = bounding_box_mm(rod)
    outer_w = 2.0 * ell.a_mm + 2.0 * ell.rod_radius_mm
    outer_h = 2.0 * ell.b_mm + 2.0 * ell.rod_radius_mm
    assert abs(bb["size_x"] - outer_w) <= 8.0, bb
    assert abs(bb["size_y"] - outer_h) <= 8.0, bb


def test_printable_metal_handle_is_solid():
    handle = build_printable_metal_handle()
    bb = bounding_box_mm(handle)
    assert bb["size_y"] >= 150.0
    assert bb["size_x"] >= 80.0


def test_metal_loop_has_no_click():
    handle = build_printable_metal_handle()
    stats = validate_full_handle(handle)
    assert stats["all_checks_pass"], stats
    assert "no click" in stats["assembly"].lower()


def test_grip_clamshell_still_locks():
    params = default_parameters()
    parts = build_clamshell(params)
    stats = validate_clamshell(parts, params)
    assert stats["all_checks_pass"], stats
