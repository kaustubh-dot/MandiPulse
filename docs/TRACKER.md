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

### Done (Milestone L — clone-runnable demo + Streamlit Cloud deploy)

| ID | Status | Task | Depends On |
|---|---|---|---|
| L-01 | Done | `build_demo_sample.py`: slim committed bundle in `data/sample/` (2.4 MB, parity-verified) | - |
| L-02 | Done | Read-layer fallback in `data_access.py`: full artifact → demo sample → stop; `RUNNING_ON_SAMPLE` flag | L-01 |
| L-03 | Done | Commit bundle; allow `data/sample/` in `.gitignore` | L-01 |
| L-04 | Done | `requirements.txt` already present; Streamlit Cloud deploy instructions in README | L-02, L-03 |
| L-05 | Done | README overhaul: 2-min quickstart, honest results table, architecture diagram, deploy steps | L-04 |
| L-06 | Done | `test_demo_fallback.py` (8 tests); fix 2 broken existing tests; coverage floor 69→70; 147 tests | all |

**Dashboard runs from a fresh clone on the bundled Oct 2025 snapshot.** No pipeline run required.
To deploy: connect repo on share.streamlit.io, set entrypoint to `app/streamlit_app.py`, no secrets needed.

### Done (Milestone K — release hardening + freeze, v0.1-mvp)

| ID | Status | Task | Depends On |
|---|---|---|---|
| K-01 | Done | End-to-end pipeline smoke test: 4 tests guard clean-panel→features→predictions→recommendations wiring | - |
| K-02 | Done | Cover `modeling/tracking.py` (MLflow glue): URI resolution + absent-degradation tests; tracking.py 73% | - |
| K-03 | Done | Raise `--cov-fail-under` to 69; post-K coverage 70% | K-01, K-02 |
| K-04 | Done | `RELEASE.md` runbook, TRACKER freeze note, README status line | K-01..K-03 |

**MVP is FROZEN at v0.1-mvp.** 139 tests, 70% coverage. Post-MVP work requires RULES.md + TRACKER scope promotion.

### Done (Milestone J — DuckDB read-layer + coverage gating)

| ID | Status | Task | Depends On |
|---|---|---|---|
| J-01 | Done | `read_csv_via_duckdb` in `data/store.py` (in-memory DuckDB over CSV; CSV stays source of truth) | - |
| J-02 | Done | Route `data_access.py` reads through the store; preserve stop-vs-degrade guards | J-01 |
| J-03 | Done | Route backtest/build_recommendations input reads through the store | J-01 |
| J-04 | Done | `pytest --cov-fail-under=60` in `pyproject.toml`; post-J coverage 61%; floor set at 60 | - |
| J-05 | Done | Store tests (parity, date, missing-file) + util tests (formatting, slugify, make_mandi_id); 127 tests | J-01 |
| J-06 | Done | Docs: ARCHITECTURE storage decision + rationale, TRACKER, README; MVP loop RULES-complete | J-02 |

Plan: `docs/MILESTONE_J_PLAN.md`. Decision: DuckDB is a **read-layer over CSV**, not a storage rewrite —
CSV stays on-disk source of truth. Data-access + tests + docs only; no modeling/forecaster/number changes.

**The MVP loop is now RULES-complete.** No Milestone K is queued. Post-MVP levers are in TRACKER §Deferred.

### Done (Milestone I — residual-target reformulation, M3-04)

| ID | Status | Task | Depends On |
|---|---|---|---|
| I-01 | Done | `predict_lightgbm_residual` in `lightgbm_model.py`; wired into `train_lightgbm_7d.py` alongside level model | D3-06 |
| I-02 | Done | Report + Decision section: residual MAE 195.63 vs baseline 139.57; promotion = NO | I-01 |
| I-03 | Done | No-op — baseline wins on test; moving-average remains shipped forecaster, nothing downstream changed | I-02 |
| I-04 | Done | Tests: reconstruction correctness + leakage guard (106 tests total) | I-01 |
| I-05 | Done | Docs: README modeling status, TRACKER; ARCHITECTURE unchanged (forecaster not promoted) | I-02 |

Result: residual-LightGBM test MAE **195.63** vs moving-average **139.57** INR/quintal — baseline wins. Moving-average remains the shipped forecaster. Honest negative result documented in `reports/modeling/lightgbm_metrics_7d.md`.

### Done (Milestone H — surface the backtest in the dashboard, `1e34297`)

