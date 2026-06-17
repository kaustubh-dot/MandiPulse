# MandiPulse India Development Rules

This file is for future AI coding agents and maintainers. Follow these rules unless the project docs are intentionally updated first.

## Scope Rules

- Do not change project scope without updating the relevant docs.
- Keep MVP limited to 1 crop, 1 state, and 10-15 mandis: Onion in Maharashtra.
- Keep the MVP forecast horizon limited to 7 days.
- Keep the project framed as a mandi decision intelligence system.
- Do not turn the project into generic crop price prediction.
- Do not add Kubernetes, mobile app, WhatsApp bot, deep learning forecasting, Temporal Fusion Transformers, large-scale 500+ mandi networks, or unnecessary microservices.
- React frontend: promoted post-MVP as Milestone N (static Next.js export only — see below).
- Treat FastAPI, regime/anomaly detection, live monitoring, causal inference, arbitrage detection, and price propagation graph as optional/future modules unless explicitly scoped and documented.

## Data Rules

- Use CEDA / AGMARKNET as the primary data source unless the data-source contract is intentionally changed.
- Treat Data.gov.in as a fallback path, not the primary MVP blocker.
- Resolve CEDA commodity, state, district, and market IDs through lookup endpoints before fetching prices.
- Use the cached Onion/Maharashtra raw data for modeling work. Refresh only when a valid CEDA key is available and the refresh is intentional.
- Preserve raw data separately from cleaned data.
- Do not commit raw data if it is large, restricted, or easily reproducible from source.
- Normalize crop, mandi, state, district, unit, and date fields.
- Use INR per quintal as the standard price unit.
- Track missing values, duplicates, invalid values, and outliers.
- Do not silently drop records without documenting the rule.
- Do not hardcode local paths.
- Use config files or environment variables for paths and settings.
- Keep generated artifacts reproducible from code, config, and source data.

## Forecasting Rules

- Do not use random train-test split for forecasting.
- Always preserve temporal validation.
- Use train on older dates and validate/test on later dates.
- Always compare against baselines.
- Required baselines:
  - Seasonal naive.
  - Moving average.
  - Linear/Ridge.
- Report MAE, RMSE, sMAPE, and MASE.
- Evaluate the 7-day MVP horizon only. Evaluate other horizons only after they are promoted from post-MVP scope.
- Never create lag or rolling features using future data.
- Save split dates and validation method with every report.

## Uncertainty Rules

- Forecast outputs must return uncertainty intervals once the uncertainty milestone is implemented.
- Report empirical coverage and interval width.
- Do not present interval bounds as guarantees.
- If conformal prediction is not used, document the alternative method and tradeoff.
- Recommendation logic must account for uncertainty through risk level or uncertainty penalty.

## Recommendation Rules

- The recommendation feature is core to the project.
- Always include transport cost in recommendation calculations.
- Always rank by net expected price or risk-adjusted score, not raw forecast price alone.
- Always show alternatives, not only the top mandi.
- Include risk level and reason in the recommendation output.
- Document transport cost assumptions clearly.
- Evaluate recommendation quality with regret@K, average missed profit, or nearest mandi baseline comparison.

## Regime and Anomaly Rules

- Regime/anomaly detection is deferred from the narrowed MVP.
- If implemented later, regime labels must be explainable.
- Future valid labels are:
  - `normal`
  - `volatile`
  - `crisis_anomaly`
- Do not claim a detected anomaly is caused by a specific event unless externally verified.
- Prefer simple rolling volatility and z-score methods before complex models.
- HMM-based regime detection is optional/future.

## Causality Rules

- Do not claim causality casually.
- Do not write statements like "rainfall caused prices to rise" unless a properly scoped causal module exists.
- Use cautious language:
  - "associated with"
  - "consistent with"
  - "may reflect"
  - "predictive signal"
- If causal inference is implemented later, it must include assumptions, DAG, refutation tests, and limitations.

## Architecture Rules

- Keep functions modular and tested.
- In the narrowed MVP, use a single Streamlit app over a separate FastAPI service.
- **Post-MVP promotion (Milestone M):** FastAPI is now active as an additive delivery surface.
  The Streamlit app remains the offline/data-science showcase. The FastAPI service exposes
  `/health`, `/forecast`, and `/recommend` over the same precomputed artifacts. MVP data scope
  (1 crop, 1 state, 7-day horizon) does not widen. Keep it simple and monolithic.
