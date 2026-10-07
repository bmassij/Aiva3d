# Handle test — photo-based grip reconstruction

Reverse-engineering test for the **mesh sleeve** on the right leg of the photographed D-loop handle.

## Reference photos

Place originals in `reference/` (included):

- `WhatsApp Image 2026-10-02 at 20.16.42.jpeg` — bare metal + grid  
- `WhatsApp Image 2026-10-02 at 20.16.42 (1).jpeg` — sleeved grip + grid  

Read **`reference_analysis.md`** before changing dimensions.

## Model

| Part | File | Description |
|------|------|-------------|
| Hard core | `model.build_hard_core()` | ~10 mm dia along measured centerline |
| Soft shell | `model.build_soft_outer_shell()` | 30 mm OD VariShore-style shell |
| Print | two XY clamshell halves | Short sliders in L-notches; slide in, click one way |

## Verify & export

**Production exports** (final handle):

```powershell
cd D:\AI\3d
.\.venv\Scripts\python.exe scripts\export_handle_final.py
.\.venv\Scripts\python.exe scripts\build_freecad_handle.py
```

→ `projects/work/handle_test/exports/` (`handle_*.step`, `handle_complete.stl`, `handle_complete.3mf`, `handle_assembly.FCStd`)

**Verification pipeline** (separate folder):

```powershell
.\.venv\Scripts\python.exe scripts\verify_handle_reconstruction.py
```

→ `exports/verification/handle_test/`

## Print (4 helften)

Niet `handle_complete` printen. Gebruik `exports/print/`:

| STL | Materiaal |
|-----|-----------|
| `01_hard_plus.stl` | hard, niet-schuim |
| `02_hard_minus.stl` | hard, niet-schuim |
| `03_soft_plus_varishore.stl` | VariShore schuim (L-inkepingen) |
| `04_soft_minus_varishore_rails.stl` | VariShore schuim (sliders + haak) |

Tekening: `exports/drawings/handle_print_sheet.png`

In FreeCAD helften uit elkaar: selecteer `SoftPlus` → Data → **Placement → Position → z** = `32` mm (en `SoftMinus` z = `-32`). Of open opnieuw na de exploded save.

```powershell
.\.venv\Scripts\python.exe scripts\export_handle_final.py
.\.venv\Scripts\python.exe scripts\render_handle_drawing.py
```

## UI

```powershell
python scripts\start_cad_ui.py
```
