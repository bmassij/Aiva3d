"""Clamshell split + end symmetry for the printable grip."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from projects.work.handle_test.clamshell import build_clamshell, validate_clamshell
from projects.work.handle_test.parameters import default_parameters
from projects.work.handle_test.validation import validate_end_symmetry


def test_centerline_ends_are_mirrors():
    params = default_parameters()
    sym = validate_end_symmetry(params)
    assert sym["pass"], sym
    assert abs(sym["end_x_mm"][0] - sym["end_x_mm"][1]) <= 0.15


def test_clamshell_builds_and_rails_click():
    params = default_parameters()
    parts = build_clamshell(params)
    stats = validate_clamshell(parts, params)
    assert stats["all_checks_pass"], stats
    assert stats["hard_halves_symmetric"]
    assert stats["rails_on_minus_half"]
    assert stats["hook_visible"]
    assert stats["volumes_mm3"]["hook"] >= 40.0


def test_customer_materials_are_labeled():
    from projects.work.handle_test.materials import HARD_PRINT, SOFT_PRINT, legend_markdown_nl

    md = legend_markdown_nl().lower()
    assert "niet-schuim" in md or "niet schuim" in md.replace("-", " ")
    assert "varishore" in md
    assert "schuim" in md
    assert HARD_PRINT["color"].startswith("#")
    assert SOFT_PRINT["color"].startswith("#")
