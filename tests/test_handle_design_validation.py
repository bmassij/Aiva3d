"""Design validation tolerances for final handle."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from projects.work.handle_test.ergonomics import assess_grip_od
from projects.work.handle_test.model import build
from projects.work.handle_test.parameters import default_parameters


def test_d_leg_centerline_has_photo_bow():
    from projects.work.handle_test.measurements_loader import centerline_for_cad, load_measurements_doc

    pts = centerline_for_cad(load_measurements_doc())
    xs = [p[0] for p in pts]
    assert max(xs) - min(xs) >= 10.0


def test_design_checks_pass():
    params = default_parameters()
    hard, soft = build(params)
    from projects.work.handle_test.validation import validate_handle_pair

    stats = validate_handle_pair(hard, soft, params)
    assert stats["all_checks_pass"]


def test_ergonomic_assessment_keeps_30mm():
    a = assess_grip_od(30.0)
    assert a.measured_od_mm == 30.0
    assert "30" in a.summary


def test_grip_ergonomic_recommendation_comfort_od():
    from projects.work.handle_test.grip_ergonomic_design import recommend_grip_design

    rec = recommend_grip_design(photo_outer_diameter_mm=30.0)
    assert rec.photo_outer_diameter_mm == 30.0
    assert rec.recommended_nominal_od_mm >= 30.0
    assert rec.recommended_soft_wall_mm >= 8.0
    assert rec.recommended_length_mm >= 100.0
