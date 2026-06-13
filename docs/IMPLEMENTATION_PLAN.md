# MandiPulse India Implementation Plan

## Build Strategy

Build the system in narrow, working slices. The core path is:

```text
static CEDA data grab -> EDA -> clean panel -> baselines -> 7-day model -> recommendation -> Streamlit demo
```

The narrowed MVP is Onion in Maharashtra, top 10-15 mandis, 7-day horizon, and a single Streamlit app. Do not build FastAPI, regime/anomaly detection, advanced monitoring, 14/30-day horizons, or additional crops/states until this path works end to end.

## 8-Week Roadmap

### Week 1: Project Setup + Data Foundation

Goal: create the project skeleton and establish a clean initial dataset.

Deliverables:

- Repository folder structure.
- Python environment and dependency file.
- Initial data source decision.
- Raw data ingestion for selected crops/states.
- Initial cleaned data layer.
- Data dictionary draft.
- EDA notebook for coverage, missingness, outliers, and candidate mandis.

Dependencies:

- Access to mandi price data.
- Decision on final MVP crops/states after initial data quality check.

Definition of done:

- [ ] Raw records are reproducible from documented source.
- [ ] Clean table exists for at least the candidate MVP scope.
- [ ] EDA identifies 10-15 usable Maharashtra onion mandis or flags data quality risk.
- [ ] Missingness and duplicate patterns are documented.

### Week 2: Data Cleaning + Feature Engineering

Goal: produce a model-ready feature table.

Deliverables:

- Name normalization for crops, states, districts, mandis.
- Unit normalization to INR/quintal.
- Duplicate handling.
- Missing data flags and handling strategy.
- Crop-mandi-date panel.
- Lag features for 1, 3, 7, 14, 30 days.
- Rolling mean, median, standard deviation, returns, volatility.
- Calendar features.
- Data validation checks.

Dependencies:

- Week 1 clean raw/processed data.
- Mandi metadata with IDs.

Definition of done:

- [ ] Feature table is reproducible.
- [ ] No future data leakage in features.
- [ ] Rows with insufficient history are flagged or excluded.
- [ ] Validation checks pass or generate documented failures.
- [ ] Feature table supports the 7-day target.

### Week 3: Baseline Forecasting

Goal: establish honest baselines using temporal validation.

Deliverables:

- Seasonal naive baseline.
- Moving average baseline.
- Linear/Ridge baseline.
- Temporal split or rolling backtest utility.
- Metrics report: MAE, RMSE, sMAPE, MASE.
- Baseline performance summary by crop, horizon, and state/mandi group.

Dependencies:

- Week 2 feature table.

Definition of done:

- [ ] No random train-test split is used.
- [ ] Baseline metrics are logged and saved.
- [ ] Baseline code is tested on small sample data.
- [ ] Weak/strong horizon performance is documented.

### Week 4: Main Model + MLflow

Goal: train the primary model and track experiments.

Deliverables:

- LightGBM training pipeline as the primary MVP model.
- CatBoost comparison only if time allows after LightGBM works.
- Hyperparameter configuration.
- Baseline vs main model comparison.
- MLflow experiment logging.
- Best model artifact saved.
- Feature schema saved.
- Model evaluation report.

Dependencies:

- Week 3 temporal validation and baseline metrics.

Definition of done:

- [ ] Main model is compared to all baselines.
- [ ] MLflow logs params, metrics, artifacts, and run metadata.
- [ ] Saved model can be reloaded and used for inference.
- [ ] Model artifact includes feature order/schema.
- [ ] Results are credible even if not perfect.

### Week 5: Uncertainty + Regime Detection

Goal: make forecasts uncertainty-aware and market-regime-aware.

Deliverables:

- Conformal, quantile, or residual interval implementation.
- Empirical coverage evaluation.
- Interval width report.
- Regime/anomaly detection logic.
- Regime labels: normal, volatile, crisis/anomaly.
- Volatility/regime report.

Dependencies:

- Week 4 model artifacts.
- Backtest predictions.

Definition of done:

- [ ] Every forecast can return lower and upper bounds.
- [ ] Coverage is measured on validation/test period.
- [ ] Regime label has a human-readable reason.
- [ ] Anomaly logic is documented and tested.

### Week 6: Recommendation Engine

Goal: convert forecasts into transport-cost-aware mandi recommendations.

Deliverables:

- Transport cost estimator.
- Candidate mandi filtering.
- Net expected price calculation.
- Uncertainty penalty.
- Risk level assignment.
- Ranked mandi output.
- Recommendation regret metrics.
- Recommendation logic ready for API.

Dependencies:

- Week 5 forecast intervals.
- Mandi metadata with coordinates.

Definition of done:

- [ ] Recommendation output ranks mandis deterministically.
- [ ] Formula includes forecast price, transport cost, and uncertainty penalty.
- [ ] Regret@K or missed profit is evaluated.
- [ ] Tests cover edge cases such as missing coordinates and no candidates.

### Week 7: FastAPI + Dashboard

Goal: create the usable decision product.

Deliverables:

- FastAPI app.
- Endpoints: `/health`, `/forecast`, `/recommend`, `/regime`, `/metrics`.
- Pydantic request and response models.
- Streamlit pages:
  - Overview.
  - Forecast.
  - Recommendation.
  - Regime / Anomaly.
  - Monitoring.
- Forecast charts with confidence bands.
- Recommendation table and map.
- Basic monitoring page.

