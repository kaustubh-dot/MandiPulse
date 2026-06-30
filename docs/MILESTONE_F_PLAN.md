# Milestone F — Test Coverage + Dashboard Reliability Hardening

**Scope:** strictly within MVP (Onion/Maharashtra, 7-day horizon). No new
features, no new scope. This milestone closes the RULES-required test gap and fixes correctness
issues found in the Milestone E dashboard review.

Read `docs/RULES.md` first. Run `ruff check .` and `black .` before finishing. Do not commit until
asked.

---

## Context

Milestone E (commit `75d6515`) shipped the Streamlit dashboard: landing page plus three pages
(Data Coverage, Forecast, Recommendation). It works and is on-scope. The review found:

- **No tests exist** despite golden fixtures already sitting in `tests/golden/`
  (`clean_mandi_prices.csv`, `feature_table_7d.csv`, `forecast_outputs_7d.csv`,
  `recommendation_outputs_7d.csv`, `baseline_metrics_7d.md`). RULES §Testing requires coverage for
  the recommendation formula, interval shape, temporal split, baseline metrics, forecast response
  shape, and artifact loading — and the "once the dashboard exists" condition is now met.
- Several per-mandi forecasts are **stale** (as-of dates range 2025-10-17 → 2025-10-30, up to 13
  days apart). The landing page hardcodes a single "As-of date: 2025-10-30" and the recommendation
  ranking mixes fresh and stale mandis with no signal to the user.
- The forecast chart hardcodes the string `"90% interval"` instead of reading
  `confidence_level`.
- Tracker is out of date (dashboard tasks still "Next"; `M3-03` "Pending" though
  `persistence.py` exists).

**Decisions already made by the project owner:**
- Scope = **tests + reliability fixes** (both, this milestone).
- Staleness handling = **warn but keep ranking** (show a per-mandi staleness badge/warning; do NOT
  drop stale mandis from the ranking).

---

## Part 1 — Test suite (priority)

Create a `tests/` suite that runs offline against the golden fixtures. `pyproject.toml` already sets
`testpaths=["tests"]` and `pythonpath=["src"]`. Use small synthetic frames where a golden fixture
doesn't fit; do NOT require raw data.

Add these files:

### `tests/conftest.py`
- Fixtures that load each golden CSV from `tests/golden/` via a `GOLDEN_DIR` path constant
  (resolve relative to the test file — do not hardcode an absolute path).
- A `synthetic_features` fixture: a tiny leakage-safe panel (2–3 mandis, ~60 daily rows each) with
  the columns `make_temporal_splits` / `load_trainable_features` require.

### `tests/test_recommend_engine.py` (RULES: recommendation ranking formula)
- `haversine_km`: known-distance sanity check (e.g. ~0 for identical points; a known city pair
  within tolerance).
- `compute_transport_cost_inr_qtl`: linear in distance, independent of load size.
- `risk_level`: boundary cases at `low_max_pct` and `high_min_pct` (≤ low → "low", between →
  "medium", ≥ high → "high").
- `score_recommendations`:
  - `rank` is dense 1..N, sorted by `risk_adjusted_score` descending.
  - `expected_net_price = forecast - transport_cost`.
  - `risk_adjusted_score = expected_net_price - penalty_weight * interval_width`.
  - all RULES-required output columns present (`mandi`, `alternatives` via full table,
    `estimated_transport_cost_inr_qtl`, `expected_net_price_inr_qtl`, `risk_level`, `reason`).
  - raises `ValueError` when a candidate mandi is missing coordinates.

### `tests/test_intervals.py` (RULES: uncertainty interval shape)
- `compute_interval_residuals`: lower ≤ upper; raises when no validation rows for the model.
- `build_backtest`: `covered` is boolean and equals
  `lower ≤ target ≤ upper`; `interval_width = upper - lower`.
- `build_latest_forecast_output`: `lower_bound ≤ forecast_price ≤ upper_bound` for every row;
  required columns present; raises `ValueError` for an unsupported model name.
- `latest_forecastable_rows`: returns exactly one (latest) row per `market_id`.

### `tests/test_splits.py` (RULES: temporal split + leakage prevention)
- `make_temporal_splits`: train_end < validation_start, validation_end < test_start (with the
  horizon purge gap honored — assert the gap is at least `horizon_days`).
- No row appears in more than one split.
- `load_trainable_features`: raises on missing required columns; drops `feature_row_valid == False`.
- `apply_row_filter`: `"observed_only"` keeps only observed rows; unknown filter raises.

