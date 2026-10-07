# Quote API (Crooijmans Pilot 3)

Self-contained **FastAPI** service under `quote_api/`. No Streamlit, no CadQuery.

## Run locally

```powershell
cd D:\AI\3d
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn quote_api.app:app --host 0.0.0.0 --port 8080
```

OpenAPI: `http://localhost:8080/docs`

## Environment

| Variable | Purpose |
|----------|---------|
| `QUOTE_MAX_UPLOAD_BYTES` | Max upload size (default 52428800) |
| `QUOTE_CORS_ORIGINS` | Comma-separated CORS origins (optional) |
| `QUOTE_CURRENCY` | Currency code (default `EUR`) |

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health |
| POST | `/estimate` | Fast indicative quote (`multipart/form-data`) |
| POST | `/quote` | Commercial quote JSON |
| POST | `/quote/pdf` | Customer PDF (no internal cost/margin) |
| GET | `/materials` | Material profiles (DEVELOPMENT DEFAULT) |
| GET | `/machines` | Machine profiles |
| GET | `/pricing/profiles` | Labor, post, packaging, margin profiles |

### Upload fields

- `file` (required) — `.3mf`
- `quantity` (optional, default 1)
- `material_profile` (optional profile id)
- `machine_profile` (optional)
- `pricing_profile` (optional)

## Response model

See `quote_api/schemas.py` — `QuoteAnalysis` includes internal `cost_price` and `margin_percent` for the **internal** Crooijmans UI. Customer PDF omits those fields.

## Vercel

Set `QUOTE_API_URL` on the **Crooijmans** Vercel project to the public base URL of this API (no trailing slash required). The Next.js route `web/crooijmans/app/api/quote/route.ts` proxies `POST /quote`.

## Deploy

Deploy `quote_api` on any Python host (VPS, Runpod, etc.). Install `quote_api/requirements.txt` or root `requirements.txt`. Process manager example:

```bash
uvicorn quote_api.app:app --host 0.0.0.0 --port 8080
```
