# Creating a new CAD project

1. Create a folder under `projects/work/<your_project>/`.
2. Add a Python module with:
   - Named parameters at the top (mm).
   - `ParametricModelMeta` with `Dimension` and `DataProvenance` for each value.
   - `def build() -> cq.Workplane:` containing only geometry logic.
   - Optional `main()` that validates, exports, and previews.
3. Reuse helpers from `cad/primitives/` and `cad/utilities/` instead of duplicating hole/fillet patterns.
4. Run:

```powershell
cd D:\AI\Aiva3D
.\.venv\Scripts\Activate.ps1
python projects\work\<your_project>\<module>.py
```

5. Run tests before committing geometry changes:

```powershell
python -m pytest
```

## Export only

```python
from exporters.pipeline import export_all
export_all(build(), "my_part", formats=("step", "stl"))
```

Files land in `exports/step/`, `exports/stl/`, etc. Existing names are never overwritten silently; a numeric suffix is added.

## Aiva3D UI

Register the project in `ui/app.py` `PROJECTS` and wire build/validation when ready for interactive iteration.
