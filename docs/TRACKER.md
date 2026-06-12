# MandiPulse India Tracker

## Label Legend

### Priority

| Label | Meaning |
|---|---|
| P0 mandatory | Required for MVP |
| P1 important | Strongly improves project quality |
| P2 optional | Future or advanced module |

### Status

| Label | Meaning |
|---|---|
| Not started | Work has not begun |
| In progress | Currently being worked on |
| Done | Completed and verified |
| Blocked | Cannot proceed without dependency or decision |

## Current Kanban

### Backlog

| ID | Priority | Status | Task |
|---|---|---|---|
| BL-01 | P2 optional | Not started | Similar historical market days module |
| BL-02 | P2 optional | Not started | Arbitrage opportunity detection |
| BL-03 | P2 optional | Not started | Predictive price transmission graph |
| BL-04 | P2 optional | Not started | Causal weather shock research module |
| BL-05 | P2 optional | Not started | PostgreSQL deployment option |

### Todo

| ID | Priority | Status | Task |
|---|---|---|---|
| TD-01 | P0 mandatory | Not started | Create repository structure |
| TD-02 | P0 mandatory | Not started | Set up Python environment and dependency file |
| TD-03 | P0 mandatory | Not started | Confirm data source and ingestion method |
| TD-04 | P0 mandatory | Not started | Build raw data ingestion |
| TD-05 | P0 mandatory | Not started | Build cleaned mandi price table |
| TD-06 | P0 mandatory | Not started | Create initial EDA notebook |
| TD-07 | P0 mandatory | Not started | Finalize MVP crop/state/mandi list |

### In Progress

| ID | Priority | Status | Task |
|---|---|---|---|
| - | - | - | No implementation tasks in progress |

### Done

| ID | Priority | Status | Task |
|---|---|---|---|
| DN-01 | P0 mandatory | Done | Final project blueprint created |
| DN-02 | P0 mandatory | Done | Planning documentation foundation created |

### Blocked

| ID | Priority | Status | Task | Blocker |
|---|---|---|---|---|
| - | - | - | No blocked tasks | - |

## Week 1 Tasks: Project Setup + Data Foundation

| ID | Priority | Status | Task | Depends On |
|---|---|---|---|---|
| W1-01 | P0 mandatory | Not started | Create project folder structure | None |
| W1-02 | P0 mandatory | Not started | Add dependency/config skeleton | W1-01 |
| W1-03 | P0 mandatory | Not started | Add `.gitignore` rules for data, secrets, artifacts, MLflow runs | W1-01 |
| W1-04 | P0 mandatory | Not started | Confirm mandi data source | None |
| W1-05 | P0 mandatory | Not started | Ingest raw mandi data sample | W1-04 |
| W1-06 | P0 mandatory | Not started | Normalize initial dates and basic fields | W1-05 |
| W1-07 | P0 mandatory | Not started | Create raw and cleaned data storage convention | W1-05 |
| W1-08 | P0 mandatory | Not started | Start EDA notebook for coverage and quality | W1-06 |
| W1-09 | P0 mandatory | Not started | Select 2 crops, 3 states, 50-100 mandis based on EDA | W1-08 |
| W1-10 | P1 important | Not started | Draft data dictionary | W1-06 |

## Week 2 Tasks: Data Cleaning + Feature Engineering

| ID | Priority | Status | Task | Depends On |
|---|---|---|---|---|
| W2-01 | P0 mandatory | Not started | Normalize crop, state, district, mandi names | W1-09 |
| W2-02 | P0 mandatory | Not started | Convert prices to INR/quintal | W2-01 |
| W2-03 | P0 mandatory | Not started | Handle duplicate crop-mandi-date records | W2-01 |
| W2-04 | P0 mandatory | Not started | Implement missing data flags | W2-01 |
| W2-05 | P0 mandatory | Not started | Build crop-mandi-date panel | W2-02 |
| W2-06 | P0 mandatory | Not started | Add lag features: 1, 3, 7, 14, 30 days | W2-05 |
| W2-07 | P0 mandatory | Not started | Add rolling mean, median, std, returns, volatility | W2-06 |
| W2-08 | P0 mandatory | Not started | Add calendar features | W2-05 |
| W2-09 | P0 mandatory | Not started | Add validation checks | W2-05 |
| W2-10 | P1 important | Not started | Add optional weather features if feasible | W2-05 |

## Week 3 Tasks: Baseline Forecasting

| ID | Priority | Status | Task | Depends On |
|---|---|---|---|---|
| W3-01 | P0 mandatory | Not started | Create temporal split utility | W2-09 |
| W3-02 | P0 mandatory | Not started | Implement seasonal naive baseline | W3-01 |
| W3-03 | P0 mandatory | Not started | Implement moving average baseline | W3-01 |
| W3-04 | P0 mandatory | Not started | Implement Linear/Ridge baseline | W3-01 |
| W3-05 | P0 mandatory | Not started | Evaluate MAE, RMSE, sMAPE, MASE | W3-02, W3-03, W3-04 |
| W3-06 | P0 mandatory | Not started | Save baseline report | W3-05 |
| W3-07 | P1 important | Not started | Add tests for temporal split and baseline metrics | W3-05 |

## Week 4 Tasks: Main Model + MLflow

