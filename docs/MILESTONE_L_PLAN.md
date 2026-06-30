# Milestone L Plan — Make It Visible (Clone-Runnable + Live Demo)

## Decision

The MVP is frozen and RULES-complete (Milestone K). Milestone L adds **no modeling or product
features.** Its single goal is **visibility**: a stranger who finds this repo can (a) run it from a
clean clone in under two minutes and (b) click a live URL and see a working forecast +
recommendation. This is the highest-leverage work for the project's purpose — a standout B.Tech
resume project for AI Engineer / Data Science roles.

**No RULES.md scope change is required.** This stays inside existing rules:

- RULES line 90: *"use a single Streamlit app"* — we deploy that same app, add no FastAPI.
- RULES line 153: *"Do not commit generated raw data files unless small, public, and intentionally
  sampled."* — the demo bundle is a small, intentionally sampled, public artifact set. Permitted.
- RULES line 29: *"Keep generated artifacts reproducible from code, config, and source data."* — the
  bundle is produced by a committed, re-runnable script, not hand-edited.

**Scope guard:** no forecaster, recommendation, metric, or number changes. The demo bundle must
carry the *exact same numbers* the full pipeline produces — it is a trimmed copy, never a
recomputation. If any displayed figure would change, the task is wrong.

## The core problem

