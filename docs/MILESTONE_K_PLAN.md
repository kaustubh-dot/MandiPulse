# Milestone K Plan — Release Hardening + Freeze

## Decision

The MVP loop is **RULES-complete** (TRACKER §"MVP loop is now RULES-complete"). Milestone K adds
**no product features.** It closes the two remaining in-scope quality gaps, raises the coverage
floor to match, and **freezes the MVP** behind a tagged release. Everything in TRACKER §Deferred
(X-01…X-13) stays out of scope; pulling any of it in requires a separate RULES.md + TRACKER
promotion the user authorizes.

Scope guard: **no modeling, forecaster, recommendation, or number changes.** Tests, one MLflow
test surface, docs, and release metadata only.

## Tasks

| ID | Task | Depends On |
|---|---|---|
| K-01 | End-to-end pipeline smoke test on golden fixtures | - |
| K-02 | Cover `modeling/tracking.py` (MLflow glue) | - |
| K-03 | Raise `--cov-fail-under` to match post-K coverage | K-01, K-02 |
| K-04 | Release: `RELEASE.md` runbook, TRACKER freeze note, README freeze badge | K-01..K-03 |
| K-05 | ruff/black, commit, push, STOP for Opus review | all |

### K-01 — Pipeline smoke test

**Goal:** one test that proves the 8-stage pipeline wires together start-to-finish — the
integration break that per-stage unit tests miss.

**Approach (in-process, not subprocess):** new `tests/test_pipeline_smoke.py`. Drive each stage's
**core build function** (not the CLI `argparse main`) in sequence, threading each stage's output
frame into the next, seeded from the existing `golden_clean_panel` / `golden_feature_table`
fixtures in `conftest.py`. Assert at each hop:
- the frame is non-empty and has the columns the next stage consumes,
- terminal artifacts (forecast frame, recommendation frame) carry their RULES-required columns
  (forecast: lower/upper bounds; recommendation: transport cost, alternatives, risk level + reason).

Use `tempfile.TemporaryDirectory()` for any path the stage writes (Windows `tmp_path`
PermissionError rule). Do **not** spawn subprocesses (slow + flaky on Windows). If a stage exposes
only a CLI entrypoint with no importable core function, that's a finding — note it; the minimum is
to cover the build/predict functions already imported by the unit tests, chained.

**Non-goal:** re-asserting numeric values already locked by unit tests. This test guards *wiring*,
not arithmetic.

### K-02 — Cover `modeling/tracking.py`

`tracking.py` is imported by all three training scripts and sits at 0% coverage. New
`tests/test_tracking.py`:
- `_tracking_uri()`: `sqlite:///…` passes through unchanged; a `://`-bearing URI passes through;
  a bare relative path resolves to an absolute `file://` URI. Stub `load_yaml_config` via
  monkeypatch so the test owns the config dict.
- mlflow-absent degradation: monkeypatch `tracking._MLFLOW_AVAILABLE = False`, then assert
  `set_experiment` warns, `start_run` yields `None`, and `log_params/log_metrics/log_artifact`
  are silent no-ops.

Do not require a live mlflow server or write `mlruns/`. No new dependency.

### K-03 — Coverage floor

Measure post-K coverage, then set `--cov-fail-under` to `floor(measured) - 1` in
`pyproject.toml` addopts (current floor 60 → expected ~65). State the new measured number in the
commit body. Floor only ratchets up, never down.

### K-04 — Release + freeze

- `RELEASE.md`: one-screen runbook — install (`pip install -e ".[dev]"`), pipeline order
  (copy the CLAUDE.md 8-stage order), `streamlit run`, and the v0.1-mvp scope statement
  (1 crop / 1 state / 15 mandis / 7-day). No Unicode `→ … ± × —` in any code path; prose is fine.
- TRACKER: add a "Frozen" status line — MVP shipped at v0.1-mvp, K Done, post-MVP requires
  scope promotion.
- README: one-line "Status: v0.1-mvp (frozen)" note near the top.
- Git tag `v0.1-mvp` is created by the user (or on request) after the push lands — the plan does
  not self-tag.

### K-05 — Land it

`ruff check src/ scripts/ tests/` + `black --check` (skip `.claude/skills/` — not project code),
full `pytest`, commit with imperative subject and **no Claude attribution**, push **only when
asked**, then STOP for Opus review.

## Acceptance

- `pytest` green; total tests ≥ 129 (127 + smoke + tracking).
- Coverage floor raised and passing.
- `tracking.py` no longer 0%.
- ruff/black clean on project source.
- RELEASE.md + TRACKER freeze note present.
- No change to any forecast/recommendation number, model artifact, or pipeline output.

## Hand-off

Implementer: Sonnet. Reviewer: Opus. Commit + push (when asked) + stop per the milestone loop.
