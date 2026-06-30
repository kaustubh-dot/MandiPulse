# Milestones O & P — Exogenous Signals + Conformal Intervals

**Workflow:** Implement, commit, push, and stop per milestone.
**Status:** Planned. **Order:** O before P (O changes the feature table; P calibrates whatever ships).
**Type:** Modeling. Touches features, baselines, LightGBM, intervals, reports, tests.
MVP scope unchanged: onion / Maharashtra / 7-day / 15 mandis.

---

## RULES guardrails both milestones must honor

- **Temporal split only** (`splits.py` already purges horizon gaps). Never random.
- **No future data in features.** Every new feature must be known on the as-of date. Calendar
  features (festival/MSP/season) are date-derived and safe. Lag/rolling on any new series must use
  `min_periods=window` backward windows like the existing ones.
- **Always compare against baselines.** Report MAE, RMSE, sMAPE, MASE. Save split dates.
- **Promote only on TEST MAE.** Validation winning is the existing overfit trap (val 129 vs test 188).
  A model is promoted to shipped forecaster **only if it beats moving-average on the TEST split**.
  A negative result is an acceptable, documented outcome — that is the project's honesty story.
- **Conformal is RULES-blessed** (§Uncertainty line 51). Report empirical coverage + interval width;
  never present bounds as guarantees.