| ID | Priority | Status | Task | Depends On |
|---|---|---|---|---|
| W4-01 | P0 mandatory | Not started | Choose LightGBM or CatBoost as primary model | W3-06 |
| W4-02 | P0 mandatory | Not started | Implement training pipeline | W4-01 |
| W4-03 | P0 mandatory | Not started | Compare main model against baselines | W4-02 |
| W4-04 | P0 mandatory | Not started | Add MLflow experiment tracking | W4-02 |
| W4-05 | P0 mandatory | Not started | Save best model artifact and feature schema | W4-03 |
| W4-06 | P0 mandatory | Not started | Create model evaluation report | W4-03 |
| W4-07 | P1 important | Not started | Add model reload/inference smoke test | W4-05 |

## Week 5 Tasks: Uncertainty + Regime Detection

| ID | Priority | Status | Task | Depends On |
|---|---|---|---|---|
| W5-01 | P0 mandatory | Not started | Implement uncertainty interval method | W4-05 |
| W5-02 | P0 mandatory | Not started | Evaluate empirical coverage and interval width | W5-01 |
| W5-03 | P0 mandatory | Not started | Add interval outputs to forecast artifact | W5-01 |
| W5-04 | P0 mandatory | Not started | Implement rolling volatility regime rules | W2-07 |
| W5-05 | P0 mandatory | Not started | Implement z-score anomaly detection | W2-07 |
| W5-06 | P0 mandatory | Not started | Create regime/anomaly report | W5-04, W5-05 |
| W5-07 | P1 important | Not started | Add SHAP global/local explanations | W4-05 |

## Week 6 Tasks: Recommendation Engine

| ID | Priority | Status | Task | Depends On |
|---|---|---|---|---|
| W6-01 | P0 mandatory | Not started | Finalize mandi metadata coordinates | W1-09 |
| W6-02 | P0 mandatory | Not started | Implement transport cost estimator | W6-01 |
| W6-03 | P0 mandatory | Not started | Implement candidate mandi filtering | W6-01 |
| W6-04 | P0 mandatory | Not started | Calculate expected net price | W5-03, W6-02 |
| W6-05 | P0 mandatory | Not started | Add uncertainty penalty and risk level | W5-03 |
| W6-06 | P0 mandatory | Not started | Rank mandis and return alternatives | W6-04, W6-05 |
| W6-07 | P0 mandatory | Not started | Evaluate regret@K and missed profit | W6-06 |
| W6-08 | P1 important | Not started | Add tests for recommendation edge cases | W6-06 |

## Week 7 Tasks: FastAPI + Dashboard

| ID | Priority | Status | Task | Depends On |
|---|---|---|---|---|
| W7-01 | P0 mandatory | Not started | Build FastAPI app skeleton | W6-06 |
| W7-02 | P0 mandatory | Not started | Add `/health` endpoint | W7-01 |
| W7-03 | P0 mandatory | Not started | Add `/forecast` endpoint | W5-03, W7-01 |
| W7-04 | P0 mandatory | Not started | Add `/recommend` endpoint | W6-06, W7-01 |
| W7-05 | P0 mandatory | Not started | Add `/regime` endpoint | W5-06, W7-01 |
| W7-06 | P0 mandatory | Not started | Add `/metrics` endpoint | W7-01 |
| W7-07 | P0 mandatory | Not started | Build Streamlit Overview page | W7-02, W7-06 |
| W7-08 | P0 mandatory | Not started | Build Streamlit Forecast page | W7-03 |
| W7-09 | P0 mandatory | Not started | Build Streamlit Recommendation page | W7-04 |
| W7-10 | P0 mandatory | Not started | Build Streamlit Regime/Anomaly page | W7-05 |
| W7-11 | P0 mandatory | Not started | Build Streamlit Monitoring page | W7-06 |
| W7-12 | P1 important | Not started | Add API integration tests | W7-02, W7-03, W7-04 |

## Week 8 Tasks: Docker + Tests + Documentation

| ID | Priority | Status | Task | Depends On |
|---|---|---|---|---|
| W8-01 | P0 mandatory | Not started | Add Dockerfile | W7-11 |
| W8-02 | P0 mandatory | Not started | Add Docker Compose for API and dashboard | W8-01 |
| W8-03 | P0 mandatory | Not started | Add unit tests for critical pipeline modules | W2-W6 tasks |
| W8-04 | P0 mandatory | Not started | Add CI workflow for tests/lint | W8-03 |
| W8-05 | P0 mandatory | Not started | Write README | W7-11 |
| W8-06 | P0 mandatory | Not started | Write model card | W4-06, W5-02 |
| W8-07 | P1 important | Not started | Capture demo screenshots/GIF | W7-11 |
| W8-08 | P1 important | Not started | Record demo video/script | W7-11 |
| W8-09 | P0 mandatory | Not started | Final docs and tracker alignment | W8-05 |

## Scope Watchlist

| Item | Status | Rule |
|---|---|---|
| Weather features | P1 important | Include only if data alignment is quick |
| SHAP explanations | P1 important | Add after model works |
| ARIMA/SARIMA | P2 optional | Selected crop-mandi diagnostics only |
| Causal inference | P2 optional | Future research only |
| Arbitrage detection | P2 optional | Future after recommendation engine |
| Price propagation graph | P2 optional | Future and non-causal wording |

