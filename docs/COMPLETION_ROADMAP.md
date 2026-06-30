# MandiPulse India — End-to-End Completion Roadmap

> Execution plan for finishing the MVP.
> Each milestone is independently runnable and ends with a concrete verification command.

## Context

MandiPulse is a transport-cost-aware mandi decision-intelligence MVP (Onion / Maharashtra, 7-day horizon, offline static showcase). Data ingestion, cleaning, feature engineering, baselines, LightGBM, uncertainty intervals, and the recommendation engine are **already implemented and producing artifacts**. What remains, per `docs/PRD.md` (P0) and `docs/IMPLEMENTATION_PLAN.md` (Milestone 6 + open items):

- **No Streamlit dashboard** (the headline P0 deliverable — US-07).
- **No MLflow tracking** (P0 — US-06).
- **No saved model / feature schema** (TRACKER M3-03).
- **No tests** despite `pyproject.toml` configuring `pytest`.
- **8 code-review findings** open, two of them correctness-affecting (recommendation config ignored; fragile `mandi_id` string join).
- Shared code (`slugify`, `dataframe_to_markdown`, `payload_records`, all modeling functions) is **duplicated across `scripts/`** and `train_baselines_7d.py` is imported as a de-facto library from `scripts/`, which only resolves by accident of `sys.path`.

**Locked decisions** (from user): full remaining MVP · full package refactor into `src/mandipulse/` · stay offline on cached data (ends 2025-10-30) · `configs/recommendation.yaml` is the source of truth for recommendation params.

**Outcome:** a reproducible `data → model → artifacts → dashboard` pipeline, importable package code, MLflow-tracked experiments, a test suite, refreshed docs, and a one-command demo (`streamlit run app/streamlit_app.py`) that runs with no API key.

---

## Target end-state structure

```
src/mandipulse/
├── __init__.py                  # export version + key public API
├── config.py                    # (exists) + add load_config helpers per domain
├── paths.py                     # NEW: centralized artifact/report/data path resolution
├── utils/
│   ├── __init__.py
│   ├── text.py                  # NEW: slugify, make_mandi_id (single source of truth)
│   ├── formatting.py            # NEW: dataframe_to_markdown
│   └── io.py                    # NEW: save_json, load_json, payload_records, save_dataframe
├── data/
│   ├── __init__.py
│   └── ceda_client.py           # (exists, unchanged)
├── features/
│   ├── __init__.py
│   ├── clean_panel.py           # NEW: logic moved from build_clean_onion_panel.py
│   └── feature_table.py         # NEW: logic moved from build_feature_table.py
├── modeling/
│   ├── __init__.py
│   ├── columns.py               # NEW: TARGET_COLUMN, NUMERIC_FEATURES, CATEGORICAL_FEATURES, etc.
│   ├── splits.py                # NEW: SplitConfig, SplitDates, make_temporal_splits, apply_row_filter, load_trainable_features
│   ├── metrics.py               # NEW: smape, mase_scale, metric_row, per_market_metrics, summarize_predictions
│   ├── baselines.py             # NEW: build_ridge_pipeline, predict_baselines
│   ├── lightgbm_model.py        # NEW: build_lightgbm_pipeline, predict_lightgbm
│   ├── intervals.py             # NEW: residual interval calibration + latest-forecast assembly
│   ├── persistence.py           # NEW: save/load model artifact + feature schema JSON
│   └── tracking.py              # NEW: thin MLflow wrapper (start_run, log params/metrics/artifacts)
├── recommend/
│   ├── __init__.py
│   └── engine.py                # NEW: haversine, transport cost, risk scoring (config-driven)
└── app/
    ├── __init__.py
    └── data_access.py           # NEW: cached loaders for artifacts used by the dashboard

scripts/                         # become THIN CLIs (argparse → call package functions)
app/
├── streamlit_app.py             # NEW: entrypoint, navigation
└── pages/
    ├── 1_Data_Coverage.py       # NEW
    ├── 2_Forecast.py            # NEW
    └── 3_Recommendation.py      # NEW
tests/                           # NEW pytest suite (see Milestone F)
```

**Reuse, do not re-create:** `mandipulse.config.load_yaml_config` / `resolve_project_path` (`src/mandipulse/config.py`) already load YAML and resolve paths — every new module uses these instead of `pd.read_csv`-with-raw-paths or re-deriving `PROJECT_ROOT`.

---

## Guiding rules for the implementer