- If FastAPI is added after MVP, keep it simple and monolithic.
- **Post-MVP promotion (Milestone N):** A Next.js static frontend is active as an additive
  delivery surface. It reads pre-exported JSON from `web/public/data/` — no backend required.
  The Streamlit app remains the offline/data-science showcase. MVP data scope (1 crop, 1 state,
  7-day horizon) does not widen.
- Do not add heavy frameworks without justification.
- Use DuckDB as the default local data store. Do not substitute with raw CSV-only or Parquet-only workflows without documented justification. PostgreSQL is allowed only for deployment if documented and approved.
- Use MLflow for experiment tracking and model artifact metadata.
- Do not create hidden coupling between notebooks and production modules.
- Shared logic should live in `src/mandipulse/`, not only notebooks.

## Testing Rules

- Add tests for critical pipeline components.
- Required MVP test areas:
  - Data validation.
  - Feature leakage prevention.
  - Temporal split.
  - Baseline metrics.
  - Forecast response shape.
  - Uncertainty interval shape.
  - Recommendation ranking formula.
  - Streamlit/local artifact loading once the dashboard exists.
- Use small synthetic fixtures where possible.
- Do not require large raw datasets for unit tests.

## Post-MVP API Rules

These rules apply only if FastAPI is promoted after the Streamlit MVP is useful.

- Keep API responses aligned with `docs/API_SPEC.md`.
- Validate all inputs with Pydantic.
- Forecast response must include:
  - Forecast price.
  - Lower bound.
  - Upper bound.
  - Confidence level.
  - Market regime.
- Recommendation response must include:
  - Recommended mandi.
  - Alternatives.
  - Transport cost.
  - Expected net price.
  - Risk level.
  - Reason.
- Use standard error response format.
- Do not silently fallback to dummy predictions in production-like paths.
- API must resolve mandi display names to internal `mandi_id` via metadata lookup.
- If a mandi name cannot be resolved, return `MANDI_NOT_FOUND` error, not a silent fallback.
- Never hardcode mandi name to ID mappings in API route handlers; use the mandi metadata table.

## Dashboard Rules

- The dashboard should feel clear, credible, and data-heavy but readable.
- Do not make it flashy or childish.
- Do not use a generic agriculture theme with decorative visuals that distract from decisions.
- The first screen must communicate mandi decision intelligence.
- Every forecast visualization should show uncertainty.
- Every recommendation view should show transport cost and risk.
- The MVP must show data/model reliability on Data Coverage and Forecast pages. A separate Monitoring page is post-MVP.

## Artifact and Git Rules

- Do not commit secrets, `.env`, credentials, tokens, or API keys.
- Do not commit large model files unless explicitly intended and lightweight.
- Do not commit MLflow runs.
- Do not commit generated raw data files unless small, public, and intentionally sampled.
- Keep `.env.example` updated with required variables.
- Keep `.gitignore` aligned with generated artifacts.
- Keep README and docs aligned with implementation.
- Update tracker after completing tasks.

### Required `.gitignore` Entries

The following must be present in `.gitignore`:

```text
data/raw/
data/interim/
data/processed/
*.duckdb
*.duckdb.wal
mlruns/
artifacts/models/
artifacts/predictions/
.env
__pycache__/
*.pyc
.venv/
.vscode/
.idea/
```

## Documentation Rules

- Update `docs/TRACKER.md` when tasks move status.
- Update `docs/API_SPEC.md` if endpoint contracts change.
- Update `docs/DATA_SCHEMA.md` if tables or columns change.
- Update `docs/ARCHITECTURE.md` if system flow changes.
- Update README after meaningful implementation milestones.
- Document assumptions, limitations, and known risks.

## Stop Conditions

Stop and redesign if the project starts to look like:

> "I predicted crop prices using a model."

The project must remain:

> "I built an offline mandi decision intelligence system for Maharashtra onion markets that forecasts 7-day prices, estimates uncertainty, and recommends the best selling mandi after transparent transport cost."
