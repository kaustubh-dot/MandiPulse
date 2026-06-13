# MandiPulse India Tech Stack

## Recommended Stack

| Layer | Tooling | Role | Why Chosen |
|---|---|---|---|
| Language | Python 3.11 or 3.12 | Core implementation | Strong data science ecosystem and Streamlit support |
| Dependency management | `pyproject.toml` with pip or uv | Reproducible local setup | Lightweight and common for portfolio projects |
| Data processing | Pandas, NumPy | Cleaning, feature creation, panel construction | Familiar, fast enough for 10-15 mandis |
| Local analytics store | DuckDB | Processed tables, feature tables, local SQL | Simple local OLAP without a server |
| Optional relational DB | PostgreSQL | Production-like deployment option | Useful later, not required for MVP |
| Data validation | Pandera or Great Expectations | Schema and quality checks | Prevents silent data issues |
| Modeling | scikit-learn, LightGBM, CatBoost later | Baselines, primary model, optional comparison | LightGBM is the first primary MVP model; CatBoost is P1 comparison only |
| Statistical baselines | Statsmodels where useful | Seasonal naive, optional ARIMA/SARIMA | Good for selected crop-mandi diagnostics |
| Uncertainty | MAPIE, quantile models, residual intervals | Prediction intervals | Supports calibrated uncertainty without deep learning |
| Explainability | SHAP | Feature importance and local drivers | Interview-friendly, model-aware explanations |
| API | FastAPI, Pydantic, Uvicorn | Post-MVP prediction and recommendation service | Useful later, not part of the narrowed MVP |
| Dashboard | Streamlit, Plotly, Folium or PyDeck | MVP product interface | Fast offline dashboard with maps and charts |
| Experiment tracking | MLflow | Metrics, parameters, model artifacts | Standard MLOps signal for portfolio |
| Monitoring | Custom reports | Data coverage, missingness, backtest metrics | Static reports are enough for MVP |
| Testing | Pytest, pytest-cov | Unit and integration tests | Simple and reliable |
| Code quality | Ruff, Black optional | Linting and formatting | Keeps repository clean without heavy tooling |
| Packaging | Docker, Docker Compose | Local deployment | Demonstrates deployable system without Kubernetes |
| CI | GitHub Actions | Tests and linting | Portfolio-ready automation |

## Tool Choices by Project Need

| Need | Chosen Tool | Notes |
|---|---|---|
| Fast local exploration | Pandas + DuckDB | DuckDB can query CSV/Parquet and persisted processed tables |
| Clean feature pipeline | Pandas + modular Python functions | Avoids overengineered orchestration |
| Time-based validation | scikit-learn utilities plus custom temporal splitter | Random split is forbidden |
| Main tabular model | LightGBM first, CatBoost P1 comparison | Use LightGBM as the primary MVP model; do not block MVP on CatBoost |
| Confidence intervals | MAPIE conformal prediction | Prefer calibrated intervals over uncalibrated model confidence |
| Human-readable reasons | SHAP + narrative templates | Keep explanations cautious and non-causal |
| Decision layer | Custom recommendation module | Core differentiator of the project |
| API schema | Pydantic models | Keeps dashboard/API contract explicit |
| Dashboard | Streamlit | Avoids React and keeps focus on ML system |
| Local deployment | Docker Compose | One command for API, dashboard, and MLflow if configured |

## Alternatives Rejected for MVP

| Alternative | Decision | Reason |
|---|---|---|
| Kubernetes | Reject | Too heavy for an MVP and not needed for local/portfolio deployment |
| React frontend | Reject | Slows project without improving ML engineering signal |
| Mobile app | Reject | Scope creep |
| WhatsApp bot | Reject | Scope creep and integration complexity |
| Temporal Fusion Transformer | Reject | Heavy deep learning stack, not needed for 10-15 mandis |
| Large neural forecasting frameworks | Reject | Increases complexity and data requirements |
| More crops/states before Onion/Maharashtra works | Reject | Risks messy, unfinished data work |
| Microservices | Reject | A single Streamlit app is enough for MVP; FastAPI can stay monolithic later |
| Random forest as main story | Avoid | The MVP story should be LightGBM plus honest baselines |
| Full causal inference | Future only | Risky claims; optional research module after MVP |
| Full arbitrage system | Future only | Can be a lightweight analysis later, not core MVP |
| Production route optimization | Reject | Transport cost estimate is enough for MVP |

## Local Development Setup Assumptions

- The project runs on a single developer machine.
- Python environment is isolated with `.venv` or equivalent.
- Raw data is stored locally under `data/raw/`, but raw data should not be committed if large or license-restricted.
- Processed data is stored in DuckDB, Parquet, or CSV under ignored data folders.
- MLflow runs are local during development and should not be committed.
- FastAPI is deferred from the narrowed MVP.
- Streamlit calls shared service modules and saved local artifacts first.
- Docker Compose is post-MVP and should run only the services that exist at that point.

## Production / Deployment Assumptions

This is a portfolio MVP, not a national-scale production system.

| Area | Assumption |
|---|---|
| Deployment target | Local Docker Compose or lightweight cloud VM |
| Data scale | 1 crop, 1 state, 10-15 mandis |
| Batch cadence | Daily or manual refresh is acceptable |
| Inference | Local Streamlit inference from saved model artifacts |
| Model registry | MLflow local tracking, with model URI/version documented |
| Storage | DuckDB for MVP; PostgreSQL optional if deployment needs server DB |
| Secrets | Environment variables via `.env.example`; never commit real `.env` |
| Monitoring | Batch-generated quality and drift metrics, not full observability platform |

## Library Groups

### Data Processing

- `pandas`
- `numpy`
- `duckdb`
- `pyarrow`
- `python-dateutil`
- `pandera` or `great-expectations`

### Modeling

- `scikit-learn`
- `lightgbm` or `catboost`
- `statsmodels` for optional ARIMA/SARIMA diagnostics
- `joblib`

### Uncertainty

- `mapie`
- LightGBM quantile objective if chosen
- CatBoost quantile objective only for later P1 comparison if CatBoost is enabled
- Custom residual interval utilities as fallback

### Explainability

- `shap`
- Plotly for visualizing feature importance
- Lightweight narrative templates for top drivers

### API

- `fastapi` post-MVP only
- `pydantic` post-MVP only unless used for internal schemas
- `uvicorn` post-MVP only
- `httpx` for API tests/client calls post-MVP only

### Dashboard

- `streamlit`
- `plotly`
- `folium` or `pydeck`
- `requests` or `httpx`

### Monitoring

- `evidently` as optional fallback only; custom data quality summaries are the default for MVP
- Custom data quality summaries as fallback
- MLflow metrics for model performance snapshots

### Testing

- `pytest`
- `pytest-cov`
- `httpx`
- `freezegun` optional for date-sensitive tests

### Packaging and Operations

- `docker`
- `docker-compose`
- `mlflow`
- `ruff`
- `black` optional
- `pre-commit` optional

## Stack Decision Rules

- Prefer one simple tool per layer.
- Add PostgreSQL only if DuckDB becomes limiting.
- Use custom data quality and backtest reports as the default for MVP. Add Evidently only after the Streamlit MVP is useful and stable.
- Use one main model family for MVP.
- Do not add deep learning or orchestration frameworks until the documented MVP works.
