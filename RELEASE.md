# MandiPulse Portfolio Release Runbook

## Scope

MandiPulse is a clone-runnable mandi decision-intelligence release candidate:

- Crop: Onion
- State: Maharashtra
- Markets: 15 selected mandis
- Forecast horizon: 7 days
- Public surfaces: Streamlit dashboard, FastAPI service, and static Next.js frontend
- Data mode: clone-runnable committed demo bundle; live CEDA refresh is optional

The modeling scope remains intentionally narrow. Future research work such as calendar features,
additional crops/states, and 14/30-day horizons must be promoted in the tracker before
implementation. Split-conformal intervals are already included in the Phase 3 evaluation evidence.

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,post-mvp]"
```

Copy `.env.example` to `.env` and set `CEDA_API_TOKEN` only if you intend to re-fetch raw CEDA data.
The shipped demo does not require secrets.

## Run The Full Pipeline

Run scripts in this order when regenerating local artifacts from the cached raw extract:

```powershell
python scripts\build_clean_onion_panel.py
python scripts\build_feature_table.py
python scripts\train_baselines_7d.py
python scripts\run_baseline_sensitivity_7d.py
python scripts\train_lightgbm_7d.py
python scripts\build_forecast_intervals_7d.py
python scripts\build_recommendations_7d.py
python scripts\run_recommendation_backtest_7d.py
python scripts\run_phase3_evaluation.py
python scripts\build_demo_sample.py
python scripts\build_web_export.py
python scripts\validate_web_export.py
```

Full generated CSVs under `artifacts/`, `data/raw/`, and `data/processed/` are local and ignored.
The intentionally committed demo artifacts are `data/sample/` and `web/public/data/*.json`.

## Run The Surfaces

```powershell
# Streamlit dashboard
streamlit run app\streamlit_app.py

# FastAPI service
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Next.js frontend
cd web
npm install
npm run dev
```

Streamlit opens at `http://localhost:8501`, FastAPI docs at `http://localhost:8000/docs`, and the
Next.js frontend at `http://localhost:3000`.

## Quality Gates

```powershell
ruff check api app src scripts tests
black --check api app src scripts tests
pytest -q

cd web
npm test
npm run build
```

Current gates: 235 Python tests pass at 78.05% coverage against a 70% floor. The web gate runs lint,
typecheck, parity tests, component tests, the static build, and the Playwright browser/accessibility
suite in CI (`.github/workflows/ci.yml`).

## Key Metrics

| Metric | Value |
|---|---|
| Shipped forecaster | moving_average_7d |
| Test MAE | 139.57 INR/quintal |
| Nominal interval coverage (90%) | 86.71% empirical (test, out-of-sample) |
| Recommendation regret@1 | 296.3 INR/qtl vs 370.1 nearest-mandi baseline |
| Beats nearest-mandi baseline | 74.4% of as-of dates |

These are offline decision-support measurements, not profit or production-usage claims. The public
v1 interval has a global width, so its uncertainty penalty is constant across eligible mandis in a
snapshot. The current ranking order is therefore driven by forecast price and transport cost.

## Deployment

Deploy the release branch `finish/portfolio-release` (the tagged release commit).

- Streamlit Cloud: deploy `app/streamlit_app.py` from `finish/portfolio-release`.
- Vercel (optional): deploy with root directory `web`; no environment variables are required.
- Render API (optional): deploy with `requirements-api.txt` and start command
  `uvicorn api.main:app --host 0.0.0.0 --port $PORT`.

After deployment, record the final URLs in the release record in
[docs/portfolio/RELEASE_GATES.md](docs/portfolio/RELEASE_GATES.md).
