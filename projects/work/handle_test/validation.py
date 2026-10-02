"""Handle-specific validation."""

from __future__ import annotations

import cadquery as cq

from cad.utilities.validation import assert_valid_solid, solid_volume
from projects.work.handle_test.parameters import HandleParameters


def validate_handle_pair(hard: cq.Workplane, soft: cq.Workplane, params: HandleParameters) -> dict:
    assert_valid_solid(hard, "hard_core")
    assert_valid_solid(soft, "soft_outer")
    v_hard = solid_volume(hard)
    v_soft = solid_volume(soft)
    if v_hard <= 0 or v_soft <= 0:
        raise ValueError("volumes must be positive")
    if params.outer_layer_thickness_mm <= 0:
        raise ValueError("outer_layer_thickness_mm must be positive")
    return {
        "hard_volume_mm3": v_hard,
        "soft_volume_mm3": v_soft,
        "outer_radius_mm": params.outer_radius_mm,
        "core_radius_mm": params.core_radius_mm,
    }
