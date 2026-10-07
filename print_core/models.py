"""Data models for print_core analysis (technical only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Tuple


@dataclass
class UnitsInfo:
    """Linear units for mesh coordinates."""

    unit: str  # e.g. "mm"
    confidence: str  # "assumed" | "from_3mf_metadata"
    notes: str = ""


@dataclass
class MaterialHint:
    """Heuristic material info from mesh name/color — not a commercial SKU."""

    object_name: str
    filament_index: Optional[int] = None
    material_label: Optional[str] = None
    rgba: Optional[Tuple[int, int, int, int]] = None


@dataclass
class MeshObjectInfo:
    name: str
    volume_mm3: float
    surface_area_mm2: float
    bounding_box_mm: Tuple[float, float, float]  # extents x, y, z
    triangle_count: int
    material_hints: list[MaterialHint] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PrintCoreAnalysis:
    filename: str
    object_count: int
    objects: list[MeshObjectInfo]
    materials: list[MaterialHint]
    volume_mm3: float
    surface_area_mm2: float
    bounding_box_mm: Tuple[float, float, float]
    units: UnitsInfo
    raw_scene_metadata: dict[str, Any] = field(default_factory=dict)
