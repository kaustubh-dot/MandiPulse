# MandiPulse India — Final Project Blueprint

> **Project type:** End-to-end Data Science / ML Engineering project  
> **Target:** Resume, GitHub, portfolio, placement interviews  
> **Positioning:** Not a generic crop price predictor — a **transport-cost-aware mandi decision intelligence system**

---

## 1. Final Project Name

# MandiPulse India  
## A Transport-Cost-Aware Mandi Decision Intelligence System

---

## 2. One-Line Description

MandiPulse India is an end-to-end agricultural market intelligence platform that forecasts crop prices across Indian mandis, produces uncertainty-aware prediction intervals, detects volatile market regimes, and recommends the most profitable mandi to sell in after transport cost.

---

## 3. Resume Bullet

**MandiPulse India — Agricultural Market Intelligence Platform**  
Built an end-to-end mandi decision intelligence system for Indian agricultural markets using temporal price forecasting, sparse-data imputation, conformal prediction intervals, regime/anomaly detection, and transport-cost-aware mandi recommendation; deployed with FastAPI, Streamlit, MLflow, Docker, and monitoring.

---

## 4. Core Problem

Most small farmers and FPOs do not have clear visibility into:

- Which mandi is likely to offer the best price soon
- Whether the current market is normal or unusually volatile
- Whether a higher price at another mandi is still profitable after transport cost
- How confident a price forecast is
- Whether recent price movements are anomalies or seasonal behavior

A simple price prediction model only answers:

> "What will the crop price be?"

MandiPulse should answer:

> "Where should I sell, when should I sell, how confident is the system, and why?"

---

## 5. Why This Is Not a Common Crop Price Project

| Generic Crop Price Prediction | MandiPulse India |
|---|---|
| Predicts one price | Forecasts prices across many mandis |
| Uses random train-test split | Uses temporal backtesting |
| Gives one number | Gives prediction intervals |
| No decision layer | Recommends best mandi after transport cost |
| No uncertainty | Uses conformal prediction / quantile intervals |
| No production system | FastAPI + dashboard + Docker + monitoring |
| No business metric | Uses recommendation regret / top-k mandi evaluation |
| Looks like a notebook | Looks like a deployable decision product |

---

## 6. Strict MVP Scope

Do **not** start too big.

### MVP scope

- **Crops:** 2 crops
- **States:** 3 states
- **Mandis:** 50–100 mandis
- **Forecast horizons:** 7, 14, and 30 days
- **Main decision feature:** Recommend best mandi after estimated transport cost
- **Dashboard:** Streamlit
- **Backend:** FastAPI
- **Tracking:** MLflow
- **Deployment:** Docker / Docker Compose
- **Monitoring:** Basic data quality + drift monitoring

### Suggested crop choices

Choose crops with high volume, strong price movement, and data availability.

Good candidates:

1. **Onion**
2. **Tomato**
3. **Potato**
4. **Wheat**
5. **Paddy/Rice**

Recommended MVP pair:

> **Onion + Tomato**

Reason:

- High price volatility
- Strong public relevance
- Frequent news cycles
- Good mandi activity
- Easy to explain in interviews

### Suggested states

Recommended:

> **Maharashtra + Karnataka + Uttar Pradesh**

Reason:

- Maharashtra has strong onion/tomato mandi relevance
- Karnataka gives southern market diversity
- Uttar Pradesh gives large northern market representation

Adjust based on actual data quality after EDA.

---

## 7. Must-Have Features

These are non-negotiable for the project to feel resume-worthy.

### 7.1 Data Pipeline

- Ingest mandi price data
- Normalize crop names, mandi names, units, dates
- Handle missing values and duplicate records
- Create clean crop-mandi-date panel data
- Store processed data in DuckDB or PostgreSQL

### 7.2 Feature Engineering

Features should include:

- Lag prices: 1, 3, 7, 14, 30 days
- Rolling mean, rolling median, rolling std
- Price returns and volatility
- Day of week, month, season
- Festival/holiday indicators if available
- Arrival quantity if available
- Weather features if feasible:
  - Rainfall
  - Temperature
  - Humidity
- Mandi metadata:
  - State
  - District
  - Latitude/longitude
  - Distance from farmer/input location

### 7.3 Forecasting

Models to include:

1. Seasonal naive baseline
2. Moving average baseline
3. Linear/Ridge baseline
4. LightGBM or CatBoost main model
5. Optional ARIMA/SARIMA for selected crop-mandi pairs

