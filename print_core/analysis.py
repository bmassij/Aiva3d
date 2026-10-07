"""3MF parsing and mesh metrics via trimesh."""

from __future__ import annotations

import re
from pathlib import Path
from typing import BinaryIO, Union

import numpy as np
import trimesh

from print_core.errors import Empty3MFError, EmptyFileError, Invalid3MFError
from print_core.models import MaterialHint, MeshObjectInfo, PrintCoreAnalysis, UnitsInfo

PathLike = Union[str, Path]
LoadSource = Union[PathLike, BinaryIO, bytes]

_FILAMENT_NAME_RE = re.compile(r"FILAMENT(\d+)", re.IGNORECASE)
_MATERIAL_TAIL_RE = re.compile(r"__FILAMENT\d+_(.+)$", re.IGNORECASE)


def parse_3mf(source: LoadSource, filename: str = "model.3mf") -> trimesh.Scene:
    """Load a 3MF into a trimesh Scene."""
    if isinstance(source, bytes):
        if len(source) == 0:
            raise EmptyFileError("empty file")
        try:
            loaded = trimesh.load(trimesh.util.wrap_as_stream(source), file_type="3mf")
        except Exception as exc:
            raise Invalid3MFError(f"cannot parse 3MF: {exc}") from exc
    elif isinstance(source, (str, Path)):
        path = Path(source)
        if not path.is_file():
            raise Invalid3MFError(f"not a file: {path}")
        if path.stat().st_size == 0:
            raise EmptyFileError("empty file")
        try:
            loaded = trimesh.load(str(path), file_type="3mf", force="scene")
        except Exception as exc:
            raise Invalid3MFError(f"cannot parse 3MF: {exc}") from exc
        filename = path.name
    else:
        try:
            data = source.read()
        except Exception as exc:
            raise Invalid3MFError(f"cannot read upload: {exc}") from exc
        if len(data) == 0:
            raise EmptyFileError("empty file")
        return parse_3mf(data, filename=filename)

    if loaded is None:
        raise Empty3MFError("no geometry in 3MF")
    if isinstance(loaded, trimesh.Trimesh):
        scene = trimesh.Scene()
        scene.add_geometry(loaded, geom_name="object_0")
        return scene
    if isinstance(loaded, trimesh.Scene):
        if len(loaded.geometry) == 0:
            raise Empty3MFError("no geometry in 3MF")
        return loaded
    raise Invalid3MFError(f"unexpected load type: {type(loaded)}")


def extract_meshes(scene: trimesh.Scene) -> list[tuple[str, trimesh.Trimesh]]:
    """Return (name, mesh) pairs from a scene."""
    out: list[tuple[str, trimesh.Trimesh]] = []
    for name, geom in scene.geometry.items():
        if isinstance(geom, trimesh.Trimesh):
            out.append((str(name), geom))
        elif isinstance(geom, trimesh.Scene):
            for sub_name, sub in extract_meshes(geom):
                out.append((f"{name}/{sub_name}", sub))
    return out


def extract_objects(scene: trimesh.Scene) -> list[MeshObjectInfo]:
    """Build per-object metrics."""
    meshes = extract_meshes(scene)
    if not meshes:
        raise Empty3MFError("no mesh objects")
    objects: list[MeshObjectInfo] = []
    for name, mesh in meshes:
        hints = extract_material_metadata(name, mesh)
        vol = calculate_volume(mesh)
        area = calculate_surface_area(mesh)
        bbox = calculate_bounding_box(mesh)
        objects.append(
            MeshObjectInfo(
                name=name,
                volume_mm3=vol,
                surface_area_mm2=area,
                bounding_box_mm=bbox,
                triangle_count=int(len(mesh.faces)),
                material_hints=hints,
            )
        )
    return objects


def calculate_volume(mesh: trimesh.Trimesh) -> float:
    """Volume in mm³ (assumes mesh coordinates are mm)."""
    if mesh.is_empty:
        return 0.0
    return float(abs(mesh.volume))


