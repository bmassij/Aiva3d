# Agent instructions (Aiva3D)

This repository is **Aiva3D** — a parametric CAD platform with a Streamlit UI, not a single frozen customer part.

- **Stack:** Python 3.10 venv, CadQuery 2.x, OpenCascade via `cadquery-ocp`, Streamlit + Plotly for `ui/`.
- **Entry points:** `python -m pytest`, `scripts/run_handle_test_pipeline.py`, `scripts/start_cad_ui.py`, `projects/examples/test_mounting_plate.py`.
- **Read first:** `README.md`, `docs/ARCHITECTURE.md`, `docs/NEW_PROJECT.md`, `reference/measurements.md`.

When generating or editing CAD:

1. Use mm and explicit parameters with `DataProvenance`.
2. Implement `build()`; validate solids before export.
3. Export through `exporters/pipeline.py`.
4. Extend `cad/ai_interface.py` or `ui/nl_adjust.py` for NL→parameter flows — avoid ad-hoc parsing in geometry modules.
5. Run **`python -m pytest`** after substantive CAD changes.
