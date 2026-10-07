# CadQuery AI pipeline (LM Studio)

Multi-model routing and the **Qwen2.5-Coder-7B-CadQuery** fine-tune live under `aiva3d/ai/`.

## Pipeline

```
Photo → Qwen3-VL (vision_provider) → landmarks
     → geometry_engine (Python math) → CadSpecification
     → CadQueryProvider → generated Python
     → code_validator → sandbox_runner (subprocess)
     → geometry_validator → FreeCAD bridge / exporters
```

## Vision (Qwen3-VL + LM Studio)

Analyze reference photos (what is metal vs printable grip):

```powershell
$env:VISION_MODEL='qwen3-vl-8b-instruct'
.\.venv\Scripts\python.exe scripts\analyze_handle_reference_vision.py --pair
```

Reports: `projects/work/handle_test/reference/vision_analysis.md` (+ `.json`).

Do not send photos to the CadQuery code model.

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `LMSTUDIO_BASE_URL` | `http://127.0.0.1:1234` | LM Studio OpenAI-compatible API |
| `CADQUERY_MODEL` | `qwen2.5-coder-7b-cadquery` | Must match LM Studio model id |
| `CADQUERY_TEMPERATURE` | `0.2` | Generation temperature |
| `CADQUERY_MAX_TOKENS` | `1024` | Max tokens |
| `CADQUERY_STOP_TOKEN` | `` | Stop sequence |
| `MAX_CAD_REPAIR_ATTEMPTS` | `3` | Repair loop cap |
| `VISION_MODEL` | `Qwen3-VL-8B-Instruct` | Vision routing only |
| `GENERAL_REASONING_MODEL` | `Qwen3.6-35B-A3B` | Optional |
| `GENERAL_CODING_MODEL` | `Qwen2.5-Coder-14B-Instruct` | Optional |

## Licensing

**Qwen2.5-Coder-7B-CadQuery** is described as **CC-BY-NC-SA-4.0** (non-commercial).  
Do not use it in commercial deployments without explicit permission. See `aiva3d.ai.settings.AISettings.cadquery_license_note`.

## Security

Generated code is **never** `exec()`’d in the Streamlit or main CadQuery process. Execution runs in a **subprocess** with static AST checks first.

## Diagnostic (requires LM Studio + loaded model)

```powershell
.\.venv\Scripts\python.exe -m aiva3d.ai.test_cadquery
```

Optional flags: `--no-repair`, `--prompt "..."`.

## Unit tests (no LM Studio)

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_cadquery_ai.py -q
```
