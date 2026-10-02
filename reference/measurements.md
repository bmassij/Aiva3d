# Measurements and reverse engineering

## Provenance labels

Every dimension used in CAD must be tagged in code using `Dimension` and `DataProvenance`:

| Label | Meaning |
|--------|---------|
| **MEASURED** | Taken from calipers, ruler, drawing, or photogrammetry with documented method |
| **ASSUMED** | Estimated or chosen for function/printability — not measured |
| **CALCULATED** | Derived from other dimensions (e.g. clearance hole from screw size) |

Never document an assumption as a measured value.

## Workflow

1. Store raw notes under `reference/` (photos, sketches, CSV of dimensions).
2. List each dimension in the model's `ParametricModelMeta` with provenance.
3. Record tolerances and clearance separately from nominal size.
4. Rebuild from parameters only — avoid “magic numbers” in geometry without a named parameter.

## Photographs and grids

- Prefer a 1:1 reference grid or known object size in frame.
- Note camera angle; oblique photos are poor for absolute depth without more data.
- Mark uncertain edges as ASSUMED until confirmed.

## Units

Default **millimeters** for all new models unless explicitly specified otherwise.
