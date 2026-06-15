# MandiPulse v0.1-mvp Release Runbook

## Scope

v0.1-mvp is the frozen Onion/Maharashtra MVP:

- Crop: Onion
- State: Maharashtra
- Markets: 15 mandis
- Forecast horizon: 7 days
- Interface: offline Streamlit dashboard reading local artifacts

This release is feature-frozen. Post-MVP work (FastAPI, extra crops/states, live CEDA, 14/30-day
horizons) requires RULES.md and TRACKER scope promotion before implementation.

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

Copy `.env.example` to `.env` and set `CEDA_API_TOKEN` (needed only for re-fetching raw data).

## Run the Full Pipeline

Run scripts in this order. Each stage reads from the previous stage's output artifact.

```powershell
# Stage 1 — clean daily panel
python scripts\build_clean_onion_panel.py

# Stage 2 — 7-day feature table
python scripts\build_feature_table.py

# Stage 3 — temporal baseline models (moving-average, ridge, seasonal-naive)
python scripts\train_baselines_7d.py

# Stage 4 — LightGBM (comparison only; moving-average remains the shipped forecaster)
python scripts\run_baseline_sensitivity_7d.py
python scripts\train_lightgbm_7d.py

# Stage 5 — residual uncertainty intervals for the MVP baseline
python scripts\build_forecast_intervals_7d.py

# Stage 6 — transport-aware recommendation ranking
python scripts\build_recommendations_7d.py

# Stage 7 — recommendation quality backtest (regret@K)
python scripts\run_recommendation_backtest_7d.py
```

Artifacts land in `artifacts/` and reports in `reports/`. Both are git-ignored.

## Launch the Dashboard

```powershell
streamlit run app\Home.py
```

Open `http://localhost:8501` in a browser. The dashboard reads artifacts from the pipeline output;
run the full pipeline first.

## Run Tests

```powershell
pytest
```

Coverage floor: 69%. 139 tests across 12 test files.

## Key Metrics (v0.1-mvp)

| Metric | Value |
|---|---|
| Shipped forecaster | moving_average_7d |
| Test MAE | 139.57 INR/quintal |
| Nominal interval coverage (90%) | 86.63% empirical |
| Recommendation regret@1 | 296.3 INR/qtl vs 370.1 nearest-mandi baseline |
| Beats nearest-mandi baseline | 78.8% of as-of dates |

## What Is Not in Scope

FastAPI service, live CEDA fetch, 14/30-day horizons, additional crops or states, React frontend,
Kubernetes, regime/anomaly detection. See `docs/TRACKER.md` for the full deferred list.
