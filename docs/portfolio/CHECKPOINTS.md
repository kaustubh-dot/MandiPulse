# MandiPulse Checkpoints

This ledger records implementation, verification, review findings, corrective work, and release
decisions for the portfolio phases. It preserves the evidence needed to reproduce claims without
tying those claims to a particular development tool or reviewer identity.

## Governance

- Material changes to scope, task IDs, metric definitions, public interfaces, or acceptance
  criteria require repository-owner approval.
- Implementation completion and review approval are separate states.
- Builds alone do not prove completion; data, metric, runtime, and interface evidence are required.
- Localized review fixes must be recorded with their verification result.
- Update [CURRENT_STATE.md](CURRENT_STATE.md) only after the corresponding phase is approved.

Status flow:

`Not Started` -> `In Progress` -> `Ready for Review` -> `Changes Requested` -> `Approved` -> `Complete`

## CP-000 — Baseline audit

| Field | Value |
|---|---|
| Status | Complete |
| Review date | July 13, 2026 |
| Purpose | Establish the audited starting point and frozen portfolio scope |

The audit confirmed the Onion/Maharashtra/15-mandi/7-day boundary, the shipped moving-average
baseline, the offline snapshot model, and the need for strict exports, aligned metrics, runtime
evidence, and a recommendation-first product surface.

## CP-001 — Finished and Trustworthy MVP

| Field | Value |
|---|---|
| Status | Approved; Complete |
| Closure date | August 1, 2026 |
| Task range | P1-01 through P1-08 |

### Implemented contract

- Eight strict JSON exports with JSON Schema validation and finite-number checks.
- A shared canonical forecast as-of policy across Python calculations, Streamlit, exporter, and
  frontend logic.
- Export and frontend validation for crop, state, horizon, mandi, coordinates, quantity, radius,
  and alternative limits.
- A versioned manifest containing snapshot, source, configuration, model, code, input, artifact,
  and validation identities.
- Corrected public wording for 86.71% empirical coverage: it is below the nominal 90% level and is
  not described as conservative or guaranteed.

### Corrective review history

The first review found invalid/non-standard JSON, hardcoded metric drift, inconsistent as-of
selection, incomplete input limits, and blank/erroring coverage and forecast routes. The correction
pass added strict serialization, schemas, policy helpers, configured bounds, input and artifact
hashes, typed UI loading/error states, and cross-surface metric reconciliation.

### Final verification evidence

- Export generation and strict validation: 8/8 artifacts passed.
- Ruff and Black: passed.
- Python gate at Phase 1 closure: 198 tests passed at 72.73% coverage.
- Frontend parity: 52 assertions passed.
- Next.js 14.2.35 production build: 7/7 static routes generated.
- Production-export browser checks covered `/`, `/coverage/`, `/forecast/`, and `/recommend/` at
  desktop and mobile widths with visible data, no positive overflow, and no console errors.

### Residual risks

- The public dataset is a frozen October 30, 2025 snapshot.
- Public Vercel deployment remains an optional external step; no backend deployment is required.
- The manifest hashes the direct generator but does not recursively hash every imported module.

## CP-002 — Portfolio-Quality Product

| Field | Value |
|---|---|
| Status | Approved locally; frontend packaging deferred |
| Review date | August 1, 2026 |
| Task range | P2-01 through P2-10 |

### Product behavior

- The proposed flagship home route is recommendation-first.
- Location, quantity, transport rate, and maximum-radius controls are labeled and bounded.
- Top-three summaries expose forecast/as-of and target dates, interval bounds, transport cost,
  expected net price, uncertainty penalty, risk, and the reason for rank order.
- The recommendation route retains the full table, map, and backtest.
- Coverage and forecast routes provide the supporting data and model evidence.
- Loading, empty, error, retry, and stale-data states are explicit.
- Responsive layout, skip navigation, focus treatments, and programmatic labels are implemented.

### Recorded local verification

- Frontend parity: 52 passed, 0 failed, 0 skipped.
- Next.js production build: compiled, typechecked, and generated 7/7 static routes.
- Browser checks at 1440x900 and 390x844 covered all four product routes.
- A mobile interaction changed location to Pune, quantity to 250 qtl, transport rate to
  6 INR/km/qtl, and radius to 100 km; the ranking changed and no request or console error occurred.
