# MandiPulse India PRD

## Project Overview

**MandiPulse India** is a transport-cost-aware mandi decision intelligence system for Indian agricultural markets. The MVP is an offline, static-data showcase for Onion mandis in Maharashtra: forecast the 7-day price, subtract distance-based transport cost, and recommend the best nearby mandi.

The project is designed as a resume-worthy end-to-end Data Science / ML Engineering system, not a notebook-only modeling exercise.

## Problem Statement

Farmers, FPOs, traders, and market analysts often need to decide:

- Which mandi is likely to offer the best net price soon.
- Whether a higher price at another mandi is still profitable after transport cost.
- How much confidence to place in a forecast.
- Why the system is recommending a specific mandi.

A single crop price prediction is not enough. The useful decision is:

> Where should I sell, when should I sell, how confident is the system, and why?

## Target Users

| User | Need | MVP Support |
|---|---|---|
| Small farmer | Understand nearby mandi selling options | Ranked mandi recommendation after transport cost |
| Farmer Producer Organization | Compare multiple mandis for aggregated sale | Candidate mandi table, risk-adjusted net price |
| Market analyst | Compare spreads across selected onion mandis | Forecast table, net-price ranking, coverage diagnostics |
| Portfolio reviewer / interviewer | Evaluate ML engineering ability | Real data pipeline, temporal validation, recommendation logic, Streamlit demo |
| Project maintainer | Reproduce and extend the system | Documented schemas, API contract, tests, tracker |

## Why This Is Not Generic Crop Price Prediction

| Generic Crop Price Prediction | MandiPulse India |
|---|---|
| Predicts one price | Forecasts prices across many mandis |
| Often uses random train-test split | Uses temporal validation and backtesting |
| Returns a point estimate | Returns uncertainty-aware intervals |
| Stops at model output | Converts forecasts into mandi recommendations |
| Ignores travel cost | Estimates net expected price after transport cost |
| Has weak business metric | Evaluates regret and top-k recommendation quality |
| Usually notebook-only | Ships a reproducible offline data product and dashboard |

## MVP Scope

| Area | MVP Decision |
|---|---|
| Crops | 1 crop: Onion |
| States | 1 state: Maharashtra |
| Mandis | Top 10-15 mandis selected by coverage and volume |
| Forecast horizons | 7 days only |
| Validation | Temporal split or rolling/walk-forward validation |
| Forecast output | Forecast price plus uncertainty interval |
| Recommendation | Rank mandis by expected net price after transport cost and uncertainty penalty |
| Regime detection | Deferred |
| Backend | Deferred; no FastAPI in MVP |
| Dashboard | Single Streamlit app loading static data/model artifacts |
| Experiment tracking | MLflow |
| Deployment | Local Streamlit demo; Docker is post-MVP |
| Monitoring | Data coverage and model metrics reports only |

## Non-Goals

- No Kubernetes in MVP.
- No React frontend in MVP.
- No mobile app or WhatsApp bot in MVP.
- No deep learning forecasting models in MVP.
- No Temporal Fusion Transformer or large neural forecasting stack.
- No 500+ mandi network in MVP.
- No unnecessary microservices.
- No FastAPI service in the narrowed MVP.
- No regime/anomaly detection in the narrowed MVP.
- No live monitoring or drift platform in the narrowed MVP.
- No Tomato/Karnataka/Uttar Pradesh until Onion/Maharashtra works end to end.
- No 14-day or 30-day forecasts until the 7-day system beats or clearly explains baseline performance.
- No causal claims unless an optional future research module is explicitly implemented and validated.
- No production-grade route optimization.
- No real-time trading or arbitrage execution system.

## User Stories

| ID | User Story | Priority | Acceptance Criteria |
|---|---|---:|---|
| US-01 | As a user, I can select a Maharashtra onion mandi to see a 7-day forecast. | P0 | Forecast includes price, lower bound, upper bound, and confidence level. |
| US-02 | As a farmer/FPO, I can enter location, crop, quantity, candidate states, and horizon to get ranked mandis. | P0 | Output includes recommended mandi, transport cost, expected net price, risk level, and alternatives. |
| US-03 | As a reviewer, I can inspect data coverage for selected mandis. | P0 | Dashboard/report shows missingness, active days, and excluded mandis. |
| US-04 | As a reviewer, I can inspect baseline vs main model metrics. | P0 | Metrics compare seasonal naive, moving average, linear/Ridge, and the primary LightGBM model. CatBoost is P1 comparison only. |
| US-05 | As a user, I can see uncertainty bands on forecasts. | P0 | Forecast charts show calibrated intervals for the 7-day horizon. |
| US-06 | As a maintainer, I can reproduce experiments. | P0 | MLflow logs parameters, metrics, model artifacts, and run metadata. |
| US-07 | As a reviewer, I can run the Streamlit demo from saved local artifacts. | P0 | The app does not need a live API key. |
| US-08 | As a reviewer, I can understand why a forecast moved. | P1 | SHAP or model driver summary appears for selected forecasts. |
| US-09 | As a user, I can inspect similar historical market days. | P2 | Marked as optional/future unless core MVP is complete. |
| US-10 | As an analyst, I can inspect arbitrage-like gaps between nearby mandis. | P2 | Marked as optional/future and framed carefully as opportunity detection, not guaranteed profit. |

