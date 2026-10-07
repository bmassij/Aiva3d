# Handle / grip — reference & design analysis

**Project:** `projects/work/handle_test`  
**Authoritative measurements:** `reference_measurements.json` (also `reference/reference_measurements.json`)

---

## Customer requirement (original — Limburgish)

> Maar ze motte zo diek waere wie un handvat. Wuurt in hard en zacht geprint dus binnen en boete kant van de greep. Met varioshore. Schuim en neet schuim zekmaar. Kiek ff wat de richtlijnen zien veur un handvat rechttoe rechtaan. values zijn 1 bij 1 cm

### English interpretation

- Grip thickness appropriate for a **handle**.
- **Hard inner** + **soft outer** (VariShore / foam-like shell).
- Check **ergonomic guidelines** for a straightforward handle.
- **Graph paper:** 1 × 1 cm squares.

---

## Grid calibration — KNOWN

| Item | Value | Classification |
|------|-------|----------------|
| Square size | **10.0 × 10.0 mm** | **KNOWN** (physical paper) |

---

## Authoritative dimensions — MEASURED / CALCULATED

| Quantity | Value | Classification | Source |
|----------|-------|----------------|--------|
| Grip length | **130 mm** | **MEASURED** | 13.0 grid squares × 10 mm |
| Grip outer diameter | **30 mm** | **MEASURED** | 3.0 grid squares × 10 mm |
| Hard core diameter | **11.1 mm** | **MEASURED** | Bare-metal rod (~1.1 squares × 10 mm) |
| Soft wall (material, radial) | **9.20 mm** | **CALCULATED** | 15.0 − (5.55 + 0.25) mm |
| Hard/soft clearance | **0.25 mm** | **ASSUMED** | Dual-print interface (`design_constants.py`) |

Automated CV spans (~150 mm / ~36 mm) are **comparison only** — not used for CAD.

---

## ERGONOMIC DESIGN CHECK

### 1. Customer requirement

Customer asked to review normal ergonomic guidelines for a straightforward handgrip (“recht toe recht aan”), without replacing the photographed object.

### 2. Measured photographic dimensions

- **OD 30 mm**, length **130 mm**, core **11.1 mm** (grid-derived).

### 3. Ergonomic reference range

Cylindrical / power-grip guidance commonly cites roughly **30–45 mm** diameter; some studies highlight **~35 mm** as comfortable in maximum-grip tasks. Optimum depends on **hand size**, **task**, and **grip force**.

### 4. Comparison: 30 mm vs guidance

30 mm sits at the **lower end** of the typical cylindrical range but remains **within** the often-cited band.

### 5. Why 30 mm is acceptable here

The **physical sleeve on the reference photos** measures ~3 grid squares → **30 mm**. Ergonomic literature supports handles in this range; smaller diameters can suit smaller hands or finger-wrap grips.

### 6. Effect of soft VariShore outer layer

Compressible foam reduces peak pressure and can feel **larger/ softer** than nominal CAD diameter under load. **CAD uses nominal printed OD (30 mm).**

### 7. Effect of 11.1 mm hard core

Provides structural stiffness and bore matching the metal rod scale; soft shell carries compliance.

### 8. Compression during use

**Not modeled in CAD.** Effective diameter under hand force depends on material batch, print process, and pressure — document separately; do not alter authoritative 30 mm OD.

### 9. Unknowns

- User hand size and exact task (precision vs power grip).
- Out-of-plane bend of rod (only plan-view photos).
- VariShore formulation and print parameters.

### 10. Final design decision

**Keep 30 mm OD and 130 mm length** from grid metrology. Ergonomic review: **acceptable** for a cylindrical power grip at the lower end of common guidance. Optional **~35 mm OD variant** may be explored later as a **separate branch**, not as replacement of photo reconstruction.

---

## Centerline strategy — INFERRED

- **Method:** `three_point_arc_from_traced_leg`
- **Bottom / top:** from scaled sleeve trace on the right D-leg (e.g. bottom X ≈ 3.9 mm, top at loop inner corner X = 0).
- **Mid:** oval right-leg equator (outward X); ends sit inward on the D-curve over the 130 mm sleeve.
- **Reference metal:** same arc shape extended to full loop height (~215 mm) — one continuous right leg, not sleeve arc + straight vertical.
- **Why not dense polyline:** multi-segment sweeps failed OCC validity for the hard core; arc is the stable compromise.
- **Limitation:** plan-view trace only; no side elevation.

---

## Material strategy

| Part | Role | CAD |
|------|------|-----|
| Hard core | Structural inner | Separate solid Ø11.1 mm |
| Soft outer | VariShore shell | Separate solid OD 30 mm, inner void = core + 0.25 mm clearance |

---

## Photo files

| File | Role |
|------|------|
| `reference/WhatsApp Image 2026-10-02 at 20.16.42 (1).jpeg` | Sleeved grip — primary length/OD counts |
| `reference/WhatsApp Image 2026-10-02 at 20.16.42.jpeg` | Bare metal — core diameter |
| `reference/calibrated/*.jpg` | Grid overlays |

---

## Reference metal handle (context only)

`reference_geometry.py` builds **OriginalMetalHandle** from photo-supported plan dimensions:

| Region | Classification |
|--------|----------------|
| Rod Ø 11.1 mm | MEASURED |
| Loop plan bbox (full dark mask) | 163.3 × 215.5 mm | MEASURED | Includes square shaft — **not** used for D-loop CAD width |
| Loop rope plan (ROI, no shaft) | ~98 × ~162 mm | MEASURED | Bare-metal crop; drives `metal_loop` in JSON |
| Top bar / left leg / bottom arc | `metal_loop` + `loop_plan.py` | INFERRED | Hub-to-outer ~57 mm (≈5.7 grid squares); left extent from loop ROI |
| Square bar stock, welds, out-of-plane bend | UNKNOWN (not modeled) |

Production **HardCore** / **SoftGrip** remain separate and are not fused into reference metal.

## Validation & exports

- `python scripts/export_handle_final.py` → `projects/work/handle_test/exports/`
- `python scripts/build_freecad_handle.py` → `handle_assembly.FCStd`
- Verification: `exports/verification/handle_test/` (separate from production exports)
