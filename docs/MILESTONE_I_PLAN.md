# Milestone I Plan — Beat the moving-average baseline honestly (M3-04)

**Goal:** Give the LightGBM forecaster a fair shot at beating `moving_average_7d` by **reformulating the
target as a residual over the baseline**, evaluate it under the same temporal/metrics rules, and **only
promote it if it actually wins on the test split**. If it still loses, keep moving-average shipped and
report the result honestly — that is an acceptable, RULES-compliant outcome.

This milestone is **modeling only**. Do **not** touch the dashboard (Milestone H is done) or adopt DuckDB
(Milestone J). Keep MVP scope: Onion/Maharashtra, 7-day horizon, 15 mandis, temporal split only.

---

## Why this, why now

`reports/modeling/lightgbm_metrics_7d.md` is the open wound: LightGBM is **188.2** test MAE vs
**139.57** for `moving_average_7d` — 48.6 INR/qtl worse — yet nearly ties on validation (129.4 vs 126.1).
That validation/test gap is the signature of an **absolute-level** model overfitting to in-sample price
levels and then eating distribution shift. The model is forced to re-derive the entire price from
features when the baseline already nails the level.

The fix is the lever TRACKER has parked as M3-04: **predict the residual the baseline leaves behind**,
not the raw price. `final_prediction = rolling_mean_7 + model(features)`. If the model learns nothing it
predicts ~0 residual and collapses back to the baseline — so it can only add value where real signal
exists, and the validation/test gap shrinks because the target variance is far smaller.

RULES §Forecasting is binding here: temporal split only, never leak future, always compare against
baselines, report MAE/RMSE/sMAPE/MASE, save split dates. None of that relaxes.

---

## Critical constraints (read before coding)

1. **No leakage, ever.** The residual target is `target_price_t_plus_7 - rolling_mean_7`. Both terms
   already exist per row and `rolling_mean_7` is past-only (built in `build_feature_table.py` with
   `min_periods=window` on a backward window). Do **not** introduce any new feature that peeks at
   `t+1..t+7`. Reconstruct the price prediction by adding `rolling_mean_7` back — `rolling_mean_7` is a
   feature column, not the target, so this is safe.

2. **Keep the honest benchmark.** Do **not** delete or replace the existing absolute-level LightGBM run.
   Add the residual model as a **new model row** (`lightgbm_residual`) alongside it so the report shows
   level-LightGBM, residual-LightGBM, and all baselines side by side. The story "residual reformulation
   closed/erased the gap" only lands if both are visible.

3. **Promotion is earned on TEST, not validation.** The shipped forecaster (`moving_average_7d`) only
   changes if `lightgbm_residual` beats it on **test MAE**. Validation-only wins do not promote — that is
   exactly the trap that produced the current overfit. If it loses on test, the deliverable is the honest
   comparison report + an updated Interview Note; the dashboard and `baseline_predictions_7d.csv` keep
   using moving-average.

4. **Same split, same metrics, saved.** Reuse the existing temporal split utility and
   `summarize_predictions` / `per_market_metrics`. Every report must carry split dates and all four
   metrics (MAE, RMSE, sMAPE, MASE), overall and per-mandi, as the current one does.

5. **Windows console:** keep unicode arrows (→ … ± × —) out of any string that reaches `print()`. Reports
   are written UTF-8 — arrows are fine *there only*. (Same rule that bit Milestone H.)

---

## Tasks

### I-01 — Add a residual-target training path to `train_lightgbm_7d.py`

- Compute the residual target in the trainer (not the feature table — keep the feature schema stable):
  `y_residual = train[TARGET_COLUMN] - train["rolling_mean_7"]`. Train a LightGBM regressor on the
  **existing** `NUMERIC_FEATURES + CATEGORICAL_FEATURES` against `y_residual`.
- Reconstruct predictions: `prediction = split_df["rolling_mean_7"] + model.predict(X)`. Emit these as a
  new model named `lightgbm_residual` in the same predictions frame the others use, so
  `summarize_predictions` / `per_market_metrics` pick it up with zero special-casing.
- Keep the current absolute-level `lightgbm` run intact and in the output. Both must appear in the metrics
  CSV and the report.
