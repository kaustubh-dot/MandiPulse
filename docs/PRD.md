# MandiPulse India PRD

## Project Overview

**MandiPulse India** is a transport-cost-aware mandi decision intelligence system for Indian agricultural markets. It forecasts crop prices across selected mandis, estimates uncertainty intervals, detects volatile or abnormal market regimes, and recommends where a farmer or FPO should sell after estimated transport cost.

The project is designed as a resume-worthy end-to-end Data Science / ML Engineering system, not a notebook-only modeling exercise.

## Problem Statement

Farmers, FPOs, traders, and market analysts often need to decide:

- Which mandi is likely to offer the best net price soon.
- Whether a higher price at another mandi is still profitable after transport cost.
- Whether the current market is normal, volatile, or abnormal.
- How much confidence to place in a forecast.
- Why the system is recommending a specific mandi.

A single crop price prediction is not enough. The useful decision is:

> Where should I sell, when should I sell, how confident is the system, and why?

## Target Users

| User | Need | MVP Support |
|---|---|---|
| Small farmer | Understand nearby mandi selling options | Ranked mandi recommendation after transport cost |
| Farmer Producer Organization | Compare multiple mandis for aggregated sale | Candidate mandi table, risk-adjusted net price |
| Market analyst | Monitor volatility and anomalies | Regime labels, anomaly timeline, forecast intervals |
| Portfolio reviewer / interviewer | Evaluate ML engineering ability | End-to-end pipeline, FastAPI, Streamlit, MLflow, Docker, monitoring |
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
| Usually notebook-only | Ships API, dashboard, MLflow tracking, Docker, monitoring |

## MVP Scope

| Area | MVP Decision |
|---|---|
| Crops | 2 crops: Onion and Tomato unless EDA proves poor data quality |
| States | 3 states: Maharashtra, Karnataka, Uttar Pradesh unless EDA requires substitution |
| Mandis | 50-100 mandis total |
| Forecast horizons | 7, 14, and 30 days |
| Validation | Temporal split or rolling/walk-forward validation |
| Forecast output | Forecast price plus uncertainty interval |
| Recommendation | Rank mandis by expected net price after transport cost and uncertainty penalty |
| Regime detection | Normal, volatile, crisis/anomaly labels |
| Backend | FastAPI |
| Dashboard | Streamlit |
| Experiment tracking | MLflow |
| Deployment | Docker and Docker Compose |
| Monitoring | Data freshness, missing values, drift indicator, recent forecast error |

## Non-Goals

- No Kubernetes in MVP.
- No React frontend in MVP.
- No mobile app or WhatsApp bot in MVP.
- No deep learning forecasting models in MVP.
- No Temporal Fusion Transformer or large neural forecasting stack.
- No 500+ mandi network in MVP.
- No unnecessary microservices.
- No causal claims unless an optional future research module is explicitly implemented and validated.
- No production-grade route optimization.
- No real-time trading or arbitrage execution system.

## User Stories

| ID | User Story | Priority | Acceptance Criteria |
|---|---|---:|---|
| US-01 | As a user, I can select crop, state, mandi, and horizon to see a forecast. | P0 | Forecast includes price, lower bound, upper bound, confidence level, and regime label. |
| US-02 | As a farmer/FPO, I can enter location, crop, quantity, candidate states, and horizon to get ranked mandis. | P0 | Output includes recommended mandi, transport cost, expected net price, risk level, and alternatives. |
| US-03 | As a market analyst, I can see whether a mandi is normal, volatile, or in crisis/anomaly. | P0 | Dashboard explains the regime with a simple reason such as high rolling volatility. |
| US-04 | As a reviewer, I can inspect baseline vs main model metrics. | P0 | Metrics compare seasonal naive, moving average, linear/Ridge, and LightGBM/CatBoost. |
| US-05 | As a user, I can see uncertainty bands on forecasts. | P0 | Forecast charts show calibrated intervals for 7/14/30-day horizons. |
| US-06 | As a maintainer, I can reproduce experiments. | P0 | MLflow logs parameters, metrics, model artifacts, and run metadata. |
| US-07 | As an operator, I can check if data is fresh and the API is healthy. | P0 | `/health` and `/metrics` provide current status. |
| US-08 | As a reviewer, I can understand why a forecast moved. | P1 | SHAP or model driver summary appears for selected forecasts. |
| US-09 | As a user, I can inspect similar historical market days. | P2 | Marked as optional/future unless core MVP is complete. |
| US-10 | As an analyst, I can inspect arbitrage-like gaps between nearby mandis. | P2 | Marked as optional/future and framed carefully as opportunity detection, not guaranteed profit. |

## Core Features

| Feature | Description | Priority |
|---|---|---:|
| Data ingestion | Collect mandi price data for selected crops, states, and mandis. | P0 |
| Data cleaning | Normalize names, units, dates, duplicates, missing values. | P0 |
| Feature engineering | Lag, rolling, returns, volatility, calendar, arrival, optional weather and distance features. | P0 |
| Temporal validation | Train on older dates and validate/test on later dates. | P0 |
| Baselines | Seasonal naive, moving average, linear/Ridge. | P0 |
| Main model | LightGBM or CatBoost. | P0 |
| Uncertainty intervals | Conformal prediction, quantile regression, or residual intervals. | P0 |
| Recommendation engine | Net expected price after transport cost and uncertainty penalty. | P0 |
| Regime/anomaly detection | Rolling volatility, z-score, or Isolation Forest based labels. | P0 |
| FastAPI service | Health, forecast, recommend, regime, metrics endpoints. | P0 |
| Streamlit dashboard | Overview, forecast, recommendation, regime/anomaly, monitoring pages. | P0 |
| MLflow tracking | Experiments, metrics, parameters, model artifacts. | P0 |
| Monitoring | Data quality, freshness, drift, recent error, inference success. | P0 |
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
| API latency | Reasonable local demo response time |
| Data freshness | Latest loaded market date is visible |
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
| Anomaly detection has no labels | Hard to validate | Use rule-based detection plus event annotation where available |
| Scope creep into causal inference or arbitrage | Project becomes unfinished | Keep advanced modules as P2/future until MVP is complete |

## Final Resume Positioning

**MandiPulse India - Agricultural Market Intelligence Platform**  
Built an end-to-end mandi decision intelligence system for Indian agricultural markets using temporal price forecasting, sparse-data imputation, conformal prediction intervals, regime/anomaly detection, and transport-cost-aware mandi recommendation; deployed with FastAPI, Streamlit, MLflow, Docker, and monitoring.

## MVP Acceptance Checklist

- [ ] Tracks 2 crops across 3 states and 50-100 mandis.
- [ ] Uses temporal validation only.
- [ ] Compares against at least three baselines.
- [ ] Produces 7/14/30-day forecasts.
- [ ] Produces uncertainty intervals and reports coverage.
- [ ] Recommends mandis after transport cost and uncertainty penalty.
- [ ] Detects normal, volatile, and crisis/anomaly regimes.
- [ ] Serves FastAPI endpoints.
- [ ] Provides Streamlit dashboard pages.
- [ ] Logs experiments and artifacts with MLflow.
- [ ] Runs with Docker Compose.
- [ ] Includes basic monitoring and tests.

