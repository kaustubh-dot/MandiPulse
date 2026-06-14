# MandiPulse Tracker

## Scope

Active MVP scope is Onion/Maharashtra, 15 mandis, 7-day horizon, offline Streamlit dashboard.

Anything outside that scope is post-MVP unless explicitly promoted in `TODO.md`, `docs/IMPLEMENTATION_PLAN.md`, and this tracker.

## Status Labels

| Label | Meaning |
|---|---|
| Done | Completed and checked |
| Next | Next implementation target |
| Pending | Not started |
| Deferred | Post-MVP or intentionally out of scope |
| Blocked | Cannot proceed without dependency or decision |

## Current Kanban

### Next

| ID | Status | Task | Depends On |
|---|---|---|---|
| M2-06 | Next | Run observed-only/imputation sensitivity on baseline split | Baseline report |
| M2-07 | Next | Diagnose why Ridge underperforms moving average | M2-06 |
| M3-01 | Next | Train first LightGBM 7-day model only after sensitivity check | M2-07 |
| M3-02 | Next | Compare LightGBM against baselines | M3-01 |
| M3-03 | Next | Save model artifact and feature schema | M3-02 |

### Pending

| ID | Status | Task | Depends On |
|---|---|---|---|
| M4-01 | Pending | Add uncertainty intervals | M3-03 |
| M4-02 | Pending | Evaluate empirical coverage | M4-01 |
| M5-01 | Pending | Fill mandi latitude/longitude metadata | M2-05 |
| M5-02 | Pending | Implement transport cost estimator | M5-01 |
| M5-03 | Pending | Implement risk-adjusted mandi ranking | M4-01, M5-02 |
| M6-01 | Pending | Build Streamlit data coverage page | M2-05 |
| M6-02 | Pending | Build Streamlit forecast page | M3-03 |
| M6-03 | Pending | Build Streamlit recommendation page | M5-03 |

### Done

| ID | Status | Task |
|---|---|---|
| D0-01 | Done | CEDA selected as primary AGMARKNET data path |
| D0-02 | Done | CEDA token validated |
| D0-03 | Done | Project config and dependency files added |
| D1-01 | Done | Raw Onion/Maharashtra CEDA fetch script added |
| D1-02 | Done | Full raw extract saved locally |
| D1-03 | Done | Coverage profile report generated |
| D1-04 | Done | Top-15 Maharashtra onion mandis selected |
| D2-01 | Done | Clean daily panel built |
| D2-02 | Done | Clean panel report generated |
| D2-03 | Done | Leakage-safe 7-day feature table built |
| D2-04 | Done | Feature table report generated |
| D3-01 | Done | Temporal train/validation/test split utility added |
| D3-02 | Done | Seasonal naive, moving-average, and Ridge baselines evaluated |
| D3-03 | Done | Baseline metrics report generated |

### Deferred

| ID | Status | Task |
|---|---|---|
| X-01 | Deferred | FastAPI service |
| X-02 | Deferred | API endpoint test suite |
| X-03 | Deferred | Regime/anomaly detection |
| X-04 | Deferred | Live monitoring/drift platform |
| X-05 | Deferred | 14-day and 30-day forecasts |
| X-06 | Deferred | Tomato or additional crops |
| X-07 | Deferred | Karnataka/Uttar Pradesh or additional states |
| X-08 | Deferred | Arbitrage module |
| X-09 | Deferred | Similar historical days module |
| X-10 | Deferred | Price propagation graph |
| X-11 | Deferred | Causal weather shock module |
| X-12 | Deferred | React frontend |
| X-13 | Deferred | Kubernetes/microservices |

### Blocked

| ID | Status | Task | Blocker |
|---|---|---|---|
| - | - | No blocked tasks | - |

## Current Data Artifacts

| Artifact | Status | Notes |
|---|---|---|
| Raw CEDA CSV | Local only | Ignored under `data/raw/` |
| Clean panel CSV | Local only | Ignored under `data/processed/` |
| Feature table CSV | Local only | Ignored under `data/processed/` |
| Mandi list | Tracked | Coordinates still need to be filled |
| Quality reports | Tracked | Keep updated when data scripts change |
| Baseline report | Tracked | `reports/modeling/baseline_metrics_7d.md` |

## Guardrails

- Do not add deferred work to P0/P1 tasks until the active MVP works.
- Do not require a live API key for modeling or dashboard work.
- Do not use random train/test splits.
- Do not commit `.env`, `.venv`, raw data, processed data, MLflow runs, or generated caches.