Forecast horizons:

- 7 days
- 14 days
- 30 days

### 7.4 Temporal Validation

Do not use random split.

Use:

- Train on older dates
- Validate on later dates
- Test on newest unseen period

Preferred:

```text
Train: first 70%
Validation: next 15%
Test: final 15%
```

Or rolling/walk-forward validation.

### 7.5 Uncertainty Estimation

Use one of:

- Quantile regression
- MAPIE conformal prediction
- Residual-based prediction intervals

Best version:

> Use conformal prediction to generate calibrated uncertainty intervals.

Output should look like:

```json
{
  "forecast_price": 1840,
  "lower_bound": 1690,
  "upper_bound": 2015,
  "confidence_level": 0.90
}
```

### 7.6 Regime / Anomaly Detection

Detect whether market behavior is:

- Normal
- Volatile
- Crisis / abnormal

Simple MVP approaches:

- Rolling volatility threshold
- Z-score anomaly detection
- Isolation Forest on price returns
- Optional Hidden Markov Model later

Dashboard should show:

> Current regime: Volatile  
> Reason: 7-day volatility is 2.4x above normal.

### 7.7 Transport-Cost-Aware Mandi Recommendation

This is the feature that makes the project a decision system.

For each candidate mandi:

```text
Expected net price = predicted mandi price - estimated transport cost
```

Rank mandis by:

```text
risk_adjusted_score = expected net price - uncertainty_penalty
```

Example output:

| Rank | Mandi | Forecast Price | Transport Cost | Net Expected Price | Risk |
|---:|---|---:|---:|---:|---|
| 1 | Lasalgaon | ₹2100/qtl | ₹120/qtl | ₹1980/qtl | Medium |
| 2 | Pune | ₹1980/qtl | ₹60/qtl | ₹1920/qtl | Low |
| 3 | Mumbai | ₹2250/qtl | ₹310/qtl | ₹1940/qtl | High |

### 7.8 Explainability

Include:

- SHAP global feature importance
- SHAP local explanation for one forecast
- Human-readable explanation

Example:

> Price is expected to rise because previous 7-day prices increased, arrivals dropped, and recent rainfall was below normal.

### 7.9 API

Minimum FastAPI endpoints:

```text
GET  /health
POST /forecast
POST /recommend
GET  /regime
GET  /metrics
```

Optional advanced endpoints:

```text
GET /arbitrage
GET /similar-days
GET /data-quality
```

### 7.10 Dashboard

Minimum dashboard pages:

1. **Overview**
   - Selected crop/state/mandi
   - Latest prices
   - Forecast summary

2. **Forecast View**
   - Price forecast line chart
   - Confidence bands
   - Forecast horizon selector

3. **Mandi Recommendation View**
   - Ranked mandis
   - Net price after transport cost
   - Risk-adjusted recommendation

4. **Market Regime / Anomaly View**
   - Normal/volatile/crisis indicator
   - Recent anomalies
   - Volatility trend

5. **Model Monitoring View**
   - Data freshness
   - Missing data
   - Recent forecast error
   - Drift indicators

---

## 8. Nice-to-Have Advanced Features

Only build these after the core MVP works.

### 8.1 Arbitrage Detection

Detect when price gaps between nearby mandis exceed transport cost.

Formula:

```text
arbitrage_margin = destination_price - source_price - transport_cost
```

Useful output:

> Onion prices in Mandi A are ₹300/qtl lower than Mandi B, while estimated transport cost is ₹120/qtl. Potential margin: ₹180/qtl.

This is strong because it shows market inefficiency detection.

### 8.2 Price Propagation Graph

Build a mandi graph where:

- Nodes = mandis
- Edges = price lead-lag relationships or distance-based connections

Use:

- NetworkX
- Granger causality carefully
- Correlation/lag analysis

Important wording:

Use:

> Predictive price transmission graph

Avoid saying:

> True causal price propagation

### 8.3 Similar Historical Market Days

For a selected forecast, show historical days with similar patterns.

Example:

> Similar historical pattern detected in March 2023, when prices rose 12% over the next 10 days.

This is easy to explain and very useful for interviews.

---

## 9. Features to Avoid in MVP

Avoid these at the beginning:

