# Milestone H Plan — Surface the recommendation backtest in the dashboard

**Goal:** Make the Milestone-G regret@K backtest *visible and credible* inside the Streamlit
Recommendation page, and refresh the docs. The evaluation exists and is sound (regret@1 296.3 vs
nearest-mandi 370.1 INR/qtl; top-1 beats nearest 78.8%) but no user can see it today.

This milestone is **dashboard + docs only**. Do **not** touch the modeling (M3-04) or the data store
(DuckDB) — those are later milestones I and J. Keep MVP scope: Onion/Maharashtra, 7-day horizon.

---

## Why this, why now

Milestone G built `recommend/evaluation.py` and `run_recommendation_backtest_7d.py`, which prove the
ranking beats the naive nearest-mandi baseline. RULES §Recommendation requires evaluating quality with
"regret@K ... or nearest mandi baseline comparison" — done — and RULES §Dashboard says the UI must feel
"credible, data-heavy but readable." Right now the backtest result lives only in a markdown report
nobody opens. Surfacing it closes the loop: the Recommendation page can say *"historically, this
ranking has done X."*

---

## Critical constraints (read before coding)

1. **The backtest artifact is git-ignored.** `artifacts/recommendations/recommendation_backtest_7d.csv`
   is generated, not committed. The dashboard MUST degrade gracefully when it is absent — show a small
   `st.info(...)` telling the user to run `python scripts/run_recommendation_backtest_7d.py`, and then
   continue rendering the live recommendation. Do **NOT** call `st.stop()` for a missing backtest — the
   live ranking works fine without it. (Contrast with `_missing_artifact_error`, which stops the page
   because forecasts are mandatory. The backtest is optional context.)

2. **Single source of truth for the metrics.** Do NOT re-implement the regret/win-rate math in the page.
   The script's `write_report` currently inlines it, and a mislabeled-metric bug already happened there
   once. Extract the summarization into a tested pure function in `evaluation.py` and call it from BOTH
   the script and the dashboard.

3. **Keep it honest.** Label the section as a historical backtest over the test split with its date
   range. Preserve the existing "decision support, not a guaranteed-profit recommendation" framing. Do
   not imply future performance.

---

## Tasks

### H-01 — Extract `summarize_backtest()` into `evaluation.py` (refactor, single source of truth)

Add a pure function to `src/mandipulse/recommend/evaluation.py`:

```python
def summarize_backtest(backtest: pd.DataFrame, k_values: list[int]) -> dict:
    """Return headline backtest metrics as a flat dict (no I/O, no formatting).

    Keys per k in k_values: regret_at_{k}_mean, regret_at_{k}_median,
    optimal_rate_{k} (fraction top-K captured the best mandi, i.e. regret<=0),
    beats_nearest_{k} (fraction where regret_at_k < nearest_mandi_regret).
    Plus: nearest_mandi_regret_mean, nearest_mandi_regret_median,
    n_dates, date_min, date_max, n_dropped.
    Returns {} for an empty frame.
    """
```

- Move the math that currently lives in `scripts/run_recommendation_backtest_7d.py::write_report`
  (mean/median regret, optimal rate `regret<=0`, beats-nearest `regret < nearest_mandi_regret`,
  nearest-mandi mean/median, n_dates, date range, total dropped) into this function.
- **Rewrite `write_report` to call `summarize_backtest` and format its dict** into the existing markdown
  table. The report output must stay equivalent to today's (same rows/labels). Verify by regenerating
  and diffing.
- Rates are fractions (0–1) in the dict; format as `%` at the presentation layer (report + page).

### H-02 — Add loaders to `data_access.py`

- Add path import `recommendation_backtest_path` and a loader:

```python
@st.cache_data(show_spinner=False)
def load_recommendation_backtest() -> pd.DataFrame | None:
    """Load the backtest artifact, or return None if it has not been generated yet.

    Unlike the mandatory artifacts, the backtest is optional context — a missing
    file must NOT stop the page. Return None and let the caller show guidance.
    """
    path = recommendation_backtest_path()
    if not path.exists():
        return None
    return pd.read_csv(path)
```

