"""Framework-agnostic 3MF/mesh analysis (no pricing, no CadQuery)."""

from print_core.analysis import (
    calculate_bounding_box,
    calculate_mass,
    calculate_surface_area,
    calculate_volume,
    detect_units,
    extract_material_metadata,
    extract_meshes,
    extract_objects,
    inspect_3mf,
    parse_3mf,
)
from print_core.models import MeshObjectInfo, PrintCoreAnalysis, UnitsInfo

__all__ = [
    "MeshObjectInfo",
    "PrintCoreAnalysis",
    "UnitsInfo",
    "parse_3mf",
    "inspect_3mf",
    "extract_objects",
    "extract_meshes",
    "calculate_volume",
    "calculate_surface_area",
    "calculate_bounding_box",
    "detect_units",
    "extract_material_metadata",
    "calculate_mass",
]
