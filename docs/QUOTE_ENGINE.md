# Quote Engine

Commercial calculation layer for Crooijmans Pilot 3.

## Pipeline

```
3MF upload
  → print_core.inspect_3mf (volume, objects, material hints)
  → estimate_print_time_minutes (ESTIMATE)
  → PricingEngine (material + machine + labor + post + packaging)
  → margin → sale_price
  → optional customer PDF
```

## Estimate vs quote

| Mode | Endpoint | Use |
|------|----------|-----|
| **Estimate** | `POST /estimate` | Quick indicative pricing for uploads |
| **Quote** | `POST /quote` | Same calculation today; reserved for stricter validation / PDF workflow later |

Both use real 3MF parsing (no mock volume).

## Print time

`quote_api/engine/estimate.py` produces an **ESTIMATE** from volume, infill, layer height, and nominal speed. It is **not** slicer-exact. Phase 2 may plug in Orca/Bambu slicer output.

## Pricing

Deterministic formulas in `quote_api/engine/pricing.py` and `margin.py`:

```
cost_price = material + machine + labor + post_processing + packaging
sale_price = cost_price × (1 + margin_percent / 100)
```

No AI for financial math.

## Profiles

JSON under `quote_api/profiles/`:

- `materials.json` — density, `price_per_kg`
- `machines.json` — `machine_cost_per_hour`, default speed/layer/infill
- `pricing.json` — labor, fixed costs, `margin_percent`

All values are marked **DEVELOPMENT DEFAULT**. Replace with Crooijmans production rates before go-live:

- filament prices
- machine rates
- labor and post-processing
- packaging
- margin and quantity breaks

## PDF

`quote_api/pdf/customer.py` — ReportLab customer PDF with sale price only. Internal cost and margin never appear on the PDF.

## Tests

```powershell
python -m pytest tests/test_print_core.py tests/test_quote_api.py -v
```

Integration tests use `handle_greep_2helften_2material.3mf` when present (run `python scripts/export_handle_final.py` first).
