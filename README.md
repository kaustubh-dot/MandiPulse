# MandiPulse India

**Transport-cost-aware mandi decision intelligence for Maharashtra onion farmers.**

[![Tests](https://img.shields.io/badge/tests-169%20passed-brightgreen)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-73%25-green)](pyproject.toml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](pyproject.toml)

## Live demos

| Surface | URL | Stack |
|---|---|---|
| Streamlit dashboard | [mandipulse.streamlit.app](https://mandipulse.streamlit.app/) | Python + Streamlit |
| FastAPI service | _optional Render deploy - see [docs/DEPLOY_API.md](docs/DEPLOY_API.md)_ | FastAPI + Render |
| Next.js frontend | _deploy to get URL — see [docs/DEPLOY_FRONTEND.md](docs/DEPLOY_FRONTEND.md)_ | Next.js + Vercel |

---

## The problem

Maharashtra onion farmers choose which mandi (market) to sell at based on word-of-mouth and nearest
distance. They ignore transport cost, forecast uncertainty, and historical ranking quality. A farmer
who drives 40 km to a mandi with a higher forecast price can still lose money if transport costs
exceed the price premium.

MandiPulse forecasts 7-day prices across 15 mandis, subtracts transparent distance-based transport
cost, and ranks mandis by **net expected price** with uncertainty bounds and risk labels.

---

## Honest results

LightGBM was trained and evaluated — it **did not beat the 7-day moving-average baseline** on the
held-out test split. The baseline ships. This is reported transparently.

| Model | Test MAE (INR/qtl) | Ships? |
|---|---|---|
| `moving_average_7d` | **139.57** | Yes |
| `ridge` | 224.43 | No |
| `lightgbm` | 188.2 | No |
| `lightgbm_residual` | 195.63 | No |

Forecast uncertainty intervals (nominal 90%) achieved **86.71% empirical coverage** on the test
split — conservative, safe to show to users.

Recommendation backtest (regret@K vs nearest-mandi baseline, held-out test window):

| Metric | Value |
|---|---|
| Mean regret@1 | 296.3 INR/qtl |
| Nearest-mandi baseline regret | 370.1 INR/qtl |
| Beats nearest-mandi | 78.8% of dates |

---

## What makes this credible

- Temporal train/validation/test splits only; no random split on time-series data.
- Baseline honesty: LightGBM and residual-LightGBM are reported even though they lose.
- Forecasts include uncertainty intervals with measured empirical coverage.
- Recommendations are evaluated with regret@K against a nearest-mandi baseline.
- The demo is clone-runnable from committed `data/sample/` artifacts; no secrets required.
- The Next.js transport-cost ranking is parity-tested against the Python engine within 0.01 INR/qtl.

---

## Architecture

```
CEDA/AGMARKNET cache
       |
 clean daily panel  (15 mandis × 2020–2025)
       |
 leakage-safe features  (lags/rolling/calendar — no future data)
       |
 temporal split  (train/val/test — no random splits)
       |
 baseline comparison  (moving-avg wins)
       |
 residual uncertainty intervals  (validation calibration)
       |
 transport-aware recommendation ranking  (haversine + cost/km)
       |
 regret@K backtest  (vs nearest-mandi baseline)
       |
 Streamlit dashboard  (Data Coverage · Forecast · Recommendation)
       |
 build_web_export.py  (→ web/public/data/*.json)
       |
 Next.js frontend  (Vercel static export — transport-cost slider re-ranks in TS)
```

Data reads go through a DuckDB query layer (`src/mandipulse/data/store.py`). CSV files remain the
on-disk source of truth; DuckDB is the read interface per `docs/RULES.md §Architecture`.

---

## Quickstart (2 minutes, no pipeline run required)

The repo ships a bundled demo dataset (`data/sample/`) so the dashboard works from a fresh clone.

```powershell
git clone https://github.com/kaustubh-dot/MandiPulse.git
cd MandiPulse
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
streamlit run app\streamlit_app.py
```

Open `http://localhost:8501`. All three pages load on the bundled Oct 2025 snapshot — no CEDA key,
no full pipeline run. A banner in the app shows which data source is active.

> **Run the full pipeline** to replace the demo bundle with your own freshly-generated artifacts.
> See [RELEASE.md](RELEASE.md) for the full pipeline runbook.

---

## API (FastAPI)

A REST API exposes the same forecasts and recommendations as a separate demo surface.

```powershell
# Local run
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
# Swagger UI at http://localhost:8000/docs
```

| Endpoint | Description |
|---|---|
| `GET /health` | Data and API readiness |
| `POST /forecast` | 7-day price + uncertainty interval for a mandi |
| `POST /recommend` | Transport-adjusted mandi ranking |

All three endpoints run over the same committed `data/sample/` bundle — no pipeline run required.
See [docs/DEPLOY_API.md](docs/DEPLOY_API.md) for Render deployment instructions.

---

## Frontend (Next.js)

The static frontend reads committed JSON from `web/public/data/` and re-ranks recommendations in
the browser as transport cost changes.

```powershell
python scripts\build_web_export.py
cd web
npm install
npm test
npm run build
npm run dev
```

Deploy it on Vercel with **Root Directory** set to `web`. No environment variables are required.

---

## Deploy in 3 steps

1. Fork this repo (or push to your GitHub account).
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with GitHub, click **New app**.
3. Set: **Repository** = this repo, **Branch** = `main`, **Main file** = `app/streamlit_app.py`.

No secrets required. The app runs entirely on the committed demo bundle.

Paste the resulting URL in the badge at the top of this README.

---

## Run the full pipeline

If you want to generate fresh artifacts from the raw CEDA data:

```powershell
python scripts\build_clean_onion_panel.py
python scripts\build_feature_table.py
python scripts\train_baselines_7d.py
python scripts\run_baseline_sensitivity_7d.py
python scripts\train_lightgbm_7d.py
python scripts\build_forecast_intervals_7d.py
python scripts\build_recommendations_7d.py
python scripts\run_recommendation_backtest_7d.py
python scripts\build_demo_sample.py
python scripts\build_web_export.py
```

See [RELEASE.md](RELEASE.md) for the full runbook with expected outputs.

---

## Tests

```powershell
pytest
```

169 tests, 73% coverage, `--cov-fail-under=70`. Includes pipeline smoke tests, leakage guards,
temporal-split validation, recommendation scoring, and data-store parity tests.

Web gates:

```powershell
cd web
npm test
npm run build
```

GitHub Actions runs the Python lint/format/test gate and the web parity/build gate on `main`.

---

## Project docs

| Doc | Contents |
|---|---|
| [RELEASE.md](RELEASE.md) | Full pipeline runbook, key metrics, deploy instructions |
| [docs/RULES.md](docs/RULES.md) | Development rules (authoritative scope guard) |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, storage decision, data flow |
| [docs/TRACKER.md](docs/TRACKER.md) | Milestone history; v0.1-mvp is frozen |
| [docs/PRD.md](docs/PRD.md) | Product scope and requirements |
| [reports/modeling/](reports/modeling/) | Committed model and evaluation reports |

---

## Setup for data ingestion (optional)

The static historical dump is already used for all modeling. Re-fetch only if you need to refresh:

```powershell
python scripts\fetch_ceda_onion_maharashtra.py --from-date 2020-01-01 --to-date 2026-06-13
```

Requires a CEDA API token — create `.env` from `.env.example` and set `CEDA_API_TOKEN`.
