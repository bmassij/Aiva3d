# Handle test project

Interactive reverse-engineering test for a dual-material handle (hard core + VariShore shell).

## Files

| File | Purpose |
|------|---------|
| `parameters.py` | Parametric dimensions and provenance |
| `model.py` | `build_hard_core()`, `build_soft_outer_shell()` |
| `validation.py` | Solid checks and volume report |
| `reference_analysis.md` | Photo-based analysis (update after upload) |
| `reference/` | Project-linked reference images |

## CLI (without UI)

```powershell
cd D:\AI\Aiva3D
.\.venv\Scripts\python.exe scripts\run_handle_test_pipeline.py
```

## UI

```powershell
python scripts\start_cad_ui.py
```

Select project **handle_test** in the browser.
