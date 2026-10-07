"""BREP cross-section symmetry / constancy along grip (no mesh)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from projects.work.handle_test.design_constants import HARD_SOFT_CLEARANCE_MM
from projects.work.handle_test.geometry_symmetry import (
    pick_annulus,
    pick_radius,
    section_at_path_parameter,
)
from projects.work.handle_test.model import build
from projects.work.handle_test.parameters import default_parameters

R_CORE = 5.55
R_INNER_SHELL = 5.55 + HARD_SOFT_CLEARANCE_MM  # 5.8 mm
R_OUTER = 15.0
TOL_RADIUS = 0.25
TOL_CIRCULARITY = 0.20

PATH_T_SAMPLES = (0.35, 0.5, 0.65)


def test_grip_cross_sections_along_stations():
    params = default_parameters()
    hard, soft = build(params)
    hard_shape = hard.val().wrapped
    soft_shape = soft.val().wrapped

    for t in PATH_T_SAMPLES:
        hard_rep = section_at_path_parameter(hard_shape, params, t)
        soft_rep = section_at_path_parameter(soft_shape, params, t)
        y = hard_rep.station_y_mm
        assert hard_rep.method == soft_rep.method == "path_perpendicular"

        core = pick_radius(hard_rep.circles, R_CORE)
        assert core is not None, f"hard: no core circle at t={t} Y={y}"
        assert abs(core.radius_mm - R_CORE) <= TOL_RADIUS, (
            f"hard radius at t={t} Y={y}: {core.radius_mm}"
        )
        assert core.radius_std_mm <= TOL_CIRCULARITY

        inner, outer = pick_annulus(soft_rep.circles)
        assert inner is not None and outer is not None, f"soft: missing rings at t={t} Y={y}"
        assert abs(inner.radius_mm - R_INNER_SHELL) <= TOL_RADIUS
        assert inner.radius_std_mm <= TOL_CIRCULARITY
        if t == 0.5:
            assert abs(outer.radius_mm - R_OUTER) <= 0.75
            assert outer.radius_std_mm <= 0.5
            shell_radial = outer.radius_mm - inner.radius_mm
            assert abs(shell_radial - 9.2) <= 0.8, f"shell radial at t={t}: {shell_radial}"
