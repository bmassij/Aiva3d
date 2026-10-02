"""Automated validation for the CAD environment."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import cadquery as cq
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config
from cad.utilities.validation import assert_valid_solid, solid_volume
from exporters.pipeline import export_step, export_stl


def test_cadquery_import():
    assert cq.__version__


def test_boolean_and_solid():
    base = cq.Workplane("XY").box(20, 20, 10)
    cut = cq.Workplane("XY").center(0, 0).circle(5).extrude(15)
    result = base.cut(cut)
    assert_valid_solid(result)
    assert solid_volume(result) < solid_volume(base)


def test_parameter_change_affects_volume():
    small = cq.Workplane("XY").box(10, 10, 10)
    large = cq.Workplane("XY").box(20, 20, 20)
    assert solid_volume(large) > solid_volume(small)


def test_mounting_plate_build_and_export(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "EXPORT_STEP_DIR", tmp_path / "step")
    monkeypatch.setattr(config, "EXPORT_STL_DIR", tmp_path / "stl")
    mod = importlib.import_module("projects.examples.test_mounting_plate")
    model = mod.build()
    assert_valid_solid(model)
    step = export_step(model, "test_mounting_plate_test")
    stl = export_stl(model, "test_mounting_plate_test")
    assert step.path.exists() and step.bytes_written > 0
    assert stl.path.exists() and stl.bytes_written > 0


@pytest.mark.parametrize(
    "module_path,build_name",
    [
        ("templates.bracket.bracket_template", "build_bracket"),
        ("templates.enclosure.enclosure_template", "build_enclosure"),
        ("templates.handle.handle_template", "build_handle"),
        ("templates.housing.housing_template", "build_housing"),
        ("templates.mechanical_part.mechanical_part_template", "build_mechanical_part"),
    ],
)
def test_templates_build(module_path, build_name):
    mod = importlib.import_module(module_path)
    builder = getattr(mod, build_name)
    model = builder()
    assert_valid_solid(model)
