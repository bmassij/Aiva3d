"""Tests for print_core (no CadQuery)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import trimesh

from print_core import (
    calculate_mass,
    inspect_3mf,
    parse_3mf,
)
from print_core.errors import Empty3MFError, EmptyFileError, Invalid3MFError

ROOT = Path(__file__).resolve().parents[1]
HANDLE_3MF = (
    ROOT
    / "projects"
    / "work"
    / "handle_test"
    / "exports"
    / "print"
    / "handle_greep_2helften_2material.3mf"
)


def _box_3mf(path: Path, names: list[str]) -> None:
    scene = trimesh.Scene()
    for i, name in enumerate(names):
        box = trimesh.creation.box(extents=(10.0, 20.0, 5.0))
        t = np.eye(4)
        t[0, 3] = i * 15.0
        scene.add_geometry(box, geom_name=name, transform=t)
    scene.export(str(path), file_type="3mf")


def test_parse_single_object(tmp_path: Path) -> None:
    p = tmp_path / "one.3mf"
    _box_3mf(p, ["PART_A"])
    analysis = inspect_3mf(p)
    assert analysis.object_count == 1
    assert analysis.volume_mm3 > 0
    assert analysis.objects[0].name == "PART_A"


def test_parse_multi_object(tmp_path: Path) -> None:
    p = tmp_path / "multi.3mf"
    _box_3mf(p, ["OBJ_1", "OBJ_2"])
    analysis = inspect_3mf(p)
    assert analysis.object_count == 2
    assert analysis.volume_mm3 > analysis.objects[0].volume_mm3


def test_multi_material_name_hints(tmp_path: Path) -> None:
    p = tmp_path / "dual.3mf"
    _box_3mf(p, ["HELFT_PLUS__FILAMENT1_hard", "HELFT_PLUS__FILAMENT2_varishore"])
    analysis = inspect_3mf(p)
    assert analysis.object_count == 2
    filaments = {h.filament_index for h in analysis.materials}
    assert filaments == {1, 2}


def test_calculate_mass() -> None:
    # 1 cm³ at 1 g/cm³ = 1 g → 1000 mm³
    assert calculate_mass(1000.0, 1.0) == pytest.approx(1.0)


def test_empty_file_raises(tmp_path: Path) -> None:
    p = tmp_path / "empty.3mf"
    p.write_bytes(b"")
    with pytest.raises(EmptyFileError):
        parse_3mf(p)


def test_invalid_file_raises(tmp_path: Path) -> None:
    p = tmp_path / "bad.3mf"
    p.write_bytes(b"not a zip")
    with pytest.raises(Invalid3MFError):
        parse_3mf(p)


def test_print_core_no_cadquery_imports() -> None:
    pkg = ROOT / "print_core"
    for py in pkg.rglob("*.py"):
        text = py.read_text(encoding="utf-8")
        assert "cadquery" not in text
        assert "streamlit" not in text
        assert "quote_api" not in text


@pytest.mark.integration
def test_handle_greep_3mf_if_present() -> None:
    if not HANDLE_3MF.is_file():
        pytest.skip(f"fixture not built: {HANDLE_3MF}")
    analysis = inspect_3mf(HANDLE_3MF)
    assert analysis.object_count >= 2
    assert analysis.volume_mm3 > 100.0
    assert any(h.filament_index for h in analysis.materials)