def calculate_surface_area(mesh: trimesh.Trimesh) -> float:
    """Surface area in mm²."""
    if mesh.is_empty:
        return 0.0
    return float(mesh.area)


def calculate_bounding_box(mesh: trimesh.Trimesh) -> tuple[float, float, float]:
    """Axis-aligned extents (x, y, z) in mm."""
    if mesh.is_empty:
        return (0.0, 0.0, 0.0)
    ext = mesh.bounding_box.extents
    return (float(ext[0]), float(ext[1]), float(ext[2]))


def detect_units(scene: trimesh.Scene) -> UnitsInfo:
    """3MF convention is millimeters; trimesh does not always expose unit metadata."""
    meta = getattr(scene, "metadata", None) or {}
    unit_hint = meta.get("units") or meta.get("unit")
    if unit_hint and str(unit_hint).lower() in ("mm", "millimeter", "millimeters"):
        return UnitsInfo(unit="mm", confidence="from_3mf_metadata", notes=str(unit_hint))
    return UnitsInfo(
        unit="mm",
        confidence="assumed",
        notes="3MF production convention; verify for non-standard exports.",
    )


def _vertex_rgba(mesh: trimesh.Trimesh) -> tuple[int, int, int, int] | None:
    try:
        colors = mesh.visual.vertex_colors
        if colors is None or len(colors) == 0:
            return None
        c = np.asarray(colors[0])
        if c.size < 3:
            return None
        a = int(c[3]) if c.size > 3 else 255
        return (int(c[0]), int(c[1]), int(c[2]), a)
    except Exception:
        return None


def extract_material_metadata(name: str, mesh: trimesh.Trimesh | None = None) -> list[MaterialHint]:
    """Heuristic hints from geometry naming (e.g. handle_test export pattern)."""
    filament_index: int | None = None
    m = _FILAMENT_NAME_RE.search(name)
    if m:
        filament_index = int(m.group(1))
    material_label: str | None = None
    tail = _MATERIAL_TAIL_RE.search(name)
    if tail:
        material_label = tail.group(1).replace("_", " ")
    rgba = _vertex_rgba(mesh) if mesh is not None else None
    return [
        MaterialHint(
            object_name=name,
            filament_index=filament_index,
            material_label=material_label,
            rgba=rgba,
        )
    ]


def calculate_mass(volume_mm3: float, density_g_cm3: float) -> float:
    """Mass in grams from volume (mm³) and density (g/cm³)."""
    if volume_mm3 <= 0 or density_g_cm3 <= 0:
        return 0.0
    volume_cm3 = volume_mm3 / 1000.0
    return float(volume_cm3 * density_g_cm3)


def inspect_3mf(source: LoadSource, filename: str = "model.3mf") -> PrintCoreAnalysis:
    """Full technical inspection of a 3MF file."""
    if isinstance(source, (str, Path)):
        filename = Path(source).name
    scene = parse_3mf(source, filename=filename)
    units = detect_units(scene)
    objects = extract_objects(scene)
    total_vol = sum(o.volume_mm3 for o in objects)
    total_area = sum(o.surface_area_mm2 for o in objects)
    if objects:
        mins = np.array([np.inf, np.inf, np.inf])
        maxs = np.array([-np.inf, -np.inf, -np.inf])
        for _name, mesh in extract_meshes(scene):
            if mesh.is_empty:
                continue
            b = mesh.bounds
            mins = np.minimum(mins, b[0])
            maxs = np.maximum(maxs, b[1])
        combined = tuple(float(maxs[i] - mins[i]) for i in range(3))
    else:
        combined = (0.0, 0.0, 0.0)
    materials: list[MaterialHint] = []
    for obj in objects:
        materials.extend(obj.material_hints)
    meta = dict(getattr(scene, "metadata", None) or {})
    return PrintCoreAnalysis(
        filename=filename,
        object_count=len(objects),
        objects=objects,
        materials=materials,
        volume_mm3=total_vol,
        surface_area_mm2=total_area,
        bounding_box_mm=combined,
        units=units,
        raw_scene_metadata=meta,
    )