Dependencies:

- Week 6 recommendation engine.
- Model and data artifacts.

Definition of done:

- [ ] Dashboard can complete the demo flow.
- [ ] API responses match `docs/API_SPEC.md`.
- [ ] Forecast and recommendation are served from model artifacts.
- [ ] Errors are user-friendly.
- [ ] API integration tests cover core endpoints.

### Week 8: Docker + Tests + Documentation

Goal: make the project resume-ready and reproducible.

Deliverables:

- Dockerfile.
- Docker Compose setup.
- Unit tests for data, features, model, uncertainty, recommendation, regime.
- Integration tests for API.
- README.
- Model card.
- Final architecture diagram.
- Demo screenshots/GIF or video script.
- Final cleanup of docs and tracker.

Dependencies:

- Week 7 working app.

Definition of done:

- [ ] Docker Compose starts the API and dashboard.
- [ ] Test suite passes locally.
- [ ] README explains the decision intelligence framing.
- [ ] Demo flow is recorded or documented.
- [ ] Raw data, secrets, large models, and MLflow runs are not committed.

## What to Build First in the First 7 Days

### Day 0

- Get a CEDA API bearer token and store it locally as `CEDA_API_TOKEN`.
- Run `python scripts\day0_validate_ceda.py --from-date 2025-03-01 --to-date 2025-03-31`.
- Use curl or Postman only for debugging failed CEDA endpoint calls.
- Document response format, ID lookup behavior, date-range behavior, and any quirks.
- Confirm Onion/Maharashtra data availability and record Tomato/other states only as deferred scope.
- Estimate historical date range coverage.
- Save one small sample response under `data/raw/samples/`.
- Update `docs/DATA_SOURCES.md` with confirmed fields, lookup IDs, date-range behavior, sample path, and quirks.
- If CEDA is inaccessible or severely rate-limited, try the Data.gov.in fallback if registration works; otherwise activate the Kaggle/bootstrap fallback plan and document.
- Stop before building full ingestion.

### Day 1

- Run the narrowed data grab:
  `python scripts\fetch_ceda_onion_maharashtra.py --from-date 2020-01-01 --to-date 2026-06-13`
- Save raw responses and flattened CSV under `data/raw/ceda/onion_maharashtra/`.
- Verify row count, market count, and date range in `fetch_summary.json`.

### Day 2

- Load the flattened raw CSV.
- Compute active days, missing days, and invalid price rows by market.
- Select candidate top 10-15 mandis by non-empty price coverage and arrival/record volume.

### Day 3

- Normalize dates, names, prices, and market IDs.
- Create the clean Onion/Maharashtra crop-mandi-date panel.
- Apply minimal quality rules: modal price positive, min <= modal <= max, duplicate handling.

### Day 4

- Build strict temporal splits.
- Implement 7-day naive/seasonal naive and moving-average baselines.
- Report MAE, RMSE, sMAPE, and MASE by mandi and overall.

### Day 5

- Build lag and rolling features using only data available up to date `t`.
- Train a basic global LightGBM model for the 7-day horizon.
- Compare honestly against baselines. If LightGBM loses, document why instead of hiding it.

### Day 6

- Implement the transport-cost ranking function using haversine distance.
- Add crude mandi latitude/longitude metadata for the selected 10-15 mandis.
- Test that the recommendation does not choose distant markets for tiny gains.

### Day 7

- Build the first barebones Streamlit app.
- Show data coverage, selected mandi forecast, baseline comparison, and top-3 net-price recommendation.
- Produce a blunt viability note: what worked, what failed, and what was cut.

## Task Dependencies

| Task | Depends On |
|---|---|
| Feature table | Cleaned crop-mandi-date panel |
| Baseline models | Feature table with horizon targets |
| Main model | Baseline evaluation utilities |
| Uncertainty intervals | Backtest predictions from model |
| Recommendation engine | Forecasts, intervals, mandi coordinates |
| Dashboard | Saved model artifacts and local feature outputs |
| API | Post-MVP only |
| Docker Compose | Post-MVP only |
| Final README | Working demo and results |

## What to Postpone

| Item | Reason |
|---|---|
| Causal inference | Optional research module; high risk of overclaiming |
| Arbitrage detection | P2 after recommendation engine works |
| Price propagation graph | P2; must avoid causal wording |
| Similar historical days | Useful later, not required for MVP |
| PostgreSQL | Optional unless deployment requires server DB |
| FastAPI | Deferred until Streamlit MVP proves useful |
| Regime/anomaly detection | Distraction until the core decision engine works |
| 14-day and 30-day forecasts | Deferred until 7-day performance is understood |
| Tomato/Karnataka/Uttar Pradesh | Deferred until Onion/Maharashtra is complete |
| Live monitoring/Evidently | Deferred; use static data quality reports first |
| HMM regime model | Optional after simple volatility/z-score approach |
| ARIMA/SARIMA for all mandis | Too time-consuming; optional for selected diagnostics |
| Deep learning forecasting | Too heavy and outside blueprint |
| React frontend | Outside MVP |
| Kubernetes | Outside MVP |

## Cross-Phase Rules

- Update `docs/TRACKER.md` after completing meaningful tasks.
- Keep README and docs aligned with actual implementation.
- Log assumptions in config or docs, not only code comments.
- Every model result must identify validation split and horizon.
- Every recommendation must include transport cost and uncertainty.
- Every demo screenshot should reinforce "mandi decision intelligence."
