"""Export pipeline: STEP, STL, 3MF, OBJ with safe filenames."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import cadquery as cq
import trimesh

import config
from cad.utilities.validation import assert_valid_solid


@dataclass
class ExportResult:
    format: str
    path: Path
    bytes_written: int


def _resolve_path(directory: Path, basename: str, suffix: str, overwrite: bool) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{basename}{suffix}"
    if path.exists() and not overwrite and config.PREVENT_EXPORT_OVERWRITE:
        stem = path.stem
        n = 1
        while path.exists():
            path = directory / f"{stem}_{n}{suffix}"
            n += 1
    return path


def export_step(
    workpiece: cq.Workplane,
    basename: str,
    overwrite: bool = False,
) -> ExportResult:
    assert_valid_solid(workpiece, "export_step")
    path = _resolve_path(config.EXPORT_STEP_DIR, basename, ".step", overwrite)
    cq.exporters.export(workpiece, str(path))
    size = path.stat().st_size
    if size == 0:
        raise RuntimeError(f"STEP export produced empty file: {path}")
    return ExportResult("step", path, size)


def export_stl(
    workpiece: cq.Workplane,
    basename: str,
    tolerance: float = config.DEFAULT_MESH_TOLERANCE,
    angular_tolerance: float = config.DEFAULT_MESH_ANGULAR_TOLERANCE,
    overwrite: bool = False,
) -> ExportResult:
    assert_valid_solid(workpiece, "export_stl")
    path = _resolve_path(config.EXPORT_STL_DIR, basename, ".stl", overwrite)
    cq.exporters.export(
        workpiece,
        str(path),
        tolerance=tolerance,
        angularTolerance=angular_tolerance,
    )
    size = path.stat().st_size
    if size == 0:
        raise RuntimeError(f"STL export produced empty file: {path}")
    return ExportResult("stl", path, size)


def _workpiece_to_trimesh(workpiece: cq.Workplane, tolerance: float, angular_tolerance: float) -> trimesh.Trimesh:
    with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        cq.exporters.export(
            workpiece,
            str(tmp_path),
            tolerance=tolerance,
            angularTolerance=angular_tolerance,
        )
        mesh = trimesh.load_mesh(str(tmp_path), process=False)
        if not isinstance(mesh, trimesh.Trimesh):
            raise RuntimeError("Expected a single Trimesh from tessellation")
        return mesh
    finally:
        tmp_path.unlink(missing_ok=True)


def export_3mf(
    workpiece: cq.Workplane,
    basename: str,
    tolerance: float = config.DEFAULT_MESH_TOLERANCE,
    angular_tolerance: float = config.DEFAULT_MESH_ANGULAR_TOLERANCE,
    overwrite: bool = False,
) -> ExportResult:
    assert_valid_solid(workpiece, "export_3mf")
    path = _resolve_path(config.EXPORT_3MF_DIR, basename, ".3mf", overwrite)
    mesh = _workpiece_to_trimesh(workpiece, tolerance, angular_tolerance)
    mesh.export(str(path), file_type="3mf")
    size = path.stat().st_size
    if size == 0:
        raise RuntimeError(f"3MF export produced empty file: {path}")
    return ExportResult("3mf", path, size)


def export_obj(
    workpiece: cq.Workplane,
    basename: str,
    tolerance: float = config.DEFAULT_MESH_TOLERANCE,
    angular_tolerance: float = config.DEFAULT_MESH_ANGULAR_TOLERANCE,
    overwrite: bool = False,
) -> ExportResult:
    assert_valid_solid(workpiece, "export_obj")
    path = _resolve_path(config.EXPORT_OBJ_DIR, basename, ".obj", overwrite)
    mesh = _workpiece_to_trimesh(workpiece, tolerance, angular_tolerance)
    mesh.export(str(path), file_type="obj")
    size = path.stat().st_size
    if size == 0:
        raise RuntimeError(f"OBJ export produced empty file: {path}")
    return ExportResult("obj", path, size)


def export_all(
    workpiece: cq.Workplane,
    basename: str,
    formats: Optional[Iterable[str]] = None,
    overwrite: bool = False,
) -> list[ExportResult]:
    """Export to multiple formats. Unknown formats are skipped."""
    if formats is None:
        formats = ("step", "stl", "3mf", "obj")
    results: list[ExportResult] = []
    for fmt in formats:
        fmt_l = fmt.lower()
        if fmt_l == "step":
            results.append(export_step(workpiece, basename, overwrite=overwrite))
        elif fmt_l == "stl":
            results.append(export_stl(workpiece, basename, overwrite=overwrite))
        elif fmt_l == "3mf":
            results.append(export_3mf(workpiece, basename, overwrite=overwrite))
        elif fmt_l == "obj":
            results.append(export_obj(workpiece, basename, overwrite=overwrite))
    return results