- Do not wire it into `_missing_artifact_error`. Returning `None` is the contract.

### H-03 — Add a "Historical performance" section to `app/pages/3_Recommendation.py`

Place it after the ranked table (or directly under the Top-3 callout — your judgment on readability),
before the map. Behavior:

- Call `load_recommendation_backtest()`. If `None`, render:
  `st.info("Backtest not generated yet. Run `python scripts/run_recommendation_backtest_7d.py` to see how this ranking has performed historically.")`
  and skip the rest of the section.
- If present, call `summarize_backtest(backtest, k_values=[1, 3])` and show a compact row of
  `st.metric` tiles, e.g.:
  - "Mean regret@1" → `{regret_at_1_mean:.0f} ₹/qtl`
  - "Beats nearest-mandi" → `{beats_nearest_1:.0%}`
  - "Optimal pick rate@1" → `{optimal_rate_1:.0%}`
  - "Nearest-mandi regret" → `{nearest_mandi_regret_mean:.0f} ₹/qtl` (the baseline being beaten)
- Caption underneath: `Backtest over {n_dates} as-of dates ({date_min} to {date_max}), moving-average
  forecaster, test split. Lower regret is better.`
- Add an `st.expander("Full backtest report")` that renders
  `load_report_markdown("recommendation_backtest_7d.md")` (helper already exists).
- Use ASCII/arrow-free strings in any code path that could print to a terminal; the page itself is fine
  with unicode, but keep `→` out of f-strings that might also be logged. (Reports are written UTF-8.)

### H-04 — Tests

- `tests/test_recommend_evaluation.py`: add `TestSummarizeBacktest` —
  - empty frame returns `{}`;
  - a hand-built 2–3 row frame yields correct mean/median regret, `optimal_rate` (regret<=0 fraction),
    and `beats_nearest` (regret < nearest fraction);
  - keys exist for each k in `k_values`.
- `tests/test_app_data_access.py`: add a test that `load_recommendation_backtest()` returns `None` when
  the artifact is missing (patch `recommendation_backtest_path` to a tmp path; use the
  `__wrapped__`-unwrap pattern already in that file; use `tempfile.TemporaryDirectory`, NOT the
  `tmp_path` fixture — it hits a Windows PermissionError on this machine, see existing
  `TestMissingArtifactGuard`).
- All ~87 existing tests must stay green.

### H-05 — Docs

- `README.md`: add/refresh a line under the recommendation feature noting the backtest exists and its
  headline result; mention the new pipeline stage. Keep claims honest and scoped.
- `docs/TRACKER.md`: mark H tasks Done; the backtest artifacts row is already present.
- `docs/ARCHITECTURE.md`: if it documents the dashboard data flow, add that the Recommendation page now
  also reads the backtest artifact (optional). Skip if not applicable.

### H-06 — Finish

- `python scripts/run_recommendation_backtest_7d.py` (regenerate; confirm report unchanged in shape).
- `python -m pytest tests/ -q` (all green).
- `python -m ruff check app/ tests/ src/ scripts/` and `python -m black app/ tests/ src/ scripts/ --line-length 100`.
- **Manually run the app is NOT required**, but if quick: `streamlit run app/streamlit_app.py` and click
  to the Recommendation page to confirm the section renders and degrades gracefully.
- Commit (imperative subject, no generated-code attribution trailer) and push.

---

## Acceptance criteria

- Recommendation page shows historical backtest metrics when the artifact exists, and a clear "run the
  backtest" info box when it does not — never crashes either way.
- Metric math lives in one tested function (`summarize_backtest`), used by both script and page; the
  markdown report is unchanged in shape.
- New tests cover the summarizer and the None-returning loader; full suite green; ruff/black clean.
- Docs reflect the new capability.

## Out of scope (later milestones)

- **I — M3-04:** beat the moving-average baseline honestly (target/feature reformulation).
- **J — DuckDB + coverage:** adopt DuckDB as the local store per RULES §Architecture (or document the
  justification) and add `pytest --cov` gating.
