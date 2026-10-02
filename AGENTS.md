# Agent instructions (CAD environment)

This repository is a **general-purpose personal CAD lab**, not a single customer part.

- **Stack:** Python 3.10 venv, CadQuery 2.x, OpenCascade via `cadquery-ocp`.
- **Entry points:** `projects/examples/test_mounting_plate.py`, `scripts/run_example.py`, `python -m pytest`.
- **Read first:** `README.md`, `docs/ARCHITECTURE.md`, `docs/NEW_PROJECT.md`, `reference/measurements.md`.

When generating or editing CAD:

1. Use mm and explicit parameters.
2. Implement `build()`; validate solids before export.
3. Export through `exporters/pipeline.py`.
4. Run tests before claiming success.
