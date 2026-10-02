# Aiva3D

**Aiva3D** is an AI-assisted parametric CAD platform built on **Python**, **CadQuery**, and **OpenCascade**. Design mechanical parts in millimeters, validate solids, preview in 3D, and export STEP/STL/3MF for printing or CAM.

**Recommended location:** `D:\AI\Aiva3D`

## Quick start

```powershell
cd D:\AI\Aiva3D
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest
python scripts\run_handle_test_pipeline.py
```

## Streamlit CAD UI

Interactive reverse-engineering workflow: reference photo upload, natural-language parameter tweaks, Plotly 3D preview, dual-model comparison, and export.

```powershell
python scripts\start_cad_ui.py
```

Open [http://localhost:8501](http://localhost:8501) and select **handle_test** for the dual-material grip project.

## Environment

| Component | Notes |
|-----------|--------|
| Python | **3.10.x** in `.venv` (recommended for CadQuery) |
| CadQuery | **2.7.x** with `cadquery-ocp` |
| UI | Streamlit + Plotly |

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

## Repository layout

```
cad/           Geometry utilities, validation, AI hooks
ui/            Streamlit CAD AI (app, mesh viewer, reference images)
templates/     Parametric starters
projects/      examples/ and work/ (e.g. handle_test)
exporters/     STEP, STL, 3MF, OBJ pipeline
preview/       Matplotlib mesh previews
exports/       Generated files (gitignored except .gitkeep)
tests/         pytest suite
scripts/       UI launcher, pipelines, examples
docs/          Architecture and workflows
reference/     Measurements and uploaded reference photos
```

## Create a model

1. See [docs/NEW_PROJECT.md](docs/NEW_PROJECT.md).
2. Implement `build()` returning a `cq.Workplane` (or documented tuple for multi-body parts).
3. Tag dimensions with `DataProvenance` (`measured` / `assumed` / `calculated`).

## Export

```python
from exporters.pipeline import export_all
export_all(model, "part_name", formats=("step", "stl", "3mf", "obj"))
```

## Tests

```powershell
python -m pytest
```

## GitHub

Remote: [https://github.com/bmassij/Aiva3d](https://github.com/bmassij/Aiva3d)

## License

MIT — see [LICENSE](LICENSE).

## Cursor / agents

Project rules: `.cursor/rules/cad-environment.mdc` and [AGENTS.md](AGENTS.md).
