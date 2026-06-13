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
| TD-04 | P0 mandatory | Done | Build raw data ingestion |
| TD-05 | P0 mandatory | Done | Build cleaned mandi price table |
| TD-06 | P0 mandatory | Done | Create initial EDA/profile report |
| TD-07 | P0 mandatory | Done | Select top 10-15 Maharashtra onion mandis |

### In Progress

| ID | Priority | Status | Task |
|---|---|---|---|
| - | - | - | No implementation tasks in progress |

### Done

| ID | Priority | Status | Task |
|---|---|---|---|
| DN-01 | P0 mandatory | Done | Final project blueprint created |
| DN-02 | P0 mandatory | Done | Planning documentation foundation created |
| DN-03 | P0 mandatory | Done | Pre-implementation gate fixes applied for Day 0 readiness |
| DN-04 | P0 mandatory | Done | CEDA selected as primary AGMARKNET data path |
| DN-05 | P0 mandatory | Done | Project structure, config skeleton, and Day 0 validation runner added |
| DN-06 | P0 mandatory | Done | MVP narrowed to offline Onion/Maharashtra decision showcase |
| DN-07 | P0 mandatory | Done | Onion/Maharashtra CEDA fetch script smoke-tested |
| DN-08 | P0 mandatory | Done | Full Onion/Maharashtra raw dump saved locally with 86,052 rows |
| DN-09 | P0 mandatory | Done | Candidate top-15 mandi list created from coverage profile |
| DN-10 | P0 mandatory | Done | Clean Onion/Maharashtra panel built for selected 15 mandis |
| DN-11 | P0 mandatory | Done | Leakage-safe 7-day feature table built |

### Blocked

| ID | Priority | Status | Task | Blocker |
|---|---|---|---|---|
| - | - | - | No blocked tasks | - |

## Week 1 Tasks: Project Setup + Data Foundation

| ID | Priority | Status | Task | Depends On |
|---|---|---|---|---|
| W1-01 | P0 mandatory | Done | Create project folder structure | None |
| W1-02 | P0 mandatory | Done | Add dependency/config skeleton | W1-01 |
| W1-03 | P0 mandatory | Done | Add `.gitignore` rules for data, secrets, artifacts, MLflow runs | W1-01 |
| W1-04 | P0 mandatory | Done | Confirm mandi data source | None |
| W1-05 | P0 mandatory | Done | Fetch full Onion/Maharashtra CEDA history before key expiry | W1-04 |
| W1-06 | P0 mandatory | Done | Normalize initial dates and basic fields | W1-05 |
| W1-07 | P0 mandatory | Done | Create raw and cleaned data storage convention | W1-05 |
| W1-08 | P0 mandatory | Done | Start EDA notebook for Onion/Maharashtra coverage and quality | W1-06 |
| W1-09 | P0 mandatory | Done | Select top 10-15 Maharashtra onion mandis based on EDA | W1-08 |
| W1-10 | P1 important | Not started | Draft data dictionary | W1-06 |

**Week 1 Definition of Done:** Raw Onion/Maharashtra CEDA records from 2020-01-01 to 2026-06-13 are saved locally. Clean table exists for candidate MVP scope. EDA identifies 10-15 usable mandis or flags data quality risk. Missingness and duplicate patterns are documented.

## Week 2 Tasks: Data Cleaning + Feature Engineering

| ID | Priority | Status | Task | Depends On |
|---|---|---|---|---|
| W2-01 | P0 mandatory | Done | Normalize crop, state, district, mandi names | W1-09 |
| W2-02 | P0 mandatory | Done | Convert prices to INR/quintal | W2-01 |
| W2-03 | P0 mandatory | Done | Handle duplicate crop-mandi-date records | W2-01 |
| W2-04 | P0 mandatory | Done | Implement missing data flags | W2-01 |
| W2-05 | P0 mandatory | Done | Build crop-mandi-date panel | W2-02 |
| W2-06 | P0 mandatory | Done | Add lag features: 1, 3, 7, 14, 30 days for 7-day target features | W2-05 |
| W2-07 | P0 mandatory | Done | Add rolling mean, median, std, returns, volatility | W2-06 |
| W2-08 | P0 mandatory | Done | Add calendar features | W2-05 |
| W2-09 | P0 mandatory | Done | Add validation checks | W2-05 |
| W2-10 | P1 important | Not started | Add weather features only after price, arrival, and calendar features work | W2-08 |