| ID | Status | Task | Depends On |
|---|---|---|---|
| H-01 | Done | Extract tested `summarize_backtest()` into `evaluation.py`; rewrite `write_report` to use it | G-01 |
| H-02 | Done | Add optional `load_recommendation_backtest()` loader (returns None when absent) | G-01 |
| H-03 | Done | Add "Historical performance" section to Recommendation page; graceful degrade | H-01, H-02 |
| H-04 | Done | Tests: `summarize_backtest` + None-returning loader | H-01, H-02 |
| H-05 | Done | Docs refresh: README, TRACKER, ARCHITECTURE | H-03 |

Plan: `docs/MILESTONE_H_PLAN.md`. Dashboard + docs only — no modeling or data-store changes.

### Done (Milestone G — recommendation eval + F-review cleanups, `4437ed9` + fix `b53de0f`)

| ID | Status | Task |
|---|---|---|
| G-01 | Done | Recommendation backtest: regret@K + nearest-mandi baseline (`recommend/evaluation.py` + `run_recommendation_backtest_7d.py`); regret@1 296.3 vs nearest 370.1, beats nearest 78.8% |
| G-02 | Done | Extract + test `add_staleness_days` helper; remove cached-frame mutation |
| G-03 | Done | Test missing-artifact and duplicate-market_id guards |
| G-04 | Done | Review fix: drop market_name merge collision (was silently 0 rows); raise on scoring failure; correct win-rate labels; 87 tests |

Plan: `docs/MILESTONE_G_PLAN.md`. Primary metric: regret@K vs nearest-mandi.

### Done (Milestone F — tests + reliability hardening, `6d5f192`)

| ID | Status | Task |
|---|---|---|
| F-01 | Done | RULES-required pytest suite: 58 tests, 6 test files, golden fixtures |
| F-02 | Done | Per-mandi forecast staleness warning on Recommendation + Forecast pages (warn, keep ranking) |
| F-03 | Done | Data-driven confidence-level label on forecast chart (`confidence_level` from artifact) |
| F-04 | Done | Surface shipped forecaster (moving-average) vs benched LightGBM on Forecast page |
| F-05 | Done | Map center computed from centroid of all plotted points + farmer location |

### Pending

| ID | Status | Task | Depends On |
|---|---|---|---|
| J-01 | Pending | Milestone J: adopt DuckDB as local store per RULES §Architecture (or document justification) + `pytest --cov` gating | - |

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
| D3-04 | Done | Observed-only baseline sensitivity report generated |
| D3-05 | Done | Ridge underperformance diagnosed as a global linear-model limitation |
| D3-06 | Done | First LightGBM 7-day model trained and compared against baselines |
| D4-01 | Done | Residual interval calibration script added for the MVP baseline |
| D4-02 | Done | Empirical interval coverage measured on held-out test data |
| D4-03 | Done | Forecast output artifact with lower and upper bounds generated |
| D5-01 | Done | Mandi latitude/longitude metadata filled |
| D5-02 | Done | Transport cost estimator implemented |
| D5-03 | Done | Risk-adjusted recommendation ranking artifact generated |
| M3-03 | Done | Save model artifact and feature schema (`train_lightgbm_7d.py` → `persistence.py`) |
| M6-01 | Done | Build Streamlit data coverage page (`75d6515`) |
| M6-02 | Done | Build Streamlit forecast page (`75d6515`) |
| M6-03 | Done | Build Streamlit recommendation page (`75d6515`) |

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
| Mandi list | Tracked | `data/external/mvp_mandis.csv` now includes latitude/longitude |
| Quality reports | Tracked | Keep updated when data scripts change |
| Baseline report | Tracked | `reports/modeling/baseline_metrics_7d.md` |
| Baseline sensitivity report | Tracked | `reports/modeling/baseline_sensitivity_7d.md` |
| LightGBM report | Tracked | `reports/modeling/lightgbm_metrics_7d.md` |
| Forecast interval report | Tracked | `reports/modeling/forecast_intervals_7d.md` |
| Forecast output artifact | Local only | `artifacts/forecasts/forecast_outputs_7d.csv` |
| Recommendation report | Tracked | `reports/modeling/recommendation_report_7d.md` |
| Recommendation artifact | Local only | `artifacts/recommendations/recommendation_outputs_7d.csv` |
| Recommendation backtest artifact | Local only | `artifacts/recommendations/recommendation_backtest_7d.csv` |
| Recommendation backtest report | Tracked | `reports/modeling/recommendation_backtest_7d.md` |

## Guardrails

- Do not add deferred work to P0/P1 tasks until the active MVP works.
- Do not require a live API key for modeling or dashboard work.
- Do not use random train/test splits.
- Do not commit `.env`, `.venv`, raw data, processed data, MLflow runs, or generated caches.
