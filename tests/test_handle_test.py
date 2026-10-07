"""Tests for handle_test dual-material grip."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from projects.work.handle_test.model import build, build_hard_core, build_soft_outer_shell
from projects.work.handle_test.parameters import default_parameters
from projects.work.handle_test.validation import validate_handle_pair
from ui.design_record import HANDLE_CUSTOMER_TEXT, design_record_from_handle_customer_text
from ui.nl_adjust import apply_instruction


def test_handle_build_validates():
    params = default_parameters()
    hard, soft = build(params)
    stats = validate_handle_pair(hard, soft, params)
    assert stats["hard_volume_mm3"] > 0
    assert stats["soft_volume_mm3"] > 0
    # Photo-measured sleeve span ~85 mm on grid
    assert 125 <= stats["grip_span_y_mm"] <= 135
    assert 28 <= stats["max_outer_width_x_mm"] <= 58


def test_hard_and_soft_solids():
    params = default_parameters()
    assert build_hard_core(params).val().Volume() > 0
    assert build_soft_outer_shell(params).val().Volume() > 0


def test_design_record_preserves_customer_text():
    rec = design_record_from_handle_customer_text()
    assert HANDLE_CUSTOMER_TEXT in rec.original_instruction
    assert rec.design_requirements


def test_nl_thicker_adjustment():
    params = default_parameters()
    before = params.core_radius_mm
    updated, notes = apply_instruction("make the grip thicker", params)
    assert updated.core_radius_mm > before
    assert notes


@pytest.mark.parametrize("bad_radius", [0.0, -1.0])
def test_model_rejects_bad_radius(bad_radius):
    params = default_parameters()
    params.core_radius_mm = bad_radius
    with pytest.raises(ValueError):
        build_hard_core(params)