## Core Features

| Feature | Description | Priority |
|---|---|---:|
| Data ingestion | Collect mandi price data for selected crops, states, and mandis. | P0 |
| Data cleaning | Normalize names, units, dates, duplicates, missing values. | P0 |
| Feature engineering | Lag, rolling, returns, volatility, calendar, arrival, and distance features. Weather is P1 and must not block MVP. | P0 |
| Temporal validation | Train on older dates and validate/test on later dates. | P0 |
| Baselines | Seasonal naive, moving average, linear/Ridge. | P0 |
| Main model | LightGBM as the first primary model. CatBoost is P1 comparison only. | P0 |
| Uncertainty intervals | Conformal prediction, quantile regression, or residual intervals. | P0 |
| Recommendation engine | Net expected price after transport cost and uncertainty penalty. | P0 |
| Regime/anomaly detection | Deferred until the core decision engine works. | P2 |
| FastAPI service | Deferred until after the Streamlit MVP is useful. | P1 |
| Streamlit dashboard | Data coverage, forecast, recommendation, and metrics views. | P0 |
| MLflow tracking | Experiments, metrics, parameters, model artifacts. | P0 |
| Monitoring | Static data quality and backtest reports. | P1 |
| Explainability | SHAP global and local explanations plus human-readable drivers. | P1 |

## Success Metrics

### Forecasting

| Metric | Goal |
|---|---|
| MAE | Lower than seasonal naive and moving average baselines |
| RMSE | Reported for comparison; not optimized alone |
| sMAPE | Stable percentage-style metric across mandis |
| MASE | Better than naive baseline where possible |

### Uncertainty

| Metric | Goal |
|---|---|
| Empirical coverage | Close to configured confidence level, such as 90% |
| Interval width | Narrow enough to be useful, not only conservative |
| Pinball loss | Used if quantile models are implemented |

### Recommendation

| Metric | Goal |
|---|---|
| Regret@K | Lower regret than nearest mandi baseline |
| Top-k accuracy | Recommended mandi appears near best actual net price |
| Average missed profit | Reported in INR per quintal |
| Net price improvement | Demonstrates value of decision layer |

### System

| Metric | Goal |
|---|---|
| App latency | Reasonable local demo response time |
| Data range | Latest loaded market date is visible |
| Missing data percentage | Tracked by crop, state, mandi |
| Inference success rate | Failures are logged and surfaced |

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Mandi data is sparse or inconsistent | Weak model quality | Start with EDA, restrict to active mandis, document missingness |
| Weather data is hard to align | Delays MVP | Treat weather as optional if core price/arrival features are sufficient |
| Forecasts underperform baselines | Weak story | Keep baselines honest, analyze by regime, emphasize decision metrics |
| Recommendation depends on rough transport cost | Overclaiming | Use transparent cost assumptions and sensitivity in dashboard |
| Uncertainty intervals are too wide | Poor usability | Report empirical coverage and interval width together |
| API key expires before full raw pull | Blocks refreshes | Fetch static historical data immediately and build offline |
| Scope creep into causal inference or arbitrage | Project becomes unfinished | Keep advanced modules as P2/future until MVP is complete |

## Final Resume Positioning

**MandiPulse India - Agricultural Market Intelligence Platform**  
Built an offline mandi decision intelligence system for Maharashtra onion markets using CEDA/AGMARKNET data, temporal validation, baseline-vs-LightGBM forecasting, uncertainty intervals, and distance-based transport-cost ranking in a Streamlit dashboard.

## MVP Acceptance Checklist

- [ ] Tracks Onion across the top 10-15 Maharashtra mandis.
- [ ] Uses temporal validation only.
- [ ] Compares against at least three baselines.
- [ ] Produces 7-day forecasts.
- [ ] Produces uncertainty intervals and reports coverage.
- [ ] Recommends mandis after transport cost and uncertainty penalty.
- [ ] Provides a Streamlit dashboard from static local artifacts.
- [ ] Logs experiments and artifacts with MLflow.
- [ ] Includes data coverage reports and tests for the core pipeline.