- Keyboard checks covered the skip link, decision-control labels, and visible focus.

### Packaging note

The current Next.js source and generated public data are intentionally being held for a separate
frontend commit and deployment pass. Do not claim a public Next.js URL until that pass is complete.

## CP-003 — Defensible ML Engineering

| Field | Value |
|---|---|
| Status | Approved; Complete |
| Closure date | August 1, 2026 |
| Task range | P3-01 through P3-09 |

### Implemented evaluation policy

- Short-gap filling uses only the last value available at each as-of date.
- Primary evaluation requires both the as-of value and t+7 target to be observed.
- Imputed and unavailable targets are counted and excluded rather than silently dropped.
- Three rolling origins precede an untouched 90-day final holdout.
- Recommendation evaluation reports candidate, eligibility, coordinate, realized-target, and
  dropped-row denominators.
- Conditional residual and finite-sample split-conformal intervals are compared under a fixed
  adoption rule.
- Data, feature, coordinate, configuration, interval, matching-tolerance, and result identities are
  bound into one provenance record.

### Final holdout evidence

| Measurement | Value |
|---|---:|
| Holdout dates | 2025-07-26 to 2025-10-23 |
| Total holdout rows | 1,204 |
| Observed-target rows | 792 |
| Imputed targets excluded | 285 |
| Unavailable targets excluded | 127 |
| Moving-average MAE | 133.61 INR/qtl |
| Moving-average RMSE | 246.89 INR/qtl |
| Moving-average sMAPE | 11.73% |

### Interval evidence

| Method | Coverage | Mean width | Interpretation |
|---|---:|---:|---|
| Conditional residual | 86.87% | 493.93 INR/qtl | Undercoverage on observed holdout |
| Split conformal | 90.91% | 528.57 INR/qtl | Closest to 90% nominal under the fixed rule |

Split conformal is adopted for the Phase 3 observed-target evaluation population. The public v1
bundle remains the earlier all-row residual interval and is reported separately.

### Multi-origin recommendation evidence

- Three rolling origins.
- Three transport multipliers per origin: 0.8x, 1.0x, and 1.2x.
- Nine scenario summaries and 63 scenario-date rows.
- Target-ineligible rows are explicitly counted as 17, 19, and 33 across the three origins.
- Each scenario records observed-only target policy, interval bounds, transport assumptions,
  matching tolerance, regret@1/regret@3, nearest-mandi regret, and provenance.

### Corrective review history

An initial review found four evaluation defects and one display-precision defect: observed-target
filtering was not applied to recommendation scenarios; dates without coordinate-bearing candidates
could be omitted; provenance was finalized too early; failure-mode regression evidence was
incomplete; and public regret was double-rounded. The correction pass fixed all five issues and
added end-to-end regression coverage.

### Final verification evidence

- Python: 206 passed, 15 known warnings, 74.90% coverage.
- Phase 3 targeted tests: 8/8 passed.
- Recommendation evaluation tests: 31/31 passed.
- Ruff and Black: passed; 70 files unchanged.
- Strict web export validation: 8/8 with manifest hashes.
- Frontend parity: 52/52 passed.
- Production build: 7/7 static routes.
- Browser smoke loaded the four product routes with visible data, no console errors, no positive
  overflow, and a correctly displayed 296.3 INR/qtl public regret value.

### Final residual risks

- The source snapshot is frozen and is not a live price feed.
- Transport cost uses a configurable approximation, not a route or carrier quote.
- The public v1 interval has one global width; its penalty does not differentiate candidates within
  the same snapshot. Risk display and coverage evidence remain useful, but this limitation must be
  stated in interviews.
- Public frontend deployment is pending the separate frontend packaging pass.
- A few historical documents may retain encoding artifacts.

## Current decision

The data, modeling, API, and evaluation scope is complete for a portfolio MVP. Further crops,
states, horizons, live monitoring, routing, or model families require a separately approved plan.
The remaining release work is frontend packaging, public deployment, and public-CI verification.
