# MandiPulse Tracker

## Canonical Portfolio Documents

The active portfolio execution and review contract lives in these documents:

- [PRODUCT.md](../PRODUCT.md) — users, purpose, scope, product truth, and constraints.
- [DESIGN.md](DESIGN.md) — locked visual and interaction system for both interfaces.
- [APP_FLOW.md](APP_FLOW.md) — authoritative routes, user journeys, and state behavior.
- [COMPLETION_ROADMAP.md](COMPLETION_ROADMAP.md) — evidence-based remaining-work inventory.
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) — active F0-F8 execution sequence and stable task IDs.
- [RELEASE_GATES.md](portfolio/RELEASE_GATES.md) — objective portfolio release acceptance criteria.
- [CURRENT_STATE.md](portfolio/CURRENT_STATE.md) — current baseline, blockers, and next action.
- [CHECKPOINTS.md](portfolio/CHECKPOINTS.md) — historical phase handoffs and approved evidence.
- [RESCUE_PLAN.md](portfolio/RESCUE_PLAN.md) — completed historical rescue scope; no longer the active implementation plan.

## Scope

Active product scope remains Onion/Maharashtra, 15 mandis, and a 7-day horizon. The analytical core,
Streamlit dashboard, and static Next.js surface exist. The current finish track corrects the
public recommendation vocabulary, hardens frontend dependencies and tests, reconciles documentation,
and prepares verified public deployment. Visual/UI acceptance and redesign are intentionally deferred
for a later dedicated pass. Additional commodities, regions, horizons, and infrastructure remain
deferred.

## Current Status

| Area | Status | Notes |
|---|---|---|
| Python MVP pipeline | Done | Clean panel, feature table, baselines, LightGBM comparison, intervals, recommendations, backtest |
| Product/calculation contract | Done | Public ranking is transport-adjusted; uncertainty remains separate evidence |
| Streamlit dashboard | UI redo deferred | Non-UI smoke and parity checks pass; visual/UI acceptance is intentionally not part of this pass |
| Next.js static frontend | UI redo deferred | Non-visual logic, typecheck, lint, build, and parity pass; visual/UI acceptance is intentionally excluded |
| Frontend dependencies | Done with upstream ESLint note | Next.js 16/React 19 audit is clean; bundled lint plugins currently support ESLint 9, whose upstream support window has ended |
| Frontend experience tests | Non-visual checks done | 137 logic/parity assertions pass; visual/UI review is intentionally deferred |
| Public deployment | Pending | Final Next.js and redesigned Streamlit URLs are not yet verified |
| GitHub Actions CI | Green on `ba9535e` | Python and web jobs pass on the exact pushed release commit |

## Local Verification

Most recent recorded baseline:

```powershell
python scripts\validate_web_export.py
ruff check app src scripts tests
black --check app src scripts tests
pytest -q
```

Expected current results: 208 Python tests with 77.59% coverage (70% floor), a schema-valid
deterministic export, 140 web unit assertions, 44 component checks, a clean typecheck/lint/build, and zero
production npm audit findings. Visual/UI acceptance remains intentionally deferred.

CP-001 and CP-003 are Approved and Complete. CP-002 has approved local evidence, but its frontend
packaging and publication remain unfinished. Phase 3 technical evidence is generated in
`reports/modeling/phase3_evaluation.md` and `.json`. The next release checkpoint has not been
approved.

## Final Finish Track — F0 Through F8

| ID | Status | Task |
|---|---|---|
| F0 | Done (2026-08-22) | Preserve and classify the current frontend work; establish a reproducible baseline |
| F1 | Done (2026-08-22) | Align ranking vocabulary, schemas, exports, tests, reports, and UI copy with the implemented calculation |
| F2 | Done (2026-08-22) | Migrate the frontend to supported dependencies and clear the production security gate |
| F3 | UI redo deferred | Existing design-system implementation is retained as a reference; visual acceptance is not part of this pass |
| F4 | UI redo deferred | Existing Next.js surface is not accepted as final; redesign is intentionally deferred |
| F5 | UI redo deferred | Existing Streamlit surface is not accepted as final; redesign is intentionally deferred |
| F6 | Non-UI checks done | Logic, parity, typecheck, lint, build, and CI checks pass; visual/UI checks intentionally skipped |
| F7 | UI redo deferred | Responsive, accessibility, and visual acceptance will follow the dedicated UI redesign |
| F8 | Pending | Reconcile docs, deploy both interfaces, verify public URLs, and record the release |

