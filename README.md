# MandiPulse India

MandiPulse India is a transport-cost-aware mandi decision intelligence system. The MVP is deliberately narrow: an offline Onion/Maharashtra showcase that forecasts a 7-day price, subtracts transparent distance-based transport cost, and ranks nearby mandis.

## Current Implementation Path

The primary mandi data path is AGMARKNET data through the CEDA API.

- Documentation: `https://api.ceda.ashoka.edu.in/documentation/`
- API base: `https://api.ceda.ashoka.edu.in/v1`
- Auth env var: `CEDA_API_TOKEN`
- Fallback: Data.gov.in / AGMARKNET only if registration becomes available later

CEDA uses numeric IDs. Day 0 validation has confirmed Onion (`commodity_id=23`) and Maharashtra (`state_id=27`). The static historical dump has been saved locally, so modeling work no longer depends on a live API key.

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

Processed data is queried through a DuckDB read-layer (`src/mandipulse/data/store.py`) — CSV files remain the on-disk source of truth; DuckDB is the query interface per RULES §Architecture. No `.duckdb` file is committed.

For simple runtime-only installs, such as basic deployment environments:

```powershell
python -m pip install -r requirements.txt
```

Create a local `.env` from `.env.example` and set:

```text
CEDA_API_TOKEN=your_ceda_token
```

Do not commit `.env`, raw datasets, model artifacts, or MLflow runs.

## Day 0 Validation

Run the CEDA validation script before writing full ingestion:

```powershell
python scripts\day0_validate_ceda.py --from-date 2025-03-01 --to-date 2025-03-31
```

The script writes small reproducibility samples under `data/raw/samples/`, which is intentionally ignored by git.

Day 0 is complete when `docs/DATA_SOURCES.md` contains:

- Confirmed auth behavior
- Commodity, state, district, and market ID findings
- Onion/Maharashtra sample status
- Date-range and rate-limit notes
- Sample response paths

## MVP Data Pipeline

The raw CEDA dump has already been captured locally. Re-run only if you need to refresh it:

```powershell
python scripts\fetch_ceda_onion_maharashtra.py --from-date 2020-01-01 --to-date 2026-06-13
```

Build the cleaned panel and 7-day feature table:

```powershell
python scripts\build_clean_onion_panel.py
python scripts\build_feature_table.py
```

Evaluate the first temporal baselines:

```powershell
python scripts\train_baselines_7d.py
```

Run the imputation sensitivity check and first LightGBM pass:

```powershell
python scripts\run_baseline_sensitivity_7d.py
python scripts\train_lightgbm_7d.py
python scripts\build_forecast_intervals_7d.py
```

Current status:

- Best test baseline remains `moving_average_7d` at 139.57 INR/quintal.
- The observed-only sensitivity check did not change the ranking; `moving_average_7d` improved modestly to 133.61 MAE on the stricter subset, so the 3-day forward-fill policy is not the main reason the baseline wins.
- Ridge still underperforms at 224.43 MAE on the full test split.
- The first LightGBM run underperformed the baseline at 188.2 test MAE.
- **Residual-target reformulation (M3-04):** LightGBM retrained on the residual `target - rolling_mean_7` (prediction = `rolling_mean_7 + model(residual)`). Result: test MAE 195.63 — still worse than the baseline (139.57). No promotion. Moving-average remains the shipped forecaster. See `reports/modeling/lightgbm_metrics_7d.md` for the full comparison and Decision section.
- Residual uncertainty intervals are now available for the MVP baseline. The nominal 90% interval calibrated on validation achieved 86.63% empirical coverage on the held-out test split, and latest-per-mandi forecasts are written to `artifacts/forecasts/forecast_outputs_7d.csv`.

Build transport-aware recommendations and run the recommendation quality backtest:

```powershell
python scripts\build_recommendations_7d.py
python scripts\run_recommendation_backtest_7d.py
```

The backtest evaluates ranking quality over the held-out test split using regret@K vs a nearest-mandi baseline. On the current test window, the ranking achieves mean regret@1 of 296.3 INR/qtl vs 370.1 INR/qtl for the nearest-mandi baseline, and beats the baseline on 78.8% of as-of dates. These are offline backtest results on historical data; past performance does not guarantee future results.

The Recommendation page in the Streamlit app surfaces these metrics when the backtest artifact exists.

Raw and processed CSVs are ignored by Git. Reproducible scripts and small reports are committed.

## Project Docs

- Product scope: `docs/PRD.md`
- Architecture: `docs/ARCHITECTURE.md`
- Data-source contract: `docs/DATA_SOURCES.md`
- Data schema: `docs/DATA_SCHEMA.md`
- Implementation plan: `docs/IMPLEMENTATION_PLAN.md`
- Tracker: `docs/TRACKER.md`
- Development rules: `docs/RULES.md`