1. **One behavior change per milestone**, each ending green before the next.
2. **Move, then thin**: when relocating logic into the package, keep function bodies byte-identical first (pure move + import rewrite), verify outputs are unchanged via a golden-file diff, *then* apply fixes.
3. **Golden-file safety net**: before refactoring, copy current artifacts to `tests/golden/` and assert the regenerated CSVs match (numeric tolerance 1e-6). This catches accidental behavior drift during the move.
4. Respect `docs/RULES.md`: temporal split only, no future-data features, INR/quintal, never commit raw data / `.env` / model artifacts / MLflow runs (verify `.gitignore` covers `mlruns/`, `artifacts/`).
5. Match existing style: `from __future__ import annotations`, modern hints, dataclasses, ruff/black @ 100 cols. Run `ruff check . && black . && pytest` at the end of every milestone.

---

## Milestone A — Foundation: shared utils + package skeleton + golden files

**Goal:** kill duplication and create the import surface the rest depends on. No output should change.

Tasks:
1. Create `tests/golden/` and copy the current `artifacts/forecasts/forecast_outputs_7d.csv`, `artifacts/recommendations/recommendation_outputs_7d.csv`, `reports/modeling/baseline_metrics_7d.md`, feature/clean CSVs (regenerate if absent by running the existing pipeline once — see Verification order).
2. Add `src/mandipulse/utils/{__init__,text,formatting,io}.py`:
   - `text.slugify(value)` — exact body from `scripts/build_clean_onion_panel.py`.
   - `text.make_mandi_id(market_name, state="maharashtra")` → `f"{state}__{slugify(market_name)}"` — the **single** definition that replaces both inline constructions in `build_clean_onion_panel.py` and `build_recommendations_7d.py`.
   - `formatting.dataframe_to_markdown(df)` — replaces 5 copies across scripts.
   - `io.save_json`, `io.load_json`, `io.payload_records`, `io.save_dataframe(df, path)` (does `mkdir(parents=True)` + `to_csv(index=False)`).
3. Add `src/mandipulse/paths.py` with helpers that read `configs/*.yaml` paths via `load_yaml_config` and return resolved `Path`s (artifact dirs, report dirs, processed data). Reduces hardcoded path strings.
4. Rewrite the 5 scripts' helper usages to import from the package; delete the local copies. Add the `sys.path.insert(0, PROJECT_ROOT/"src")` shim to any script that now imports `mandipulse` (pattern already used in `scripts/fetch_ceda_onion_maharashtra.py`).

Acceptance: `python scripts/build_clean_onion_panel.py && python scripts/build_feature_table.py` reproduce byte-identical (≤1e-6) CSVs vs golden. `ruff check . && black --check .` clean.

---

## Milestone B — Modeling package: move shared modeling code out of `scripts/`

**Goal:** make `train_baselines_7d.py` a thin CLI; relocate its library symbols into `src/mandipulse/modeling/`. Fixes the fragile cross-script import pattern.

Tasks:
1. Move column constants → `modeling/columns.py`; `SplitConfig`/`SplitDates`/`make_temporal_splits`/`apply_row_filter`/`load_trainable_features` → `modeling/splits.py`; `smape`/`mase_scale`/`metric_row`/`per_market_metrics`/`summarize_predictions` → `modeling/metrics.py`; `build_ridge_pipeline`/`predict_baselines` → `modeling/baselines.py`. Move bodies verbatim.
2. Move `build_lightgbm_pipeline`/`predict_lightgbm` (`scripts/train_lightgbm_7d.py`) → `modeling/lightgbm_model.py`; interval functions (`scripts/build_forecast_intervals_7d.py`: `compute_interval_residuals`, `build_backtest`, `summarize_backtest`, `build_latest_forecast_output`, `latest_forecastable_rows`) → `modeling/intervals.py`.
3. Rewrite **all** of `scripts/train_baselines_7d.py`, `train_lightgbm_7d.py`, `run_baseline_sensitivity_7d.py`, `build_forecast_intervals_7d.py` to import from `mandipulse.modeling.*` (no more `from train_baselines_7d import ...`). Each keeps only its `parse_args()` + `main()` orchestration + report writing.
4. Drop unused imports (`summarize_predictions` in `build_forecast_intervals_7d.py`).

Acceptance: `python scripts/train_baselines_7d.py` then `python scripts/build_forecast_intervals_7d.py` reproduce golden metrics/forecasts (≤1e-6). All four scripts run from repo root **and** via `python -m`.

---

## Milestone C — Correctness fixes (code-review findings #1–#4)

**Goal:** apply the verified review fixes now that code is centralized.

