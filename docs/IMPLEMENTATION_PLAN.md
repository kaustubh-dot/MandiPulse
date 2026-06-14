# MandiPulse Implementation Plan

## Build Strategy

Build one narrow product slice before adding breadth:

```text
cached CEDA data -> clean panel -> temporal baselines -> LightGBM -> uncertainty -> mandi ranking -> Streamlit demo
```

Current MVP scope:

- Onion only.
- Maharashtra only.
- 15 selected mandis.
- 7-day forecast horizon only.
- Offline/local artifacts.
- Streamlit-only app.

Do not build FastAPI, regime/anomaly detection, live monitoring, 14/30-day forecasts, additional crops, or additional states until this loop is useful and measured.

## Current State

Done:

- CEDA selected as the primary data source.
- CEDA token validated.
- Onion/Maharashtra raw data fetched and cached locally.
- Coverage profile produced.
- Top-15 mandis selected.
- Clean daily panel built.
- Leakage-safe 7-day feature table built.

Next:

1. Create temporal train/validation/test splits.
2. Implement baselines.
3. Save baseline metrics report.
4. Run observed-only/imputation sensitivity and diagnose Ridge underperformance.
5. Train first LightGBM model only after baseline assumptions are stable.

## Active Milestones

### Milestone 1: Data Foundation

Status: Done.

Outputs:

- `scripts/fetch_ceda_onion_maharashtra.py`
- `scripts/profile_onion_maharashtra.py`
- `scripts/build_clean_onion_panel.py`
- `scripts/build_feature_table.py`
- `data/external/mvp_mandis.csv`
- `reports/data_quality/onion_maharashtra_profile.md`
- `reports/data_quality/onion_maharashtra_clean_panel.md`
- `reports/data_quality/onion_maharashtra_feature_table.md`

Generated local data under `data/raw/` and `data/processed/` is ignored and should not be committed.

### Milestone 2: Temporal Baselines

Status: Next.

Deliverables:

- Temporal split utility.
- Seasonal naive baseline.
- Moving-average baseline.
- Ridge or linear baseline.
- Overall and per-mandi metrics.
- Baseline report under `reports/modeling/`.

Definition of done:

- No random train/test split.
- Split dates are written to the report.
- Metrics include MAE, RMSE, sMAPE, and MASE.
- Baseline code can be rerun from the feature table.

### Milestone 3: Main 7-Day Model

Status: Pending.

Deliverables:

- LightGBM training script.
- Model comparison against baselines.
- Saved model artifact.
- Saved feature schema.
- Evaluation report.

Definition of done:

- LightGBM is compared to every baseline.
- Results are reported even if LightGBM underperforms.
- Feature list may include current-day price because it is known on the as-of date; it must exclude future prices and target columns.
- Saved model can be loaded for inference.

### Milestone 4: Uncertainty

Status: Pending.

Deliverables:

- Residual, quantile, or conformal interval method.
- Empirical coverage report.
- Interval-width report.
- Forecast artifact with lower and upper bounds.

Definition of done:

- Every forecast has a lower and upper bound.
- Coverage is measured on held-out data.
- Interval assumptions are documented.

### Milestone 5: Recommendation Engine

Status: Pending.

Deliverables:

- Filled latitude/longitude values in `data/external/mvp_mandis.csv`.
- Haversine distance utility.
- Transport-cost estimator.
- Risk-adjusted ranking function.
- Recommendation report with sensitivity to transport cost.

Definition of done:

- Rankings include forecast price, transport cost, uncertainty penalty, and final score.
- Missing coordinates are handled explicitly.
- The output is framed as decision support, not guaranteed profit.

### Milestone 6: Streamlit MVP

Status: Pending.

Deliverables:

- Data coverage page.
- Forecast page.
- Recommendation page.
- Local artifact loading.
- Demo-ready README instructions.

Definition of done:

- App runs without a live CEDA key.
- User can inspect coverage, forecast, and recommendation in one flow.
- Deferred modules do not appear in navigation.

## Deferred Work

| Item | Earliest point to revisit |
|---|---|
| FastAPI | After Streamlit MVP proves useful |
| Regime/anomaly detection | After 7-day forecast and recommendation work |
| Live monitoring/Evidently | After saved model and dashboard exist |
| 14-day and 30-day horizons | After 7-day performance is understood |
| Tomato or other crops | After Onion/Maharashtra is complete |
| Karnataka or Uttar Pradesh | After Onion/Maharashtra is complete |
| SHAP explanations | After model artifact is stable |
| Docker Compose | After dashboard exists |
| React, mobile, Kubernetes, microservices | Outside MVP |

## Rules While Implementing

- Keep implementation aligned with `TODO.md` and `docs/TRACKER.md`.
- Update reports whenever generated data changes.
- Never commit `.env`, raw data dumps, processed data dumps, MLflow runs, or large artifacts.
- Prefer scripts that can be rerun from scratch.
- Use temporal validation only.
- Keep post-MVP ideas out of active P0 tasks.
