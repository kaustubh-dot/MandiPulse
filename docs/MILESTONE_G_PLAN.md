# Milestone G — Recommendation-Quality Evaluation + F-Review Cleanups

**Scope:** strictly within MVP (Onion/Maharashtra, 7-day horizon). No new
features beyond what RULES already requires. This milestone closes the last open RULES gap — the
project ranks mandis but has never *measured* whether the ranking is good — and folds in the
hardening items found while reviewing Milestone F.

Read `docs/RULES.md` first (esp. §Recommendation Rules and §Testing Rules). Run `ruff check .` and
`black .` before finishing. Do not commit until asked; when done, commit + push and stop for review.

---

## Context

- Milestone E shipped the dashboard; Milestone F (commit `6d5f192`) added a 58-test suite and
  reliability fixes.
- **RULES §Recommendation requires:** "Evaluate recommendation quality with regret@K, average
  missed profit, or nearest mandi baseline comparison." This has never been implemented. The
  recommendation engine ranks mandis but we have no evidence the ranking beats a naive
  "sell at the nearest mandi" policy.
- The owner chose **regret@K vs a nearest-mandi baseline** as the primary metric.

**Decisions already made by the project owner:**
- G scope = **recommendation eval + the F-review cleanups** (both).
- Primary metric = **regret@K** (net price lost by trusting the top-K recommendation vs the
  realized best mandi), with a **nearest-mandi baseline** for comparison.

---

## Part 1 — Recommendation backtest (the RULES gap)

### Concept
For each historical "as-of" date in a backtest window, we already can produce a ranking with the
existing pure `score_recommendations(...)`. The new piece is **realized outcome**: what the farmer
*would actually have earned* selling at each mandi, using the realized price at the forecast target
date (`as_of_date + 7`) minus that mandi's transport cost. Then:

- **regret@K** = `best_realized_net_price − max(realized_net_price over the model's top-K)`.
  regret@1 is the headline number; also report regret@3.
- **nearest-mandi baseline regret** = `best_realized_net_price − realized_net_price(nearest mandi)`.
- The model earns its place only if **mean regret@K < mean nearest-mandi regret**. Report both
  honestly even if the model loses (consistent with the LightGBM honesty note in
  `lightgbm_metrics_7d.md`).

### Realized price source
Use the **clean panel** (`clean_mandi_prices.csv`) — it has `modal_price_inr_qtl` per
`market_id` per `date`. The realized price for mandi *m* at target date *t+7* is that mandi's
`modal_price_inr_qtl` on `as_of_date + 7 days`. If a mandi has no observed row at exactly *t+7*
(holiday/gap), use the nearest observed row within ±2 days; if none, **drop that mandi from that
as-of date's evaluation and log the drop** (RULES: do not silently drop). Prefer `is_observed`
rows over imputed ones for realized outcome — note the choice in the report.

### New module: `src/mandipulse/recommend/evaluation.py`
Pure, testable functions (no I/O):
- `realized_net_price(panel, market_id, target_date, transport_cost, tolerance_days=2) -> float | None`
  — returns realized net price or `None` if no usable observed row.
- `regret_at_k(ranked: pd.DataFrame, realized: dict[int, float], k: int) -> float`
  — `best_realized − max(realized over top-k market_ids)`. Raises/skip-safe if realized is empty.
- `nearest_mandi_regret(ranked, realized, farmer_lat, farmer_lon, mandis) -> float`
  — regret of always choosing the geographically nearest mandi.
- `backtest_recommendations(panel, mandis, forecast_fn_or_table, as_of_dates, k_values, **engine_kwargs)
  -> pd.DataFrame` — one row per (as_of_date) with regret@1, regret@3, nearest-mandi regret, and the
  chosen vs best mandi names. Keep it dependency-light; reuse `score_recommendations`.

**Important — avoid leakage in the backtest:** the forecast used at each as-of date must only use
information available up to that date. The simplest leakage-safe approach for the MVP: use the
**moving-average baseline forecast computed from the feature table's `rolling_mean_7` at each
as-of row** (the same shipped model), NOT the single static `forecast_outputs_7d.csv` (which is
only the latest date). Document this clearly. If wiring per-date forecasts is too involved, an
acceptable MVP fallback is to backtest over the **validation/test split dates only**, reusing the
existing `lightgbm_predictions_7d.csv` / baseline predictions which already carry leakage-safe
`prediction` + realized `target_price_t_plus_7` per row — confirm which is simpler and note the
choice.

