# Handle test — reference analysis

**Project:** `projects/work/handle_test`  
**Grid scale (when photos present):** 1 square = **1 cm** = **10 mm**  
**Status:** Initial analysis pass — **no reference photographs were on disk at generation time.** Upload images via CAD AI UI or copy into `reference/` and `projects/work/handle_test/reference/`.

## 1. Visible geometry (from customer text + expected photos)

| Element | Notes |
|---------|--------|
| Existing handvat / grip | Primary reconstruction target |
| Graph paper backdrop | Dimensional reference (10 mm per square) |
| Metal assembly | **Out of scope** — do not remodel unless required by photos |
| Inner hard material | Structural / non-foam grip core |
| Outer soft material | VariShore or similar foam-like shell |

## 2. Measured dimensions (from 1 cm grid)

| Dimension | Value (mm) | Confidence |
|-----------|------------|------------|
| — | *None committed* | Photos not available for measurement in this pass |

**Action:** Measure along grip length, outer diameter, bend offset, and mounting features from uploaded photos using the 10 mm grid.

## 3. Inferred dimensions

| Item | Inference | Confidence |
|------|-----------|------------|
| Dual-wall grip | Customer requires hard inner + soft outer | High (text) |
| Grip follows curved path | Visible handle shape in photos (when uploaded) | Pending photos |

## 4. Assumptions (not measured)

| Parameter | Placeholder | Confidence |
|-----------|-------------|------------|
| `centerline_points_mm` | 5-point spline in XZ, 180 mm span | **Low** |
| `core_radius_mm` | 11 mm | **Low** |
| `outer_layer_thickness_mm` | 4 mm VariShore wall | **Low–medium** |
| `clearance_mm` | 0.2 mm print interface | **Medium** |

## 5. Unknown dimensions

- Exact grip length from photos  
- Outer diameter at widest point  
- Mounting interface to metal parts (if any)  
- End-cap geometry at grip terminations  

## 6. Proposed centerline

- **Plane:** XZ (length along +X, vertical bend in Z)  
- **Type:** CadQuery spline through `centerline_points_mm` in `parameters.py`  
- **Rationale:** Allows tracing the photographed grip once points are picked on the grid  

## 7. Proposed grip diameter

| Layer | Radius (mm) | Provenance |
|-------|-------------|------------|
| Hard core | `core_radius_mm` (default 11) | ASSUMED |
| Outer (foam) | `core_radius_mm + outer_layer_thickness_mm` | CALCULATED |

## 8. Hard inner layer

- Solid sweep along centerline at `core_radius_mm`  
- Exported as `handle_test_hard_*`  

## 9. Soft outer layer

- Shell: outer sweep minus inner void (`core_radius_mm + clearance_mm`)  
- Exported as `handle_test_soft_*`  

## 10. Confidence summary

| Dimension | Confidence |
|-----------|------------|
| Grid scale 10 mm | High (stated) |
| Dual material split | High (customer) |
| Centerline coordinates | **Low** until photo trace |
| Core / wall thickness | **Low** until photo cross-section |

## Customer instruction (preserved)

> Maar ze motte zo diek waere wie un handvat. Wuurt in hard en zacht geprint dus binnen en boete kant van de greep. Met varioshore. Schuim en neet schuim zekmaar. Kiek ff wat de richtlijnen zien veur un handvat rechttoe rechtaan. values zijn 1 bij 1 cm

## Next steps

1. Upload reference photos in CAD AI.  
2. Measure centerline points and diameters using 10 mm grid.  
3. Update `parameters.py` — move values from ASSUMED to MEASURED with notes.  
4. Regenerate and compare side-by-side in the UI.  
