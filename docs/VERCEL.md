# Vercel (customer web)

The **customer-facing** Next.js app lives in `web/customer/`. It handles logo upload and color preview in the browser. **3MF/CadQuery** stays on your Python backend (Streamlit or future API)—not on Vercel.

## Deploy

```powershell
cd D:\AI\3d\web\customer
npm install
npx vercel link    # once: link to Vercel project
npx vercel --prod  # production deploy
```

Or connect the GitHub repo in the Vercel dashboard and set **Root Directory** to `web/customer`.

## Environment

| Variable | Purpose |
|----------|---------|
| `NEXT_PUBLIC_CAD_API_URL` | URL to Streamlit or CAD API (e.g. `http://localhost:8501` for dev only) |

## Health check

`GET /api/health` — used to verify deploy after push.