**Week 2 Definition of Done:** Feature table is reproducible with no future data leakage. Rows with insufficient history are flagged or excluded. Validation checks pass or generate documented failures. Feature table supports the 7-day target.

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

**Week 3 Definition of Done:** No random train-test split used. Baseline metrics logged and saved. Baseline code tested on small sample data. Weak and strong horizon performance documented.

## Week 4 Tasks: Main Model + MLflow

| ID | Priority | Status | Task | Depends On |
|---|---|---|---|---|
| W4-01 | P0 mandatory | Not started | Train LightGBM as primary MVP model | W3-06 |
| W4-02 | P0 mandatory | Not started | Implement training pipeline | W4-01 |
| W4-03 | P0 mandatory | Not started | Compare main model against baselines | W4-02 |
| W4-04 | P0 mandatory | Not started | Add MLflow experiment tracking | W4-02 |
| W4-05 | P0 mandatory | Not started | Save best model artifact and feature schema | W4-03 |
| W4-06 | P0 mandatory | Not started | Create model evaluation report | W4-03 |
| W4-07 | P1 important | Not started | Add model reload/inference smoke test | W4-05 |
| W4-08 | P1 important | Not started | Train CatBoost as comparison model if time allows | W4-03 |

**Week 4 Definition of Done:** Main model compared to all baselines. MLflow logs params, metrics, artifacts, and run metadata. Saved model can be reloaded for inference. Model artifact includes feature order and schema.

## Week 5 Tasks: Uncertainty + Regime Detection

| ID | Priority | Status | Task | Depends On |
|---|---|---|---|---|
| W5-01 | P0 mandatory | Not started | Implement uncertainty interval method | W4-05 |
| W5-02 | P0 mandatory | Not started | Evaluate empirical coverage and interval width | W5-01 |
| W5-03 | P0 mandatory | Not started | Add interval outputs to forecast artifact | W5-01 |
| W5-04 | P0 mandatory | Not started | Implement rolling volatility regime rules | W2-07 |
| W5-05 | P0 mandatory | Not started | Implement z-score anomaly detection | W2-07 |
| W5-06 | P0 mandatory | Not started | Create regime/anomaly report | W5-04, W5-05 |

**Week 5 Definition of Done:** Every forecast returns lower and upper bounds. Coverage measured on validation/test period. Regime label has human-readable reason. Anomaly logic documented and tested.

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

**Week 6 Definition of Done:** Recommendation ranks mandis deterministically. Formula includes forecast price, transport cost, and uncertainty penalty. Regret@K evaluated on test period. Edge cases tested.

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
| W7-13 | P1 important | Not started | Add SHAP global and local explanations | W4-05 |

**Week 7 Definition of Done:** Dashboard completes full demo flow. API responses match API_SPEC.md. Forecast and recommendation served from model artifacts. Errors are user-friendly. API integration tests cover core endpoints.

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

**Week 8 Definition of Done:** Docker Compose starts API and dashboard. Test suite passes locally. README explains decision intelligence framing. Demo flow recorded or documented.

## Scope Watchlist

| Item | Status | Rule |
|---|---|---|
| Weather features | P1 important | Include only if data alignment is quick |
| SHAP explanations | P1 important | Add after model works |
| ARIMA/SARIMA | P2 optional | Selected crop-mandi diagnostics only |
| Causal inference | P2 optional | Future research only |
| Arbitrage detection | P2 optional | Future after recommendation engine |
| Price propagation graph | P2 optional | Future and non-causal wording |
