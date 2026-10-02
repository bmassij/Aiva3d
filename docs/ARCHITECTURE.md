# Architecture

## Layers

| Layer | Location | Role |
|--------|-----------|------|
| Configuration | `config.py` | Paths, units (mm), export directories |
| Primitives & utilities | `cad/` | Reusable ops, validation, provenance metadata |
| Templates | `templates/` | Starter parametric models (not customer finals) |
| Projects | `projects/work/`, `projects/examples/` | Your active designs and verified examples |
| Export | `exporters/pipeline.py` | STEP, STL, 3MF, OBJ with safe naming |
| Preview | `preview/viewer.py` | Matplotlib mesh snapshot; optional VTK `show` |
| Future AI | `cad/ai_interface.py` | Typed request/result hooks for NL → parameters |

## Data flow

```
parameters (+ provenance metadata)
    → build() → cq.Workplane
    → assert_valid_solid()
    → preview (optional)
    → export_* → exports/<format>/
```

## Units

All internal geometry uses **millimeters** unless a model documents otherwise.

## OpenCascade

Solid modeling is performed by OpenCascade via **CadQuery**. Do not bypass CadQuery for core B-rep unless there is a documented exception.