- Kubernetes
- Complex React frontend
- Too many crops/states
- Deep learning forecasting models
- Temporal Fusion Transformers
- Heavy causal inference claims
- Full-scale 500+ mandi network
- Mobile app
- WhatsApp bot
- Multilingual voice interface
- Complex microservices

These can be future extensions.

---

## 10. Causal Inference Warning

Causal inference is attractive, but risky.

Do not make strong claims like:

> Rainfall delay caused prices to rise by exactly ₹8/kg.

Instead, use cautious wording:

> Explored causal impact of weather shocks on mandi prices using a DAG-based DoWhy analysis and refutation tests.

Causal inference should be an optional research module, not the core of the MVP.

---

## 11. Evaluation Metrics

### Forecasting metrics

Use:

- MAE
- RMSE
- sMAPE
- MASE

### Uncertainty metrics

Use:

- Empirical coverage
- Interval width
- Pinball loss if using quantile models

### Recommendation metrics

Use:

- Top-k recommendation accuracy
- Regret@K
- Average missed profit
- Net price improvement over nearest mandi baseline

Example:

```text
Regret = best_actual_net_price - recommended_actual_net_price
```

### Regime/anomaly metrics

Use:

- Number of detected anomaly periods
- Backtest error during normal vs volatile periods
- Precision/recall if labeled events are available

### System metrics

Use:

- API latency
- Data freshness
- Missing data percentage
- Model inference success rate

---

## 12. Suggested Tech Stack

### Core

- Python
- Pandas
- NumPy
- Scikit-learn
- LightGBM or CatBoost
- Statsmodels
- MAPIE
- SHAP

### Data

- DuckDB for local analytics
- PostgreSQL optional
- Great Expectations or Pandera for validation

### Backend

- FastAPI
- Pydantic
- Uvicorn

### Dashboard

- Streamlit
- Plotly
- Folium or PyDeck for maps

### MLOps

- MLflow
- Docker
- Docker Compose
- GitHub Actions
- Evidently AI or custom drift reports

### Optional

- NetworkX for graph analytics
- OSMnx for road/distance features
- DoWhy for causal analysis
- hmmlearn for HMM-based regime detection

---

## 13. Final Folder Structure

```text
mandipulse/
├── README.md
├── LICENSE
├── pyproject.toml
├── Makefile
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── configs/
│   ├── data.yaml
│   ├── model.yaml
│   └── app.yaml
│
├── data/
│   ├── raw/
│   ├── interim/
│   ├── processed/
│   ├── external/
│   └── data_dictionary.md
│
├── notebooks/
│   ├── 01_eda_data_quality.ipynb
│   ├── 02_baseline_forecasting.ipynb
│   ├── 03_model_training_and_backtesting.ipynb
│   ├── 04_uncertainty_conformal_prediction.ipynb
│   ├── 05_recommendation_engine.ipynb
│   └── 06_regime_anomaly_detection.ipynb
│
├── src/
│   └── mandipulse/
│       ├── __init__.py
│       ├── config.py
│       │
│       ├── data/
│       │   ├── __init__.py
│       │   ├── ingestion.py
│       │   ├── validation.py
│       │   ├── preprocessing.py
│       │   └── schemas.py
│       │
│       ├── features/
│       │   ├── __init__.py
│       │   ├── time_features.py
│       │   ├── price_features.py
│       │   ├── weather_features.py
│       │   └── distance_features.py
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   ├── baselines.py
│       │   ├── trainer.py
│       │   ├── forecaster.py
│       │   ├── uncertainty.py
│       │   └── evaluation.py
│       │
│       ├── recommendation/
│       │   ├── __init__.py
│       │   ├── transport_cost.py
│       │   ├── mandi_ranker.py
│       │   └── regret_metrics.py
│       │
│       ├── regime/
│       │   ├── __init__.py
│       │   ├── anomaly_detector.py
│       │   └── regime_classifier.py
│       │
│       ├── explainability/
│       │   ├── __init__.py
│       │   ├── shap_explainer.py
│       │   └── narratives.py
│       │
│       ├── monitoring/
│       │   ├── __init__.py
│       │   ├── data_drift.py
│       │   ├── data_quality.py
│       │   └── performance_monitor.py
│       │
│       └── api/
│           ├── __init__.py
│           ├── main.py
│           ├── routes/
│           │   ├── health.py
│           │   ├── forecast.py
│           │   ├── recommend.py
│           │   ├── regime.py
│           │   └── metrics.py
│           └── response_models.py
│
├── dashboard/
│   ├── app.py
│   ├── pages/
│   │   ├── 1_overview.py
│   │   ├── 2_forecast.py
│   │   ├── 3_recommendation.py
│   │   ├── 4_regime_anomaly.py
│   │   └── 5_monitoring.py
│   └── components/
│       ├── charts.py
│       ├── maps.py
│       └── tables.py
│
├── tests/
│   ├── unit/
│   │   ├── test_features.py
│   │   ├── test_forecaster.py
│   │   ├── test_uncertainty.py
│   │   ├── test_recommendation.py
│   │   └── test_regime.py
│   ├── integration/
│   │   └── test_api.py
│   └── conftest.py
│
├── docs/
│   ├── architecture.md
│   ├── data_sources.md
│   ├── modeling_methodology.md
│   ├── evaluation.md
│   └── api_reference.md
│
├── reports/
│   ├── figures/
│   ├── model_card.md
│   └── final_report.md
│
├── artifacts/
│   ├── models/
│   ├── predictions/
│   └── monitoring/
│
└── mlruns/
```

