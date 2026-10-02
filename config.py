"""Project-wide configuration for the CAD environment."""

from pathlib import Path

# Repository root (this file lives at the root).
ROOT = Path(__file__).resolve().parent

# Default linear units: millimeters unless explicitly overridden in a model.
DEFAULT_UNIT = "mm"
DEFAULT_UNIT_LABEL = "millimeters"

# Export and preview output locations.
EXPORTS_DIR = ROOT / "exports"
EXPORT_STEP_DIR = EXPORTS_DIR / "step"
EXPORT_STL_DIR = EXPORTS_DIR / "stl"
EXPORT_3MF_DIR = EXPORTS_DIR / "3mf"
EXPORT_OBJ_DIR = EXPORTS_DIR / "obj"
PREVIEW_DIR = ROOT / "preview" / "output"

PROJECTS_DIR = ROOT / "projects"
PROJECTS_WORK_DIR = PROJECTS_DIR / "work"
PROJECTS_EXAMPLES_DIR = PROJECTS_DIR / "examples"

TEMPLATES_DIR = ROOT / "templates"

# Mesh defaults for STL / tessellated previews.
DEFAULT_MESH_TOLERANCE = 0.1  # mm, angular tolerance in degrees for CadQuery meshing
DEFAULT_MESH_ANGULAR_TOLERANCE = 0.1

# When True, export helpers refuse to overwrite existing files.
PREVENT_EXPORT_OVERWRITE = True
