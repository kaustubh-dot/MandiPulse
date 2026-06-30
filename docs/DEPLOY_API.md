# MandiPulse API — Deployment Guide (Render)

The FastAPI backend deploys on **Render** (free tier). Vercel is not used for the backend —
the ML deps blow past Vercel's 250 MB bundle cap, and the Render free tier handles cold starts
acceptably for a demo project.

## Local run

```powershell
# Install post-mvp extras once (fastapi, uvicorn, httpx already in .venv if installed)
python -m pip install -e ".[dev,post-mvp]"

# Start with live reload
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000/docs` for interactive Swagger UI.

Endpoints:

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Data and API readiness |
| POST | `/forecast` | 7-day price forecast + uncertainty interval |
| POST | `/recommend` | Transport-adjusted mandi ranking |
| GET | `/docs` | Interactive Swagger UI |
| GET | `/redoc` | ReDoc documentation |

## Render deployment

1. Push this repo to GitHub (already done).
2. Go to [render.com](https://render.com) → **New Web Service** → connect your GitHub repo.
3. Set:
   - **Build command:** `pip install -r requirements-api.txt`
   - **Start command:** `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
   - **Environment:** Python 3.11+
4. Add environment variable (optional):
   - `MANDIPULSE_ALLOWED_ORIGINS` = your Vercel frontend URL (e.g. `https://mandipulse.vercel.app`)
   - Default is `*` — acceptable for a public, read-only, no-secrets demo.
5. Deploy. First cold start on the free tier takes 30–60 seconds; subsequent requests are fast.

The API reads from `data/sample/` (committed bundle) — no pipeline run, no secrets required.

## Runtime dependencies

`requirements-api.txt` contains only the slim serve path:
`fastapi`, `uvicorn[standard]`, `pandas`, `numpy`, `duckdb`, `pydantic`, `pyyaml`, `python-dateutil`.

No lightgbm, shap, mlflow, sklearn, streamlit, or plotly — forecasts are precomputed CSVs.

## CORS

The Next.js frontend is a static export that reads committed JSON, so it does not require the API at
runtime. Keep `MANDIPULSE_ALLOWED_ORIGINS=*` for a public, no-auth demo, or set it to the final Vercel
origin if you later add browser calls to the API.
