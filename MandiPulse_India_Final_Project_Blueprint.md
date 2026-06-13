# MandiPulse India Blueprint

> Current scope: offline Onion/Maharashtra MVP. This file replaces the older broad platform blueprint so the repository has one clear direction.

## Positioning

MandiPulse India is a transport-cost-aware mandi decision intelligence project. The MVP does not try to be a live national platform. It uses a saved local CEDA/AGMARKNET dataset for Maharashtra onion markets, builds a clean daily panel, evaluates 7-day forecasts against baselines, and ranks mandis after transport cost.

## MVP Scope

| Area | Decision |
|---|---|
| Crop | Onion |
| State | Maharashtra |
| Mandis | 15 selected by coverage |
| Data source | CEDA / AGMARKNET static local dump |
| Raw data range requested | 2020-01-01 to 2026-06-13 |
| Raw data returned | 2020-01-01 to 2025-10-30 |
| Forecast horizon | 7 days |
| Product surface | Streamlit only |
| API | Post-MVP |
| Regime/anomaly detection | Post-MVP |
| Live monitoring | Post-MVP |

## Current Artifacts

| Artifact | Path |
|---|---|
| Raw CEDA dump | `data/raw/ceda/onion_maharashtra/onion_maharashtra_prices_raw.csv` |
| Selected mandi list | `data/external/mvp_mandis.csv` |
| Clean panel | `data/processed/onion_maharashtra/clean_mandi_prices.csv` |
| Feature table | `data/processed/onion_maharashtra/feature_table_7d.csv` |
| Raw data profile | `reports/data_quality/onion_maharashtra_profile.md` |
| Clean panel report | `reports/data_quality/onion_maharashtra_clean_panel.md` |
| Feature table report | `reports/data_quality/onion_maharashtra_feature_table.md` |

Raw and processed data are intentionally ignored by Git. Scripts and small reports are committed.

## What Makes It Resume-Worthy

- Real messy CEDA/AGMARKNET data, not a polished Kaggle table.
- Honest missing-data and duplicate handling.
- Leakage-safe lag and rolling features.
- Temporal validation instead of random split.
- Baseline-first modeling discipline.
- A decision layer that subtracts transparent transport cost instead of showing only a point forecast.

## What Is Cut

- No Tomato in MVP.
- No Karnataka or Uttar Pradesh in MVP.
- No 14-day or 30-day forecasts in MVP.
- No FastAPI in MVP.
- No regime/anomaly detection in MVP.
- No Evidently/live drift dashboard in MVP.
- No deep learning or causal claims.

## Next Build Step

Implement temporal splits and baseline metrics on `feature_table_7d.csv`.

The project only earns a LightGBM model after baselines are working and documented.