### New script: `scripts/run_recommendation_backtest_7d.py`
- Follows the existing pipeline-script conventions (argparse, config-driven defaults from
  `configs/recommendation.yaml`, `sys.path.insert` shim, `main() -> int`).
- Inputs: clean panel, mandi metadata, the leakage-safe per-date forecasts (per the decision above),
  a backtest window (default: the test split), `--k` values (default `[1, 3]`), farmer location
  (default Nashik, same as the recommendation script).
- Outputs:
  - `artifacts/recommendations/recommendation_backtest_7d.csv` (per-as-of-date rows) — **git-ignored**
    (it's a generated artifact under `artifacts/recommendations/`, already in `.gitignore`).
  - `reports/modeling/recommendation_backtest_7d.md` (tracked) — summary table with:
    mean/median regret@1, regret@3, mean nearest-mandi regret, **win rate** (% of as-of dates where
    the model's top-1 net price ≥ nearest-mandi net price), n_dates, n_mandis, split dates, and a
    plain-language verdict. Include the standard "decision support, not a guarantee" caveat and the
    realized-price tolerance/drop assumptions.

### Add a path helper
`src/mandipulse/paths.py` → `recommendation_backtest_path()` and the report alongside the existing
helpers. Do not hardcode paths anywhere.

---

## Part 2 — F-review cleanups

### G-1 · Extract + test the staleness helper (highest-value cleanup)
- Add to `src/mandipulse/app/data_access.py`:
  `add_staleness_days(forecasts: pd.DataFrame) -> pd.DataFrame` — returns a **copy** with a
  `staleness_days` column = `max(as_of_date) − as_of_date` in days, parsing `as_of_date` robustly.
- Replace the hand-written staleness arithmetic on all three places
  (`app/streamlit_app.py`, `app/pages/2_Forecast.py`, `app/pages/3_Recommendation.py`) with calls to
  this helper. **Remove the in-place mutation of the cached frame** on the Recommendation page
  (line ~41) — use the returned copy.
- Add `tests/test_staleness.py`: freshest mandi → 0 days; older mandi → correct positive delta;
  all-same-date → all zeros; result is a copy (original unmutated).

### G-2 · Test the missing-artifact + duplicate-market_id guards
- In `tests/test_app_data_access.py`: a test that monkeypatches a loader's path to a nonexistent
  file and asserts `_missing_artifact_error` calls `st.stop()` (patch `st.stop`/`st.error` to spy).
- In `tests/test_recommend_engine.py`: a test that feeds `score_recommendations` a `forecasts`
  frame with a duplicate `market_id` and asserts the `validate="one_to_one"` merge raises.

### G-3 · Backtest unit tests
- `tests/test_recommend_evaluation.py`: small synthetic panel + ranking where the realized best
  mandi is known by construction. Assert:
  - `regret_at_k` is 0 when the top-1 is the realized best; positive otherwise; monotonically
    non-increasing as K grows.
  - `realized_net_price` returns `None` when no observed row within tolerance; picks the nearest
    observed row otherwise.
  - `nearest_mandi_regret` matches a hand-computed value.

---

## Part 3 — Tracker + docs

Update `docs/TRACKER.md`:
- Add a Milestone G section; mark G tasks Done as they land.
- Add `recommendation_backtest_7d.md` (tracked) and `recommendation_backtest_7d.csv` (local only)
  to the Current Data Artifacts table.
- If the backtest shows the model loses to the nearest-mandi baseline, that is a legitimate result —
  record it and leave `M3-04` (beat the baseline) as the open lever. Do not fudge the numbers.

Update the pipeline order note in README to include
`run_recommendation_backtest_7d.py` after `build_recommendations_7d.py`.

---

## Definition of done
- `recommend/evaluation.py` implements regret@K + nearest-mandi baseline as pure functions.
- `run_recommendation_backtest_7d.py` produces a tracked report with mean regret@1/@3, nearest-mandi
  regret, win rate, split dates, and an honest verdict.
- Staleness logic lives in one tested helper; no in-place mutation of cached frames.
- Missing-artifact and duplicate-market_id guards are tested.
- `pytest` green (existing 58 + new tests); `ruff check .` and `black .` clean.
- Tracker + README pipeline order updated.
- No new dependencies, no scope creep, no committed secrets/raw data/artifacts.