- No new heavy deps. Conformal is implemented in-repo (it's quantile arithmetic), not a new library.

---

## Verified ground truth (do not re-guess)

| Fact | Value | Source |
|---|---|---|
| Raw CEDA columns | `date, commodity_*, state_*, district_*, market_*, min_price, max_price, modal_price` | `onion_maharashtra_prices_raw.csv:1` |
| **Arrivals/volume in cache?** | **NO** — only price. CEDA `prices()` uses `indicator="price"` | `ceda_client.py:39` |
| CEDA key status | Expired / refresh-gated per memory; do not assume it works | project memory |
| Shipped forecaster | `moving_average_7d` (test MAE 139.57) | `reports/modeling/` |
| LightGBM test MAE | 188.2 level / 195.63 residual — both lose | `lightgbm_metrics_7d.md` |
| Current intervals | residual quantiles on validation; 86.71% empirical vs 90% nominal | `intervals.py:67` |
| Feature list | `NUMERIC_FEATURES` + `CATEGORICAL_FEATURES` | `columns.py:9-38` |
| Target | `target_price_t_plus_7` = price.shift(-7) | `build_feature_table.py:53` |
| Split purge | val/test separated by `horizon_days` gap | `splits.py:84-88` |
| Interval residual source | validation split predictions only | `intervals.py:73-81` |

---

# Milestone O — Exogenous Calendar Signals (offline) + arrivals (gated)

## O.0 The honest split (read first)

"Exogenous signals" has two tracks. Only Track A is buildable offline today.

| Track | Signal | Buildable now? | Why |
|---|---|---|---|
| **A (this milestone)** | Festival/holiday calendar, MSP-window flags, harvest-season flags, days-to/from festival | **YES** — pure date math, static public dates | No API. Leakage-free (future calendar dates are known). |
| **B (gated, document only)** | Mandi arrivals / volume | **NO** | Not in cache; needs CEDA refresh with `indicator="quantity"` + a valid key. |
| **C (deferred, P1)** | Weather (rainfall, temp) | No | External source alignment; RULES says P1, not a blocker. |

**Build Track A. Track B is added as a documented, ready-to-run path that activates when a
key is available — do NOT fabricate arrivals data.** This keeps the "honest, reproducible" identity.

## O.1 Scope promotion (docs first)

- `docs/RULES.md` / `docs/PRD.md`: note that calendar exogenous features are promoted into the MVP
  feature set (still onion/MH/7d). Weather + arrivals remain P1/gated.
- `docs/TRACKER.md`: add `### In Progress (Milestone O — exogenous calendar features)` with O-01…O-08.
- `TODO.md`: check off "weather/SHAP P1" context — calendar is the in-scope exogenous lever now.

## O.2 New module: `src/mandipulse/features/calendar.py`

Pure functions, fully testable, no I/O. All inputs are `pd.Series` of dates.

```python
from __future__ import annotations
import pandas as pd

# Static, citable, offline. Onion is a rabi/kharif crop; Maharashtra harvest peaks
# drive supply gluts. Festival demand (Diwali, etc.) drives price spikes.
# Dates are public; store as a small committed CSV, not hardcoded magic.

def add_calendar_features(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    """Attach leakage-free, date-derived exogenous features.

    All features are deterministic functions of the calendar date and therefore
    known on the as-of date — no future information.
    """
    d = pd.to_datetime(df[date_col])
    out = df.copy()
    # Harvest-season flag (Maharashtra onion: rabi harvest ~Mar-May, kharif ~Oct-Dec)
    out["is_rabi_harvest"] = d.dt.month.isin([3, 4, 5]).astype(int)
    out["is_kharif_harvest"] = d.dt.month.isin([10, 11, 12]).astype(int)
    # Quarter / week-of-year cyclical (supplements existing month/dow cyclical)
    out["week_of_year"] = d.dt.isocalendar().week.astype(int)
    out["quarter"] = d.dt.quarter
    return out
```

Festival/MSP dates live in a committed lookup, regenerated deterministically:

**`data/external/calendar_events_maharashtra.csv`** (committed, small, public):
```
event_date,event_type,event_name
2020-11-14,festival,Diwali
2021-11-04,festival,Diwali
...
2020-06-01,msp_window,kharif_msp_announcement
...
```
`event_type ∈ {festival, msp_window, harvest_peak}`. Populate Diwali/Dussehra/Holi/Gudi
Padwa dates 2020–2026 (public, citable) and MSP announcement windows. Derive:
- `days_to_next_festival` (>=0, clipped at e.g. 60)
- `days_since_last_festival`
- `is_festival_week` (within ±3 days)
- `is_msp_window`

`add_event_features(df, events_df)` joins by date with a backward/forward asof-merge. **Leakage
check:** `days_to_next_festival` looks forward in the *calendar* — that is allowed because festival
dates are public and fixed in advance (a farmer knows Diwali's date months out). Document this
explicitly in the function docstring and the report; it is the one place a reviewer will scrutinize.

## O.3 Wire into the feature table

- `build_feature_table.py`: after the existing cyclical block, call `add_calendar_features` then
  `add_event_features` (load the events CSV). Keep them out of `required_feature_columns` for
  `feature_row_valid` (they're never NaN, so they won't reduce trainable rows).
- `columns.py`: append the new numeric features to `NUMERIC_FEATURES` so LightGBM/Ridge pick them up.
  Group them with a comment block `# --- exogenous calendar features (Milestone O) ---`.
  **Do NOT add them to the baselines' prediction columns** — baselines stay as-is (seasonal naive /
  moving average use a single column). Only the learned models (Ridge, LightGBM) consume them.

## O.4 Retrain + honest comparison

- Re-run `train_baselines_7d.py`, `train_lightgbm_7d.py`. The baselines are unchanged by design;
  only Ridge/LightGBM see new features.
- **New report section** in `lightgbm_metrics_7d.md`: "With exogenous calendar features" — test MAE
  for level-LightGBM and residual-LightGBM vs the 139.57 baseline. Keep the pre-O numbers in a
  "Before exogenous features" column so the delta is visible.
- **Promotion gate:** if test MAE now beats 139.57, promote LightGBM to shipped forecaster (update
  `intervals.py` `prediction_column_map` + `build_forecast_intervals_7d.py` `--model-name` default +
  README + ARCHITECTURE). If it still loses, **document the negative result** and keep moving-average.
  Either outcome is a milestone success.

## O.5 Track B — arrivals, documented-but-gated (no data fabrication)

- Add `docs/EXOGENOUS_ARRIVALS.md`: exact steps to fetch arrivals when a key exists — CEDA
  `indicator="quantity"`, the join key (`market_id`+`date`), the leakage-safe lag plan (arrivals on
  the as-of date are known; build `arrivals_lag_*` / `arrivals_rolling_*` exactly like price).
- Add a `--with-arrivals` flag to `build_feature_table.py` that is a **no-op with a clear log line**
  when the arrivals file is absent: `"arrivals file not found — skipping (see docs/EXOGENOUS_ARRIVALS.md)"`.
  This makes the path real and runnable without shipping fake numbers.

## O.6 Tests (`tests/test_calendar_features.py`)

- `add_calendar_features` produces correct flags for known dates (a March date → rabi=1).
- `days_to_next_festival` is non-negative and 0 on a festival date.
- **Leakage guard:** event features depend only on `date`, never on `modal_price` or target — assert
  that shuffling the price column leaves calendar features unchanged.
- `feature_row_valid` count does not drop after adding calendar features (they're never NaN).
- Golden-fixture parity for one mandi slice.

## O.7 MLflow + O.8 Docs

- Log new feature count + per-model test MAE under experiment `mandipulse_exogenous_7d`.
- Update README honest-results table (add exogenous column), ARCHITECTURE (feature stage), TRACKER.

---

# Milestone P — Conformal Prediction Intervals

## P.0 Goal

Replace/augment the residual-quantile intervals (86.71% empirical vs 90% nominal — *under*-covering)
with **split conformal**, which gives a finite-sample coverage guarantee under exchangeability and
typically lands closer to nominal. Keep residual intervals available behind a flag for comparison.
This runs over **whatever forecaster ships after O** (moving-average or promoted LightGBM).

## P.1 Method (split conformal, absolute residuals)

Already have the right structure: a calibration split (validation) disjoint from test, with the
horizon purge gap in `splits.py`. Split conformal:

1. On the **validation** (calibration) split, compute nonconformity scores
   `s_i = |y_i − ŷ_i|` (absolute residual).
2. Take the quantile `q = ceil((n+1)(1−α)) / n` empirical quantile of `{s_i}` (the finite-sample
   conformal correction — note the `(n+1)/n` factor, not a plain quantile).
3. Interval = `[ŷ − q, ŷ + q]` (symmetric).
4. Report empirical coverage + width on the **test** split.

Asymmetric variant (optional, better for skewed onion spikes): conformalize lower/upper residuals
separately with `α/2` each. Implement symmetric first; add asymmetric only if symmetric over/under-shoots.

## P.2 New code: extend `src/mandipulse/modeling/intervals.py`

Add alongside the existing residual functions (do not delete them):

```python
def compute_conformal_quantile(
    predictions: pd.DataFrame,
    model_name: str,
    confidence_level: float,
) -> float:
    """Split-conformal nonconformity quantile from the validation (calibration) split.

    Uses the finite-sample correction q-level = ceil((n+1)(1-alpha)) / n.
    """
    alpha = 1.0 - confidence_level
    cal = predictions[
        (predictions["split"] == "validation") & (predictions["model"] == model_name)
    ]
    if cal.empty:
        raise ValueError(f"No calibration predictions for model '{model_name}'.")
    scores = (cal[TARGET_COLUMN] - cal["prediction"]).abs()
    n = len(scores)
    level = min(1.0, (np.ceil((n + 1) * confidence_level)) / n)
    return float(scores.quantile(level))


def build_conformal_backtest(predictions, model_name, q, confidence_level) -> pd.DataFrame:
    sel = predictions[predictions["model"] == model_name].copy()
    sel["lower_bound_inr_qtl"] = sel["prediction"] - q
    sel["upper_bound_inr_qtl"] = sel["prediction"] + q
    sel["covered"] = (sel[TARGET_COLUMN] >= sel["lower_bound_inr_qtl"]) & (
        sel[TARGET_COLUMN] <= sel["upper_bound_inr_qtl"]
    )
    sel["interval_width_inr_qtl"] = sel["upper_bound_inr_qtl"] - sel["lower_bound_inr_qtl"]
    sel["confidence_level"] = confidence_level
    return sel.reset_index(drop=True)
```

`build_latest_forecast_output` gains an interval-method branch: `method ∈ {"residual","conformal"}`.
For conformal, `lower = forecast − q`, `upper = forecast + q`. Bump `model_version` suffix to
`_conformal_v1` when conformal is used so artifacts are self-describing.

## P.3 Wire into `build_forecast_intervals_7d.py`

- Add `--interval-method {residual,conformal}` (default `conformal` after this milestone).
- Compute **both** methods, write a comparison table to the report (residual vs conformal:
  empirical coverage, avg width, median width on validation + test). This is the honesty artifact.
- The shipped `forecast_outputs_7d.csv` uses the chosen method; keep the residual numbers in the
  report so the improvement (or trade-off) is visible.

## P.4 Re-export downstream

Conformal changes `lower_bound_inr_qtl` / `upper_bound_inr_qtl` in `forecast_outputs_7d.csv`. That
flows into:
- Recommendations (interval width → uncertainty penalty → risk level). Re-run
  `build_recommendations_7d.py` + `run_recommendation_backtest_7d.py`.
- **Frontend (Milestone N):** re-run `build_web_export.py` and **re-run `web` parity test** — wider/narrower
  intervals change `uncertainty_penalty` and possibly `risk_level`. The N-10 parity test must still pass.
- `data/sample/` bundle: regenerate via `build_demo_sample.py` so the committed demo matches.

## P.5 Tests (`tests/test_conformal_intervals.py`)

- `compute_conformal_quantile` returns the correct finite-sample quantile on a synthetic set with
  known residuals (hand-computed expected `q`).
- Coverage monotonicity: higher confidence_level → larger `q` → ≥ coverage.
- **Calibration/test disjointness:** assert the quantile is computed from validation rows only.
- Conformal empirical coverage on a synthetic exchangeable set is ≥ nominal − small tolerance.
- Reconstruction: `upper − lower == 2q` (symmetric).

## P.6 Docs

- `reports/modeling/forecast_intervals_7d.md`: residual-vs-conformal comparison table is the headline.
- README "Honest results": update coverage line — e.g. "conformal intervals: XX.X% empirical
  (nominal 90%), vs 86.71% under residual intervals."
- `docs/RULES.md` §Uncertainty already permits this; cite that the alternative (residual) is retained
  behind a flag and documented per the RULES requirement to document the tradeoff.
- TRACKER: P-01…P-06 Done rows.

---

## Combined task list

| ID | Milestone | Task |
|---|---|---|
| O-01 | O | Scope promotion (RULES/PRD/TRACKER/TODO) |
| O-02 | O | `features/calendar.py` + `calendar_events_maharashtra.csv` |
| O-03 | O | Wire calendar + event features into `build_feature_table.py`; extend `columns.py` |
| O-04 | O | Retrain Ridge/LightGBM; honest before/after test-MAE comparison + promotion gate |
| O-05 | O | Track B: `docs/EXOGENOUS_ARRIVALS.md` + `--with-arrivals` no-op flag |
| O-06 | O | `tests/test_calendar_features.py` (incl. leakage guard) |
| O-07 | O | MLflow logging under `mandipulse_exogenous_7d` |
| O-08 | O | Docs: README/ARCHITECTURE/TRACKER |
| P-01 | P | `compute_conformal_quantile` + `build_conformal_backtest` in `intervals.py` |
| P-02 | P | Interval-method branch in `build_latest_forecast_output` |
| P-03 | P | `--interval-method` flag + residual-vs-conformal comparison report |
| P-04 | P | Re-run recommendations/backtest/web-export; **re-run N-10 parity test**; regen `data/sample/` |
| P-05 | P | `tests/test_conformal_intervals.py` |
| P-06 | P | Docs: report, README coverage line, TRACKER |

## Execution order

O first (it may change the shipped forecaster, which P then calibrates). Within O: docs → calendar
module → wire+retrain → gate decision → tests → docs. Within P: intervals code → script flag →
compare → re-export+parity → tests → docs. Commit + push + stop after each milestone.

## Acceptance criteria

**O:**
- [ ] Calendar features are leakage-free (test proves they ignore price/target).
- [ ] `feature_row_valid` count unchanged after adding them.
- [ ] Before/after test-MAE table in the LightGBM report; promotion decision explicit (and honest if negative).
- [ ] Arrivals path documented + `--with-arrivals` no-ops cleanly without a data file.
- [ ] ruff/black clean; all tests green; coverage floor held.

**P:**
- [ ] Conformal quantile uses validation-only calibration + `(n+1)/n` correction (test proves it).
- [ ] Report shows residual-vs-conformal coverage/width side by side.
- [ ] Conformal empirical test coverage reported honestly (closer to 90% is the goal, not guaranteed).
- [ ] Downstream re-run: recommendations + `build_web_export.py` + **N-10 parity test passes**.
- [ ] `data/sample/` regenerated so the committed demo matches the new intervals.
- [ ] ruff/black clean; all tests green; coverage floor held.