Tasks:
1. **#1 Recommendation config wiring** → move recommendation logic into `recommend/engine.py`; have `scripts/build_recommendations_7d.py` load `configs/recommendation.yaml` via `load_yaml_config` and pass config values as the **defaults** (CLI flags still override). Map keys: `transport_cost.road_distance_factor`→1.3, `transport_cost.cost_per_km_per_quintal`→4.0, `ranking.uncertainty_penalty_weight`→0.3, `risk_thresholds.low_max_interval_pct`/`high_min_interval_pct`→0.10/0.25 in `risk_level()`. Regenerate the recommendation artifact + report (numbers will change — expected and intended).
2. **#2 mandi_id join** → in `recommend/engine.py`, prefer joining forecasts↔mandis on `market_id`. Add `market_id` to the forecast artifact's `output_columns` in `modeling/intervals.py` (`build_latest_forecast_output`) so the stable key is available; fall back to `mandi_id` only if `market_id` absent. Keep `validate="one_to_one"` but join on the numeric key.
3. **#3 val/test purge** → add an explicit purge gap of `horizon_days` in `make_temporal_splits` (default on): set `validation_end = test_start - 1 - horizon_days`. Update the report wording to state both purges. Re-run; coverage may shift slightly.
4. **#4 calibration-coverage labeling** → in `summarize_backtest` / interval report, label the validation row as `coverage (in-sample calibration)` and test as `coverage (out-of-sample)`.

Acceptance: recommendation report shows config-driven params (road 1.3, penalty 0.3, thresholds 10/25); forecast artifact contains `market_id`; baseline report documents train→val and val→test purges. Update `tests/golden/` to the new intended outputs after manual review.

---

## Milestone D — Model & feature-schema persistence + MLflow tracking (P0: US-06, M3-03)

**Goal:** make experiments reproducible and persist the trained model.

Tasks:
1. `modeling/persistence.py`: `save_model(pipeline, path)` / `load_model(path)` via `joblib`; `save_feature_schema(path)` writing JSON `{numeric_features, categorical_features, target, horizon_days, created_at}` to `artifacts/models/`. Wire into `scripts/train_lightgbm_7d.py`.
2. `modeling/tracking.py`: thin wrapper over `mlflow` reading `configs/app.yaml:mlflow.tracking_uri`. Degrade gracefully (no-op + warning) if `mlflow` import fails.
3. Instrument `train_baselines_7d.py`, `train_lightgbm_7d.py`, `build_forecast_intervals_7d.py`: log split config, model params, MAE/RMSE/sMAPE/MASE + empirical coverage to MLflow; log report markdown + prediction CSV as artifacts.
4. Confirm `.gitignore` excludes `mlruns/` and `artifacts/models/`.

Acceptance: `python scripts/train_lightgbm_7d.py` creates `artifacts/models/lightgbm_7d.joblib`, `feature_schema_7d.json`, and an MLflow run under `mlruns/`. `mlflow ui` lists runs for baselines, lightgbm, intervals.

---

## Milestone E — Streamlit dashboard (P0: US-07, Milestone 6)

**Goal:** 3-page offline dashboard reading local artifacts, no API key. Follows `docs/APP_FLOW.md` + `docs/DESIGN.md`.

Shared layer first:
- `src/mandipulse/app/data_access.py`: `@st.cache_data` loaders for `forecast_outputs_7d.csv`, `recommendation_outputs_7d.csv`, the clean panel, feature table, and report markdowns; plus `available_mandis()`, `history_for_mandi(market_id)`. All paths via `mandipulse.paths`. Surface a clear error if an artifact is missing.
- `app/streamlit_app.py`: title, sidebar nav, global "as-of date" caveat banner (data ends 2025-10-30), reads `configs/app.yaml:dashboard.port`.

Page contracts:
- **`pages/1_Data_Coverage.py`** — KPI strip (selected mandis, latest date, observed/imputed/trainable rows); per-mandi coverage bar chart (Plotly); missingness table; data caveat panel.
- **`pages/2_Forecast.py`** — mandi selector (15 mandis); summary metrics (`forecast_price_inr_qtl`, `lower_bound_inr_qtl`, `upper_bound_inr_qtl`, `confidence_level`); historical modal-price line chart with forecast point + shaded interval; baseline comparison table.
- **`pages/3_Recommendation.py`** — inputs (farmer lat/long defaults from config, quantity, transport cost slider seeded from `configs/recommendation.yaml`); calls `recommend.engine` **live** on the loaded forecast artifact so sliders recompute rankings; ranked table; `st.map` of farmer + mandis with top pick highlighted; top-3 alternatives callout.

Use only existing deps (`streamlit`, `plotly`, `pandas`). Risk colors: green/amber/red per DESIGN.md.