Progress and exit criteria are defined in `docs/IMPLEMENTATION_PLAN.md` and
`docs/portfolio/RELEASE_GATES.md`. Historical milestone statuses below remain evidence of completed
engineering work; they do not imply that the new finish track is complete.

## Milestone N - Static Frontend And Portfolio Closeout

| ID | Status | Task |
|---|---|---|
| N-01 | Done | Scope promotion: RULES + PRD + TRACKER; promote X-12 |
| N-02 | Done | Strict schema-validated `scripts/build_web_export.py` export plus manifest to `web/public/data/*.json` |
| N-03 | Done | Next.js + Tailwind scaffold in `web/`; static export config |
| N-04 | Done | Typed frontend data loaders |
| N-05 | Done | TypeScript port of recommendation engine |
| N-06 | Done | Shared frontend components |
| N-07 | Done | Data Coverage page |
| N-08 | Done | Forecast page |
| N-09 | Done | Recommendation page with live location/quantity/transport/radius re-ranking |
| N-10 | Done | TS/Python ranking parity test |
| N-11 | Pending | Vercel deploy; update README with final URL |
| N-12 | Done | `.gitignore`, `.nvmrc`, local Python/web gates |

## Completed Milestones

| Milestone | Status | Result |
|---|---|---|
| M | Retired | Former backend experiment; excluded from the locked portfolio surface |
| L | Done | Clone-runnable demo sample bundle |
| K | Done | MVP release hardening and coverage gate |
| J | Done | DuckDB read-layer over CSV artifacts |
| I | Done | Residual LightGBM evaluated; not promoted |
| H | Done | Recommendation backtest surfaced in dashboard |
| G | Done | Regret@K vs nearest-mandi recommendation evaluation |
| F | Done | Tests and dashboard reliability hardening |
| D0-D5 | Done | Data ingestion, cleaning, features, baselines, intervals, recommendations |

## Current Data Artifacts

| Artifact | Status | Notes |
|---|---|---|
| Raw CEDA CSV | Local only, ignored | `data/raw/` |
| Clean panel CSV | Local only, ignored | `data/processed/onion_maharashtra/clean_mandi_prices.csv` |
| Feature table CSV | Local only, ignored | `data/processed/onion_maharashtra/feature_table_7d.csv` |
| Mandi list | Tracked | `data/external/mvp_mandis.csv` |
| Demo sample bundle | Tracked | `data/sample/*.csv`; clone-runnable demo data |
| Web JSON bundle | Tracked | `web/public/data/*.json`; generated by `scripts/build_web_export.py` |
| Full generated artifacts | Local only, ignored | `artifacts/forecasts/`, `artifacts/metrics/`, `artifacts/recommendations/` |
| Data-quality reports | Tracked | `reports/data_quality/*.md` |
| Modeling reports | Tracked | `reports/modeling/*.md` |
| MLflow runs | Local only, ignored | `mlruns/` |

## Deferred Work

| ID | Status | Task |
|---|---|---|
| O | Deferred | Offline calendar/exogenous features; arrivals gated on valid refresh |
| P | Done | Conformal intervals compared against residual intervals; Phase 3 adopted split-conformal for the observed-target evaluation population |
| X-03 | Deferred | Regime/anomaly detection |
| X-04 | Deferred | Live monitoring/drift platform |
| X-05 | Deferred | 14-day and 30-day forecasts |
| X-06 | Deferred | Tomato or additional crops |
| X-07 | Deferred | Karnataka/Uttar Pradesh or additional states |
| X-08 | Deferred | Arbitrage module |
| X-09 | Deferred | Similar historical days module |
| X-10 | Deferred | Price propagation graph |
| X-11 | Deferred | Causal weather shock module |
| X-13 | Deferred | Kubernetes/microservices |

## Guardrails

- Do not require a live API key for public demos.
- Do not use random train/test splits.
- Do not commit `.env`, `.venv`, raw data, processed data, MLflow runs, or full generated artifacts.
- Keep the project framed as mandi decision intelligence, not generic crop-price prediction.
