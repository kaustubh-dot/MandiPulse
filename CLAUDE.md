# Project Instructions — MandiPulse India

Transport-cost-aware mandi decision intelligence. The MVP is an **offline Onion/Maharashtra**
showcase: forecast a 7-day price, subtract distance-based transport cost, rank nearby mandis.
`docs/RULES.md` is authoritative — read it before any scope, data, or modeling change.

## Tech Stack
- Python ≥3.11; pandas, numpy, pyarrow, DuckDB
- ML: LightGBM, scikit-learn, SHAP; tracking via MLflow
- UI (planned): Streamlit. Data source: CEDA/AGMARKNET (`CEDA_API_TOKEN`)
- Tooling: ruff + black (line-length 100), pytest, pytest-cov

## Code Style
- Start modules with `from __future__ import annotations`; use modern hints (`str | None`, `list[int]`)
- Prefer dataclasses; raise typed exceptions (e.g. `CedaApiError`), not bare strings
- snake_case files; pipeline scripts named by stage: `fetch_*`, `build_*`, `train_*`
- Never hardcode paths — use `mandipulse.config` helpers and `configs/*.yaml`
- Run `ruff check .` and `black .` before finishing

## Testing
- Run: `pytest` (config: `testpaths=["tests"]`, `pythonpath=["src"]`)
- 84 tests across 7 files; golden fixtures in `tests/golden/`
- Coverage: `pytest --cov=mandipulse`

## Build & Run
- Setup: `python -m pip install -e ".[dev]"`
- Pipeline order: `build_clean_onion_panel.py` → `build_feature_table.py` →
  `train_baselines_7d.py` → `run_baseline_sensitivity_7d.py` → `train_lightgbm_7d.py` →
  `build_forecast_intervals_7d.py` → `build_recommendations_7d.py` →
  `run_recommendation_backtest_7d.py`

## Project Structure
- `src/mandipulse/` — reusable library (config loader, CEDA client)
- `scripts/` — ordered, runnable pipeline stages
- `configs/` — YAML settings (paths/params; never hardcode)
- `docs/` — PRD, ARCHITECTURE, RULES, DATA_SOURCES (source of truth)
- `data/`, `artifacts/`, `reports/` — generated; mostly git-ignored

## Hard Rules (from docs/RULES.md)
- Keep MVP scope: 1 crop (Onion), 1 state (Maharashtra), ~10-15 mandis, 7-day horizon
- Do NOT add FastAPI, React, deep-learning forecasters, or microservices unless explicitly scoped
- Forecasting: temporal split only (never random); never build lag/rolling features from future data
- Always compare against baselines; report MAE, RMSE, sMAPE, MASE; save split dates with every report
- Price unit is INR/quintal; preserve raw data separately from cleaned; document any dropped records
- Recommendations must include transport cost, show alternatives, and carry a risk level + reason
- Never commit `.env`, raw datasets, model artifacts, or MLflow runs

## Git
- Imperative commit subjects ("Fix baseline leakage and prediction artifacts")
- Commit/push only when asked
- NEVER add Claude as a co-author or contributor: omit any `Co-Authored-By: Claude ...`
  trailer from commits and any "Generated with Claude Code" line from PR descriptions