---

## 14. API Contract

### POST `/forecast`

Request:

```json
{
  "crop": "onion",
  "state": "maharashtra",
  "mandi": "lasalgaon",
  "horizon_days": 14
}
```

Response:

```json
{
  "crop": "onion",
  "mandi": "lasalgaon",
  "horizon_days": 14,
  "forecast_price": 2100.5,
  "lower_bound": 1940.2,
  "upper_bound": 2285.8,
  "market_regime": "volatile",
  "confidence_level": 0.90,
  "top_drivers": [
    "7-day price momentum",
    "arrival quantity drop",
    "seasonal pattern"
  ]
}
```

### POST `/recommend`

Request:

```json
{
  "crop": "onion",
  "farmer_location": {
    "latitude": 19.9975,
    "longitude": 73.7898
  },
  "candidate_states": ["maharashtra"],
  "horizon_days": 14,
  "quantity_quintal": 20
}
```

Response:

```json
{
  "recommended_mandi": "lasalgaon",
  "expected_net_price_per_quintal": 1980.4,
  "risk_level": "medium",
  "alternatives": [
    {
      "mandi": "pune",
      "expected_net_price_per_quintal": 1920.2,
      "risk_level": "low"
    },
    {
      "mandi": "mumbai",
      "expected_net_price_per_quintal": 1940.1,
      "risk_level": "high"
    }
  ],
  "reason": "Lasalgaon has the highest risk-adjusted expected net price after transport cost."
}
```

---

## 15. Dashboard Layout

### Page 1 — Overview

- Total mandis tracked
- Crops tracked
- Latest data date
- Market health summary
- Current volatile markets

### Page 2 — Forecast

- Crop/mandi selector
- Forecast horizon selector
- Price forecast chart
- Confidence interval bands
- Actual vs predicted backtest chart

### Page 3 — Mandi Recommendation

- Farmer location input
- Crop and quantity input
- Ranked mandi table
- Map of candidate mandis
- Net price after transport cost

### Page 4 — Regime / Anomaly

- Market regime indicator
- Volatility chart
- Anomaly timeline
- Recent abnormal price movements

### Page 5 — Monitoring

- Data freshness
- Missing values by mandi
- Forecast error trend
- Drift report
- Model version from MLflow

---

## 16. 8-Week Build Roadmap

### Week 1 — Project Setup + Data Foundation

- Create repo and folder structure
- Set up environment
- Download/scrape mandi price data
- Create raw and processed data layers
- Create data dictionary
- Start EDA notebook

Deliverable:

> Clean initial dataset and EDA notebook.

---

### Week 2 — Data Cleaning + Feature Engineering

- Normalize crop, mandi, state, district names
- Handle missing values
- Build crop-mandi-date panel
- Create lag and rolling features
- Add calendar features
- Create data validation checks

Deliverable:

> Feature table ready for modeling.

---

### Week 3 — Baseline Forecasting

- Implement seasonal naive baseline
- Implement moving average baseline
- Implement Ridge/Linear baseline
- Set up temporal validation
- Evaluate MAE, RMSE, sMAPE, MASE

Deliverable:

> Baseline performance report.

---

### Week 4 — Main Model + MLflow

- Train LightGBM/CatBoost model
- Compare against baselines
- Track experiments in MLflow
- Save best model artifact
- Create model evaluation report