Acceptance: `streamlit run app/streamlit_app.py` opens all 3 pages with no API key; mandi selection updates forecast; moving the transport-cost slider re-ranks recommendations.

---

## Milestone F — Tests

**Goal:** pytest suite covering correctness-critical logic. `pyproject.toml` already sets `testpaths=["tests"]`, `pythonpath=["src"]`.

Create `tests/`:
- `test_text.py` — `slugify` edge cases; `make_mandi_id` stability; collision detection across the 15 real mandi names.
- `test_splits.py` — `make_temporal_splits` enforces train<validation<test ordering **and** both purge gaps; empty-partition raises.
- `test_no_leakage.py` — feature table: assert no lag/rolling column uses future rows.
- `test_metrics.py` — `smape`/`mase_scale`/`metric_row` against hand-computed values; division-by-zero guards return NaN not inf.
- `test_intervals.py` — `lower_residual <= upper_residual`; coverage computation on a toy frame.
- `test_recommend.py` — `haversine_km` vs known city distances (±1%); transport cost monotonic in distance; `risk_level` thresholds match config; ranking sorts by risk-adjusted score.
- `test_persistence.py` — round-trip save/load model + feature schema.
- `test_pipeline_smoke.py` — run clean→features→baselines on a tiny fixture CSV under `tests/fixtures/`.

Acceptance: `pytest -q` green; `pytest --cov=mandipulse` reports coverage on the moved modules.

---

## Milestone G — Docs refresh

Update, don't rewrite:
- **`docs/TRACKER.md`** — flip M3-03, M6-01/02/03 and MLflow/tests rows to Done; add rows for the refactor + review fixes.
- **`docs/IMPLEMENTATION_PLAN.md`** — mark Milestone 6 done; add "Package layout" section.
- **`TODO.md`** — replace with live checklist; check off completed items.
- **`README.md`** — add "Run the dashboard", "Experiment tracking", and "Run tests" sections; update pipeline command list.
- **`docs/ARCHITECTURE.md`** — update data-flow diagram to include package layer, MLflow, and dashboard.
- Project docs — add new pipeline order and `pytest`/`streamlit` commands.

Acceptance: a new contributor can go README → install → run pipeline → `streamlit run` → `pytest` with no missing step.

---

## Canonical end-to-end run order

```bash
python -m pip install -e ".[dev]"
# Pipeline (offline, no API key — raw CEDA dump already cached):
python scripts/build_clean_onion_panel.py
python scripts/build_feature_table.py
python scripts/train_baselines_7d.py
python scripts/run_baseline_sensitivity_7d.py
python scripts/train_lightgbm_7d.py          # saves model + schema + MLflow run
python scripts/build_forecast_intervals_7d.py
python scripts/build_recommendations_7d.py    # now config-driven
# Quality gates:
ruff check . && black --check . && pytest -q
# Demo:
streamlit run app/streamlit_app.py
mlflow ui      # optional, inspect tracked runs
```

---

## Live TODO checklist

- [ ] **A1** Golden artifacts snapshot in `tests/golden/`
- [ ] **A2** `utils/{text,formatting,io}.py` + `paths.py`; delete 5 duplicate helper copies
- [ ] **A3** Single `make_mandi_id` used by panel + recommendations
- [ ] **B1** Modeling code moved to `src/mandipulse/modeling/*`
- [ ] **B2** `scripts/*` reduced to thin CLIs; no `from train_baselines_7d import`
- [ ] **C1** `build_recommendations` reads `configs/recommendation.yaml` (config wins)
- [ ] **C2** Forecast artifact carries `market_id`; join on it
- [ ] **C3** val→test purge gap added; reports document both purges
- [ ] **C4** Interval report labels in-sample vs out-of-sample coverage
- [ ] **D1** `joblib` model + `feature_schema_7d.json` persisted
- [ ] **D2** MLflow tracking wired into 3 training scripts; `mlruns/` gitignored
- [ ] **E1** `app/streamlit_app.py` + `data_access.py`
- [ ] **E2** Data Coverage page
- [ ] **E3** Forecast page
- [ ] **E4** Recommendation page (live re-ranking)
- [ ] **F1** pytest suite (text, splits, leakage, metrics, intervals, recommend, persistence, smoke)
- [ ] **G1** Docs: TRACKER, IMPLEMENTATION_PLAN, TODO, README, ARCHITECTURE

## Out of scope (deferred, per RULES.md)

FastAPI service, SHAP explainability, CatBoost, 14/30-day horizons, additional crops/states, regime/anomaly detection, live data refresh. Do not add these or surface them in dashboard nav.
