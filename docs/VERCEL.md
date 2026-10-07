# Vercel — twee web-apps uit één repo

Eén GitHub-repo (**bmassij/Aiva3d**), **twee aparte Vercel-projecten** (twee URL’s).  
**CadQuery, slicer en PDF** blijven op een **Python-backend** (thuis, VPS, Runpod, …) — niet op Vercel.

| App | Map | Doel | Publiek |
|-----|-----|------|---------|
| **Klant** | `web/customer/` | PNG/logo → preview → **3MF** (via `NEXT_PUBLIC_CAD_API_URL`) | Klanten |
| **Crooijmans** | `web/crooijmans/` | **3MF upload** → offerte (via `QUOTE_API_URL`) | Intern / Crooijmans |

## Architectuur

```
                    ┌─────────────────────┐
  Klant (Vercel)    │  web/customer       │──NEXT_PUBLIC_CAD_API_URL──► Python CAD / Streamlit
  PNG → 3MF UI      └─────────────────────┘         (Aiva3D, CadQuery, export 3MF)

                    ┌─────────────────────┐
  Crooijmans        │  web/crooijmans     │──QUOTE_API_URL────────────► Python quote API
  3MF → offerte     └─────────────────────┘         (gewicht, tijd, €, PDF) via `quote_api`
```

**Pilot-volgorde (ideeën Crooijmans):** eerst **calculator** (Crooijmans-app + quote-API), daarna **slimme generatie** (klant PNG→3MF).

## Review-linkjes (klant / Crooijmans) — gratis op Vercel Hobby

Doel: **twee publieke URL’s** delen zodat mensen kunnen klikken en feedback geven. Alleen de **Next.js UI** staat op Vercel (gratis tier); dat kost je niets aan GPU of Python-hosting.

| Wie | Vercel-root | Wat ze zien zonder extra backend |
|-----|-------------|----------------------------------|
| **Klant** | `web/customer` | Logo/kleuren-preview, demo-knop, health |
| **Crooijmans** | `web/crooijmans` | Upload-flow, tabel; zonder `QUOTE_API_URL` → **preview_only** (bestandsgrootte, geen echte €) |

**Stappen:**

1. Wijzigingen **committen en pushen** naar GitHub (`main` of een `preview`-branch).
2. [vercel.com](https://vercel.com) → twee projecten, zelfde repo:
   - Project A → Root Directory: `web/customer`
   - Project B → Root Directory: `web/crooijmans`
3. Optioneel: **Production Branch** op `main`; elke push = nieuwe preview voor reviewers.
4. Deel de URLs (bijv. `https://crooijmans-….vercel.app` en `https://aiva3d-customer-….vercel.app`).

**Echte offerte op de live Crooijmans-URL (nog steeds €0 mogelijk):**

- Tijdens een demo: [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) of vergelijkbaar van je PC naar `uvicorn quote_api.app:app --port 8080`, tunnel-URL in Vercel env **`QUOTE_API_URL`**, daarna redeploy.
- Zonder tunnel: reviewers testen **UI** op Vercel; jij toont **echte cijfers** lokaal (`localhost:3001` + `QUOTE_API_URL=http://127.0.0.1:8080`).

**Privacy:** URLs zijn standaard openbaar op Hobby. Geen geheime data in de repo; geen echte Crooijmans-tarieven in JSON tot je die bewust zet.

## Deploy (eenmalig per app)

### 1. Klant-app

Vercel dashboard → **Add New Project** → import repo → **Root Directory:** `web/customer` → Deploy.

```powershell
cd D:\AI\3d\web\customer
npx vercel login
npx vercel link
npx vercel --prod
```

Health: `https://<klant-project>.vercel.app/api/health`

| Variable | Purpose |
|----------|---------|
| `NEXT_PUBLIC_CAD_API_URL` | Streamlit of toekomstige CAD REST API (3MF-generatie) |

### 2. Crooijmans calculator

**Tweede** Vercel-project, zelfde repo, **Root Directory:** `web/crooijmans`.

```powershell
cd D:\AI\3d\web\crooijmans
npx vercel link
npx vercel --prod
```

Health: `https://<crooijmans-project>.vercel.app/api/health`  
Offerte (stub/proxy): `POST /api/quote` met `multipart/form-data` veld `file`.

| Variable | Purpose |
|----------|---------|
| `QUOTE_API_URL` | Basis-URL Python quote-service (server-side proxy in `/api/quote`) |

**Quote API lokaal:** `uvicorn quote_api.app:app --port 8080` → zet op Crooijmans `.env.local`: `QUOTE_API_URL=http://localhost:8080`.

Zie [QUOTE_API.md](QUOTE_API.md) en [QUOTE_ENGINE.md](QUOTE_ENGINE.md).

Lokaal dev: klant `npm run dev` (8500), Crooijmans `npm run dev` (poort **3001** in package.json).

## Wat draait waar

| Functie | Vercel | Python-backend |
|---------|--------|----------------|
| UI, upload, health | ✅ | — |
| CadQuery / STEP / multi-materiaal 3MF | — | ✅ Aiva3D |
| 3MF volume, printtijd, prijs, PDF | — | ✅ `quote_api` (FastAPI + `print_core`) |
| FreeCAD bridge | — | ✅ `127.0.0.1:8765` (lokaal) |

## CLI op deze machine

Als `vercel login` nog niet gedaan is, deploy alleen via **Vercel dashboard** (GitHub auto-deploy op `main`) of eerst:

```powershell
npx vercel login
```

Anonieme CLI-deploy kan falen (`spawn cmd.exe ENOENT` / build-limiet).

## Lokaal testen

```powershell
cd D:\AI\3d\web\customer
npm install && npm run dev

cd D:\AI\3d\web\crooijmans
npm install && npm run dev
```

Streamlit CAD (apart): `python scripts\start_cad_ui.py` — vaak **8501** of **8502** als 8501 bezet is.