### `tests/test_metrics.py` (RULES: baseline metrics)
- `smape` symmetric and 0 for identical series; handles all-zero denominator → NaN.
- `metric_row`: MAE/RMSE match hand-computed values on a tiny series; `mase = mae / scale`.
- `summarize_predictions`: one row per (model, split); sorted by split then MAE.

### `tests/test_app_data_access.py` (RULES: Streamlit/local artifact loading)
- Point the loaders at the golden fixtures (monkeypatch the `paths.*` functions or the module-level
  path helpers used inside `data_access`). Assert each loader returns a DataFrame with expected
  columns and that `date` is parsed to datetime.
- `available_mandis` returns a sorted unique list; `history_for_mandi` filters by `market_id` and
  sorts by date.
- Note: `data_access` imports `streamlit`. Either import lazily or ensure `streamlit` is installed
  in the dev env (it is — `pyproject.toml` lists it). Do not call `st.*` rendering functions in
  tests; only exercise the pure loader/transform functions. If `_missing_artifact_error` calls
  `st.stop()`, test the happy path (fixture exists) to avoid Streamlit runtime coupling.

Run `pytest --cov=mandipulse` and confirm the suite is green before moving on.

---

## Part 2 — Dashboard reliability fixes

### F-1 · Per-mandi staleness warning (warn, keep ranking)
- The forecast artifact carries `as_of_date` per mandi. Define a "freshness reference" =
  `max(as_of_date)` across all mandis (do NOT hardcode a date).
- **Landing page** (`app/streamlit_app.py:18-21`): replace the hardcoded
  `As-of date: **2025-10-30**` with the computed max as-of date, and add "(some mandis older — see
  Forecast/Recommendation pages)".
- **Recommendation page** (`app/pages/3_Recommendation.py`): merge `as_of_date` into the ranked
  table and the top-3 callouts. Add a `staleness_days = max_as_of - mandi_as_of` column. Show a ⚠️
  badge / muted note on any mandi with `staleness_days > 0`. **Keep all mandis in the ranking** —
  do not drop them. Add a one-line caption explaining that older forecasts are still ranked but
  flagged.
- **Forecast page**: already shows per-mandi `as_of_date`; add a small "N days old" note when the
  selected mandi is behind the freshness reference.

### F-2 · Confidence-level label is data-driven
- `app/pages/2_Forecast.py:130`: replace the literal `name="90% interval"` with
  `name=f"{mandi_row['confidence_level']:.0%} interval"`.

### F-3 · Surface which model produced the shipped forecast
- The forecast artifact has `model_name` (currently `moving_average_7d`). On the Forecast page, add
  a short caption clarifying that the **moving-average baseline is the shipped MVP forecaster**
  (LightGBM was trained but did not beat it — test MAE 188 vs 140). Keep it honest and brief; this
  aligns with the existing "Interview Note" in `lightgbm_metrics_7d.md`.

### F-4 · Map robustness (low priority, do if time permits)
- `app/pages/3_Recommendation.py:225-229`: replace the hardcoded center
  `(farmer_lat + 19.5)/2` with the centroid of the plotted mandi coordinates plus the farmer point.
  If `Scattermapbox` emits a deprecation warning in the installed Plotly version, migrate to
  `go.Scattermap` / `map_style="open-street-map"`; otherwise leave it.

---

## Part 3 — Tracker + docs reconciliation

Update `docs/TRACKER.md`:
- Move `M6-01`, `M6-02`, `M6-03` to **Done** (dashboard pages shipped in `75d6515`).
- Re-check `M3-03` (model artifact + feature schema): `persistence.py` exists — mark Done if the
  pipeline actually calls it, else leave Pending with a note.
- Add Milestone F task rows (tests + reliability fixes) under a new section, status Done as each
  lands.
- Keep `M3-04` (beat the moving-average baseline) as Pending — out of scope for F.

Update `README` test instructions if needed (`pytest`, `pytest --cov=mandipulse`).

---

## Definition of done
- `pytest` green, covering all six RULES-required test areas.
- Landing page shows a computed (not hardcoded) freshness date.
- Recommendation + Forecast pages flag stale mandis without dropping them.
- Forecast interval label reads `confidence_level` from the artifact.
- `ruff check .` and `black .` clean.
- Tracker reflects reality.
- No new dependencies, no scope creep, no committed secrets/raw data/artifacts.