A fresh clone has no `data/processed/` or `artifacts/` (both git-ignored, correctly). The app
`st.stop()`s on the first missing artifact ([data_access.py:36](../src/mandipulse/app/data_access.py#L36)).
So today the dashboard cannot start for anyone but the original author. Streamlit Community Cloud
clones the repo and runs `app/streamlit_app.py` — it would immediately hit the stop screen.

The full artifacts are too heavy to commit: `feature_table_7d.csv` is **16.5 MB**, `clean_mandi_prices.csv`
is **5.4 MB**. We need a *slim* committed bundle that preserves every number the three pages display.

## What each page actually reads (audit result)

| Page | Loader | Full artifact | What the page uses |
|---|---|---|---|
| Home | `load_forecasts` | forecast_outputs_7d.csv (4 KB) | as_of dates, staleness |
| Data Coverage | `load_clean_panel` | clean_mandi_prices.csv (5.4 MB) | full panel: KPIs, per-mandi coverage, charts |
| Data Coverage | `load_feature_table` | feature_table_7d.csv (16.5 MB) | **only** `feature_row_valid` count + filter (2 cols) |
| Data Coverage | `load_mandi_metadata` | mvp_mandis.csv (committed) | already in repo |
| Forecast | `load_clean_panel` | clean_mandi_prices.csv | per-mandi price history |
| Forecast | `load_forecasts` | forecast_outputs_7d.csv | forecast + bounds |
| Forecast | `load_report_markdown` | reports/modeling/*.md (committed) | already in repo |
| Recommendation | `load_recommendations` | recommendation_outputs_7d.csv (7 KB) | ranked recs |
| Recommendation | `load_recommendation_backtest` | recommendation_backtest_7d.csv | regret@K (optional, degrades) |
| Recommendation | `load_report_markdown` | reports/modeling/*.md (committed) | already in repo |

**Key finding:** the 16.5 MB feature table is read for a *single column*. A 2-column slim copy
(`market_id`, `feature_row_valid`) preserves the exact trainable count the page shows.

The 5.4 MB clean panel drives charts and per-mandi history, so it needs all rows — but only a
subset of columns. It compresses well; committing it gzipped (or as-is, it is under GitHub's soft
limits) is acceptable. Final size decision belongs to L-01 after measuring the trimmed columns.

## Tasks

| ID | Task | Depends On |
|---|---|---|
| L-01 | `scripts/build_demo_sample.py` — reproducible slim demo bundle into `data/sample/` | - |
| L-02 | App read-layer fallback: full artifact → demo sample → stop | L-01 |
| L-03 | Commit the demo bundle; align `.gitignore` to allow `data/sample/` | L-01 |
| L-04 | Deploy to Streamlit Community Cloud; add `requirements.txt`; capture live URL | L-02, L-03 |
| L-05 | README overhaul: hero screenshot/GIF, live-demo badge, honest results table, 2-min quickstart | L-04 |
| L-06 | Test the fallback path; raise/hold coverage floor; tracker + ruff/black; commit; push when asked; STOP | all |

---

### L-01 — Reproducible demo-sample builder

**Goal:** a committed script that regenerates the slim bundle from full artifacts, so the bundle
stays RULES-reproducible (line 29) and never drifts from the real numbers.

**New file:** `scripts/build_demo_sample.py`, following the `build_*` stage convention
(`from __future__ import annotations`, argparse, `sys.path.insert` for `src`, typed funcs).

**Output dir:** `data/sample/` (new, committed). Bundle contents:

1. `forecast_outputs_7d.csv` — copy verbatim (4 KB).
2. `recommendation_outputs_7d.csv` — copy verbatim (7 KB).
3. `recommendation_backtest_7d.csv` — copy verbatim (small).
4. `feature_table_7d.csv` — **slim:** select only the columns the app reads. Audit says Data
   Coverage uses only `feature_row_valid`; keep `market_id` + `feature_row_valid` (and any column
   `load_feature_table`'s `parse_dates=["date"]` requires — include `date` so the loader contract
   holds). Verify the trainable count is byte-identical to the full table before/after.
5. `clean_mandi_prices.csv` — keep all rows (charts need them) but only the columns the panel
   pages read; measure the result. If it lands under ~3 MB, commit as-is; if not, document and
   gzip. Do **not** drop rows — KPIs (`total_rows`, observed/imputed counts, date range) must match.

**Hard constraint:** the script reads the full pipeline outputs and writes trimmed copies. It must
not call any model or recompute any value. Add a `--verify` mode (or inline asserts) that loads
both full and sample and asserts the displayed aggregates match exactly:
- `feature_row_valid.sum()` equal
- panel row count, observed/imputed counts, min/max date equal
- forecast/recommendation frames equal on their key columns

**Source of full artifacts:** the script's inputs are the real pipeline outputs under
`data/processed/` and `artifacts/`. These exist on the author's machine. The script is run once
locally to produce the committed bundle; CI never needs the full data.

### L-02 — App read-layer fallback

**Goal:** when a full artifact is absent (fresh clone / Streamlit Cloud), transparently fall back to
the committed demo sample instead of stopping.

**Where:** `src/mandipulse/app/data_access.py` **only.** Do **not** touch `paths.py` — those helpers
are the pipeline's *write* path; a read-fallback there would make build scripts write into the
wrong place. The fallback is a read-layer concern that belongs next to the loaders.

**Approach:** add a small private resolver in `data_access.py`:

```
def _resolve_or_sample(full_path: Path, sample_name: str) -> Path:
    if full_path.exists():
        return full_path
    sample = PROJECT_ROOT / "data" / "sample" / sample_name
    if sample.exists():
        return sample
    return full_path  # caller's existing exists()-guard fires -> _missing_artifact_error
```

Each mandatory loader calls `_resolve_or_sample(...)` before its `exists()` check. The existing
stop/degrade contract is preserved exactly: if neither full nor sample exists, mandatory loaders
still stop and the optional backtest loader still returns `None`.

**Demo-mode signal:** when a sample is served, set a module flag so Home can show an honest
"Running on bundled demo data (Oct 2025)" caption. The current Home banner already says "Offline
Demo Mode" — extend it to distinguish *bundled-sample* from *full-local* so the deployed app never
implies it has live or complete data. (RULES line 133: no silent fallback to dummy data — this
fallback is to *real sampled* data and is labeled, which is compliant, but the label is mandatory.)

**Cache note:** loaders are `@st.cache_data`; the resolver runs inside them and returns a DataFrame,
so caching is unaffected. Do not cache `Path` objects or DuckDB connections.

### L-03 — Commit the bundle + gitignore alignment

- `.gitignore` currently ignores `data/processed/` and `artifacts/predictions/` but **not**
  `data/sample/`. Add an explicit allow comment near the MandiPulse data block so a future reader
  knows `data/sample/` is intentionally tracked.
- Commit `data/sample/*`. Confirm total added size is reasonable (target < 5 MB for the whole
  bundle). Record the byte sizes in the commit message.
- RULES line 22 (don't commit raw data if large/reproducible) is satisfied: this is *cleaned,
  sampled, small, and reproducible from `build_demo_sample.py`*, not raw CEDA data.

### L-04 — Deploy to Streamlit Community Cloud

- **Add `requirements.txt`** at repo root pinning the app's runtime deps (streamlit, pandas, numpy,
  pyarrow, duckdb, plotly). Streamlit Cloud installs from it. Keep it minimal — runtime only, not
  the `[dev]` tooling. Derive versions from the working `.venv` / `pyproject.toml` to avoid drift.
- Streamlit Cloud entrypoint: `app/streamlit_app.py` (confirmed correct; the RELEASE.md fix in
  6dbf280 already corrected the earlier `app/Home.py` error).
- Deployment itself is a web action on share.streamlit.io (connect repo, pick branch `main`, set
  entrypoint). **This step needs the user** — it requires their Streamlit/GitHub account. The agent
  prepares everything (requirements.txt, verified fallback) and hands the user a 3-line checklist;
  the user clicks deploy and pastes back the URL.
- Once live, the URL flows into L-05.

### L-05 — README overhaul (the 60-second sell)

Recruiters skim. Restructure the top of `README.md` to land the project in under a minute:

1. Title + one-line pitch + **🔗 Live Demo** badge (the L-04 URL) + build/coverage line.
2. **Hero visual:** a screenshot or GIF of the Forecast or Recommendation page. (Asset capture is a
   user step — agent leaves a marked placeholder and the exact markdown to drop the image in.)
3. Two-sentence problem statement.
4. **Honest results table** — lead with it: baseline-vs-LightGBM MAE/MASE and the one-line
   *"LightGBM did not beat the 7-day moving-average baseline on held-out data, so the baseline
   ships — reported transparently."* This is the project's strongest senior signal; surface it.
5. Small architecture diagram (text/mermaid is fine) — pipeline stages → artifacts → dashboard.
6. **2-minute quickstart:** clone → `pip install -e .` → `streamlit run app/streamlit_app.py` →
   *works immediately on bundled demo data, no pipeline run required.*
7. Link to `RELEASE.md` for the full pipeline runbook.

Keep RULES Dashboard tone (line 140): credible, data-heavy, not flashy.

### L-06 — Verify, gate, finalize

- **New test** `tests/test_demo_fallback.py`: simulate a missing full artifact (point the resolver
  at a temp dir with only `data/sample/`) and assert each mandatory loader returns the sample frame
  rather than stopping; assert the demo-mode flag flips. Use `tempfile.TemporaryDirectory()` — the
  pytest `tmp_path` fixture throws PermissionError on this Windows machine.
- **Test the verify-equality** of L-01 if feasible without the full artifacts in CI: gate that test
  behind `skipif` when full artifacts are absent (same pattern as the mvp_mandis skip in
  `test_pipeline_smoke.py`), so CI on a clean checkout stays green while local runs verify parity.
- Coverage: adding `data_access.py` fallback lines + a new test should *raise* coverage; re-measure
  and bump `--cov-fail-under` to `(measured - 1)` per the project convention. Never lower it.
- `ruff check src/ scripts/ tests/` and `black --check`.
- Update `docs/TRACKER.md`: Milestone L Done, note the live URL, keep MVP frozen.
- Full `pytest` green, then commit. **Push only when the user asks.**

## Unicode / Windows constraints (carried from prior milestones)

- No `→ … ± × —` or emoji in any `print()` path in `build_demo_sample.py` (cp1252 stdout). UTF-8
  file writes and README emoji are fine.
- Always `tempfile.TemporaryDirectory()`, never the `tmp_path` fixture.
- No generated-code attribution trailers in commits or PRs.

## Out of scope for L (still deferred, needs separate promotion)

FastAPI, live CEDA fetch, 14/30-day horizons, more crops/states, CI workflow (worth doing next as
Milestone M, but separable), LLM explanation layer (the AI-Engineer flourish — plan separately
after L lands so the demo is solid first), interval recalibration (in-scope quality fix, but a
different concern from visibility — sequence after L).

## Suggested sequence after L

1. **M — CI workflow** (GitHub Actions: pytest + ruff + black + coverage gate). Makes the freeze
   verifiable; cheap; high signal for engineering roles.
2. **N — LLM explanation layer**, grounded so it only narrates pipeline numbers (the standout
   AI-Engineer differentiator). Needs its own plan + a RULES note on the LLM boundary.
3. **Interval recalibration** — widen residual bands to hit the 90% nominal target.
