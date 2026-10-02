# AI-assisted parametric CAD environment

Personal, reusable **Python + CadQuery + OpenCascade** workspace for mechanical parts, enclosures, brackets, fixtures, and 3D-printable prototypes. Default units are **millimeters**.

**Location:** `D:\AI\3d`

## Quick start

```powershell
cd D:\AI\3d
.\.venv\Scripts\Activate.ps1
python -m pytest
python projects\examples\test_mounting_plate.py
```

## Environment

| Component | Notes |
|-----------|--------|
| Python | **3.10.11** in `.venv` (recommended for CadQuery; system default may be 3.13) |
| CadQuery | **2.7.0** with `cadquery-ocp` / OpenCascade |
| Git | Repository initialized locally (no remote by default) |

Create or refresh the venv:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

## Folder structure

```
cad/           Reusable geometry, validation, AI hooks
templates/     Parametric starters (bracket, enclosure, …)
projects/      examples/ (verified) and work/ (your designs)
exporters/     STEP, STL, 3MF, OBJ pipeline
preview/       Matplotlib-based mesh previews
exports/       Generated files (gitignored except .gitkeep)
tests/         pytest suite
scripts/       run_example, preview_model
reference/     Measurement / reverse-engineering notes
docs/          Architecture and workflows
```

## Create a model

1. See [docs/NEW_PROJECT.md](docs/NEW_PROJECT.md).
2. Implement `build()` returning a `cq.Workplane`.
3. Tag dimensions with `DataProvenance` (`measured` / `assumed` / `calculated`).

## Run examples

```powershell
python scripts\run_example.py test_mounting_plate
```

## Preview

Saves a PNG under `preview/output/` (and optionally opens an interactive window):

```powershell
python scripts\preview_model.py --module projects.examples.test_mounting_plate --no-show
```

For interactive VTK viewing (local display):

```python
from preview.viewer import preview_vtk_show
preview_vtk_show(build())
```

## Export

```python
from exporters.pipeline import export_all
export_all(model, "part_name", formats=("step", "stl", "3mf", "obj"))
```

Or use the example script, which exports all supported formats.

## Tests

```powershell
python -m pytest
```

## Git

- `.venv/` and generated exports are ignored.
- Initial commit: `Initial CAD AI environment` (local only).

## Troubleshooting

| Issue | Action |
|--------|--------|
| `import cadquery` fails | Activate `.venv`; use Python 3.10–3.12 |
| Invalid solid after boolean | Check overlaps, fillet radius, sketch closure |
| 3MF/OBJ fails | Ensure `networkx` and `lxml` are installed (`requirements.txt`) |
| VTK `show()` errors | Use matplotlib preview; prefer Python 3.10 in this project |

## Future AI integration

`cad/ai_interface.py` defines `CADBuildRequest` / template registry for a later natural-language → parameters → `build()` → validate → export pipeline. No LLM is bundled in this repo.

## Cursor / AI agents

Project rules for agents live in `.cursor/rules/cad-environment.mdc`.