- Factor the residual fit/predict into `src/mandipulse/modeling/lightgbm_model.py` (e.g.
  `predict_lightgbm_residual(...)` mirroring `predict_lightgbm`) so the logic is importable and testable,
  not inlined in the script. Reuse the same hyperparameters as the level model for a fair comparison
  (only the target changes).

### I-02 — Report + promotion decision

- Extend `write_report` in `train_lightgbm_7d.py` so the summary table includes `lightgbm_residual`, and
  add a **Decision** section that states, in plain language and from the numbers (no hardcoding):
  - residual-LightGBM test MAE vs `moving_average_7d` test MAE, and the delta;
  - whether the residual model **beats** the baseline on test (MAE strictly lower);
  - the resulting promotion call: *promote* (residual model becomes the shipped forecaster) or
    *do not promote* (moving-average stays; this is fine and expected if no real signal exists).
- Update the existing **Interview Note** to reflect the residual experiment outcome honestly.

### I-03 — Wire the promotion (ONLY if residual wins on test)

- If and only if `lightgbm_residual` beats `moving_average_7d` on test MAE: make it the model whose
  predictions populate the leakage-safe `baseline_predictions_7d.csv` consumed by the recommendation
  backtest, and update the model label surfaced on the Forecast/Recommendation pages.
- If it does not win: **change nothing downstream.** Leave `baseline_predictions_7d.csv`, the forecast
  artifact, and the dashboard label on `moving_average_7d`. Record the negative result and stop.
- Do not silently swap forecasters. Whatever the outcome, the report's Decision section must match what
  actually shipped.

### I-04 — Tests

- `tests/test_lightgbm_model.py` (new or existing): a unit test for `predict_lightgbm_residual` proving
  **reconstruction correctness** — on a tiny synthetic frame, `prediction == rolling_mean_7 + residual`
  to floating tolerance, and a degenerate case where the model's residual is ~0 returns ~baseline.
- A **leakage guard** test: the residual target uses only `target - rolling_mean_7`, and `rolling_mean_7`
  for row at date `d` must not depend on any price after `d` (assert on a hand-built per-mandi series).
- Keep all existing tests green (currently 98).

### I-05 — Docs

- `reports/modeling/lightgbm_metrics_7d.md`: regenerated by the script (residual row + Decision section).
- `README.md`: update the modeling-status bullets to state the residual-reformulation outcome honestly
  (won or didn't, with the test-MAE numbers). Keep claims scoped.
- `docs/TRACKER.md`: mark I-01 Done with the result; if promoted, note the shipped forecaster changed.
- `docs/ARCHITECTURE.md`: only if the shipped forecaster changed (Modeling Boundary / Data Flow mention).

### I-06 — Finish

- `python scripts/train_lightgbm_7d.py` (regenerate metrics + report).
- If promoted: re-run the downstream chain it feeds (`build_forecast_intervals_7d.py` →
  `build_recommendations_7d.py` → `run_recommendation_backtest_7d.py`) so artifacts stay consistent.
- `python -m pytest tests/ -q` (all green).
- `python -m ruff check app/ tests/ src/ scripts/` and `python -m black app/ tests/ src/ scripts/ --line-length 100`.
- Commit (imperative subject, no generated-code attribution trailer) and push.

---

## Acceptance criteria

- A `lightgbm_residual` model is trained, evaluated on the same temporal split, and reported **alongside**
  the existing level-LightGBM and all baselines with MAE/RMSE/sMAPE/MASE, overall and per-mandi.
- The report carries a clear Decision section grounded in the numbers, and the shipped forecaster is
  promoted **iff** the residual model beats `moving_average_7d` on test MAE — otherwise nothing downstream
  changes and the negative result is reported honestly.
- Reconstruction + leakage tests cover the new path; full suite green; ruff/black clean.
- Docs reflect the actual outcome.

## Out of scope (later milestones)

- **J — DuckDB + coverage:** adopt DuckDB as the local store per RULES §Architecture (or document the
  justification) and add `pytest --cov` gating.
- Any new exogenous features (weather, arrivals), extra horizons, or extra crops/states — all post-MVP.
  This milestone changes the **target formulation only**, reusing the existing feature set, so the
  comparison isolates one variable.