Deliverable:

> Strong model with tracked experiments.

---

### Week 5 — Uncertainty + Regime Detection

- Add conformal prediction or quantile intervals
- Validate empirical coverage
- Add anomaly/regime detection
- Create volatility/regime report

Deliverable:

> Forecasts with confidence bands and regime labels.

---

### Week 6 — Recommendation Engine

- Estimate transport cost
- Rank mandis by net expected price
- Add uncertainty penalty
- Evaluate recommendation regret
- Build recommendation API logic

Deliverable:

> Working mandi recommendation engine.

---

### Week 7 — FastAPI + Dashboard

- Build FastAPI app
- Add `/forecast`, `/recommend`, `/regime`, `/health`
- Build Streamlit dashboard
- Add forecast charts and recommendation table
- Add basic monitoring page

Deliverable:

> End-to-end working app.

---

### Week 8 — Docker + Tests + Documentation

- Dockerize app
- Add Docker Compose
- Add unit tests
- Add API integration test
- Write README
- Write model card
- Add architecture diagram
- Record demo video

Deliverable:

> Resume-ready GitHub project.

---

## 17. What Will Make the Project Look Weak

Avoid these mistakes:

- Calling it only "crop price prediction"
- Using random train-test split
- No uncertainty intervals
- No mandi recommendation feature
- No temporal backtesting
- No comparison with baselines
- No model monitoring
- No explanation of missing data
- Too many crops/states causing messy unfinished work
- Claiming causal conclusions without proper evidence
- No deployed API/dashboard
- Poor README

---

## 18. What Will Make the Project Impressive

The project will stand out if it has:

- Clear problem framing
- Clean architecture diagram
- Real mandi data
- Temporal validation
- Baseline vs advanced model comparison
- Conformal prediction intervals
- Mandi recommendation after transport cost
- Regime/anomaly detection
- SHAP explanations
- FastAPI + Streamlit
- MLflow tracking
- Docker deployment
- Model card
- Demo video

---

## 19. README Structure

Your final README should include:

```text
1. Project title and tagline
2. Problem statement
3. Why this is not generic crop price prediction
4. Demo screenshots/GIF
5. Architecture diagram
6. Data sources
7. ML methodology
8. Forecasting and validation approach
9. Uncertainty estimation
10. Mandi recommendation logic
11. Dashboard features
12. API endpoints
13. Results and metrics
14. Model monitoring
15. Limitations
16. Future work
17. How to run locally
18. Tech stack
19. Resume bullet
```

---

## 20. Final Interview Pitch

Use this 60-second explanation:

> MandiPulse is an end-to-end agricultural market intelligence platform for Indian mandis. I built it because simple crop price prediction is not enough for farmers or FPOs — the real decision is where and when to sell after considering transport cost and uncertainty.  
>
> The system ingests historical mandi prices, cleans sparse and missing market data, engineers lag and rolling features, and trains forecasting models using temporal backtesting. I used LightGBM/CatBoost against naive baselines and added conformal prediction intervals so the system returns not just a price forecast, but also uncertainty bounds.  
>
> The main product feature is a mandi recommendation engine that ranks nearby markets by expected net price after transport cost and uncertainty penalty. I also added regime/anomaly detection to flag volatile markets, SHAP explanations for forecast drivers, and production components like FastAPI endpoints, a Streamlit dashboard, MLflow tracking, Docker, and monitoring.  
>
> The key learning was that the project is not about predicting prices, but about turning noisy agricultural market data into a usable decision system.

---

## 21. Final Positioning with Your Portfolio

Your portfolio story should look like this:

| Project | Domain | Main Signal |
|---|---|---|
| AlterScore | Fintech | Responsible AI, explainability, credit risk |
| MandiPulse | Agriculture / markets | Time-series forecasting, uncertainty, recommendation systems, MLOps |
| BTP Landslide Project | Climate / geospatial | Multimodal fusion, remote sensing, risk prediction |

Together, these show:

- Multiple domains
- Multiple data types
- Classification + forecasting + recommendation
- Explainability
- Production thinking
- Real-world problem solving

---

## 22. Final Rule

If the project starts looking like this:

> "I predicted crop prices using Random Forest."

Stop and redesign.

It must always stay framed as:

> "I built a mandi decision intelligence system that forecasts prices, estimates uncertainty, detects volatile market regimes, and recommends the best selling market after transport cost."

That is the version worth building.
