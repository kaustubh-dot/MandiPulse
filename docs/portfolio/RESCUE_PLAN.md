# MandiPulse Portfolio Rescue Plan

> **Historical document.** Retained for narrative and decision context only; it is not active truth.
> Superseded by `docs/IMPLEMENTATION_PLAN.md` (approved execution sequence) and `TODO.md` (live
> worklist). Content below describes the repository as it was when this plan was written.

This is the canonical execution plan for the remaining MandiPulse portfolio work. It is a
documentation-only bootstrap: the bootstrap itself does not change application code, generated
artifacts, metrics, data, or deployment state.

## Portfolio position and authority

MandiPulse is primarily an **ML Engineer portfolio project**: an offline, transport-cost-aware
mandi decision intelligence system for Maharashtra onion markets. The portfolio story is the
complete engineering chain—point-in-time data, forecasting, uncertainty, recommendation logic,
evaluation, provenance, and a credible product surface—not a generic crop-price prediction demo.

The repository owner is the product and scope authority. Material plan changes—including scope,
task IDs, metric definitions, public contracts, phase gates, and acceptance criteria—require
explicit approval. Each phase must be implemented, independently reviewed, and verified before it
is marked complete. A passing build is evidence of buildability, not portfolio completion.

## Frozen scope

| Dimension | Frozen decision |
|---|---|
| Crop | Onion |
| State | Maharashtra |
| Markets | 15 mandis |
| Forecast horizon | 7 days |
| Data snapshot | October 30, 2025 |
| Flagship product surface | Next.js |
| Secondary surface | Streamlit |
| API role | FastAPI is a local snapshot API unless connected to a real consumer |

The scope, the task IDs below, and the phase gates are stable. Any material change requires the
repository-owner approval and an update to the canonical documents before implementation.

## Phase 1 — Finished and Trustworthy MVP

### Goal

Make the existing MVP trustworthy as a reproducible ML Engineer portfolio artifact. Repair export
validity, metric and wording drift, as-of semantics, API boundaries, provenance, product-surface
positioning, and release hygiene while keeping the frozen Onion/Maharashtra/15-mandi/7-day scope.

### Task table

| ID | Task |
|---|---|
| P1-01 | Strict, finite, schema-validated JSON exports. |
| P1-02 | Canonical metrics and corrected public wording. |
| P1-03 | Shared forecast as-of and candidate-availability policy. |
| P1-04 | API validation, configured limits, and health semantics. |
| P1-05 | Versioned artifact manifest and provenance metadata. |
| P1-06 | Next.js flagship deployment and product-surface positioning. |
| P1-07 | Documentation and release hygiene. |
| P1-08 | Phase 1 verification and finish gate. |

### Dependencies

- Baseline audit checkpoint CP-000 and the frozen scope above.
- Existing sample artifacts, reports, API schemas, frontend routes, and CI configuration remain the
  starting point; no silent replacement of historical milestone documents.
- P1-01 through P1-05 establish the data, metric, interface, and provenance contracts required by
  P1-06 and P1-07.
- P1-08 depends on every preceding Phase 1 task and on the evidence package being complete.

### Public interface changes

- Exported JSON becomes a strict finite-value contract with explicit schemas and stable field names.
- Forecast and recommendation consumers share one forecast as-of and candidate-availability policy.
- FastAPI validates supported crop, state, horizon, mandi, coordinates, quantity, radius, and
  alternative limits; `/health` reports readiness semantics rather than merely process liveness.
- Artifact metadata exposes version, snapshot, as-of, source, configuration, model, and generation
  provenance sufficient to identify the exact public bundle.
- Next.js is the flagship public surface; Streamlit is secondary; FastAPI remains a local snapshot
  API unless a real consumer is intentionally connected.
- Any changed public contract must be reflected in the API spec, frontend types/loaders, README,
  reports, generated exports, and the checkpoint evidence.

### Acceptance criteria

- Every exported JSON file passes strict `JSON.parse` and schema validation.
- No exported JSON value is `NaN`, `Infinity`, or `-Infinity`.
- Real browser smoke tests cover the coverage, forecast, and recommendation routes.
- The smoke tests show no blank pages and no uncaught promise errors or page errors.
- Displayed metrics agree across reports, README, API responses, and the frontend; labels describe
  the same denominator, split, confidence level, and snapshot.
- Forecast as-of dates, candidate availability, radius filtering, and alternative limits are
  explicit and consistent across the API, Streamlit, Next.js, reports, and exports.
- API edge cases return the documented typed errors and configured limits; health semantics clearly
  distinguish service availability from data readiness.
- The artifact manifest and provenance metadata identify the data snapshot, code/config/model
  versions, generation inputs, and validation result.
- Ruff, Black, Python tests, frontend parity tests, and the production build remain green at the
  audited baseline or have an explicitly recorded, approved explanation for any change.
- **Build success alone is not sufficient.** Runtime/browser evidence and cross-surface metric
  agreement are mandatory for this gate.

### Exact verification expectations

1. Enumerate every committed export under `web/public/data/` and every release export path. Parse
   each file with a standards-compliant JSON parser using strict `JSON.parse`; validate each file
   against its committed schema and fail on the first error.
2. Scan all exported JSON text and parsed numeric values for `NaN`, `Infinity`, and `-Infinity`;
   the expected result is zero occurrences and zero non-finite values.
3. Run the repository quality gates: `ruff check api app src scripts tests`,
   `black --check api app src scripts tests`, `pytest -q`, `cd web; npm test`, and
   `cd web; npm run build`. Record exact command output, test counts, and coverage.
4. Start the production Next.js surface and use a real browser to visit `/coverage`, `/forecast`,
   and `/recommend`. Record route URLs, selected inputs, screenshots or equivalent runtime
   evidence, console errors, page errors, and uncaught promise errors. All three routes must render
   meaningful content.
5. Exercise FastAPI with valid requests and invalid crop, state, horizon, mandi, coordinate,
   quantity, radius, and alternative-limit cases. Exercise both ready and unavailable data states
   for `/health`. Record HTTP status, error code, response shape, and limit behavior.
6. Reconcile the canonical metric values from the reports to README, API payloads, and frontend
   displays. Record the compared paths, fields, denominators, dates, and exact values; any mismatch
   fails the gate.
7. Inspect the manifest/provenance entry for every public artifact and confirm that the recorded
   snapshot, as-of policy, source, configuration, model, and validation results reproduce the
   bundle identity.

### Handoff requirements

Complete the whole phase, update CP-001 in [CHECKPOINTS.md](CHECKPOINTS.md), and only then request
review. The handoff must include the base
and head commits, all completed task IDs, files and interfaces changed, exact commands and results,
real browser evidence, failures or skipped checks, residual risks, implementation notes, and a
clear statement that the phase is ready for independent review. Implementation completion alone
does not mark the checkpoint Approved or Complete.

### Explicit Phase 1 finish point

Phase 1 is finished only when P1-01 through P1-08 pass their acceptance criteria and independent review marks
CP-001 Approved and Complete. Phase 2 does not start before that point. This documentation
bootstrap ends with Phase 1 **Not Started**; it does not mark Phase 1 Ready for Review.

## Phase 2 — Portfolio-Quality Product

### Goal

Turn the trustworthy MVP into a clear, recommendation-first portfolio product whose decision path
is understandable to a farmer, reviewer, or hiring manager on desktop and mobile.

### Task table

| ID | Task |
|---|---|
| P2-01 | Recommendation-first home page. |
| P2-02 | Location, quantity, transport-rate, and radius inputs. |
| P2-03 | Top-three recommendation summary and explanation. |
| P2-04 | Correct forecast-date and uncertainty visualization. |
| P2-05 | Dedicated full-history coverage interface. |
| P2-06 | Loading, empty, error, retry, and stale-data states. |
| P2-07 | Small, consistent design system. |
| P2-08 | Responsive and accessibility hardening. |
| P2-09 | README screenshot, walkthrough, and case study. |
| P2-10 | Phase 2 portfolio gate. |

### Dependencies

- CP-001 must be independently approved and complete.
- P1-01 through P1-05 define the data and API contracts consumed by the product surface.
- P2-10 depends on all preceding Phase 2 tasks and on the Phase 1 runtime evidence remaining valid.

### Public interface changes

- The Next.js home route becomes the recommendation entry point and exposes location, quantity,
  transport-rate, and radius inputs within the frozen scope.
- The frontend exposes the top three ranked alternatives with explanations, forecast dates,
  uncertainty, transport cost, net price, and risk labels.
- Coverage and forecast routes expose the full history and correct as-of/uncertainty semantics;
  loading, empty, error, retry, and stale-data states become deliberate UI states.
- Accessibility and responsive behavior are part of the product contract. Existing API fields and
  task scope remain stable unless the repository owner approves a material change.

### Acceptance criteria

- The first screen communicates the recommended mandi and the assumptions behind the decision.
- Users can enter location, quantity, transport rate, and maximum radius without changing crop,
  state, or horizon outside the frozen scope.
- The top three recommendations explain forecast, transport, net price, uncertainty penalty, risk,
  and the reason for rank order.
- Forecast dates and interval bounds are labeled correctly and are not presented as guarantees.
- Full history and coverage diagnostics have a dedicated, usable interface.
- Every data-fetch state has intentional loading, empty, error, retry, and stale-data behavior.
- Visual tokens and components form a small consistent design system.
- Desktop and mobile layouts are usable; keyboard navigation, focus, labels, contrast, and semantic
  structure satisfy the agreed accessibility checks.
- README contains a short product-surface walkthrough and ML Engineer case study that agrees with
  the released product and canonical metrics. Frontend screenshots publish with the separate
  frontend release.
- Phase 2 does not widen the frozen data, crop, state, or horizon scope.

### Exact verification expectations

1. Run `cd web; npm test` and `cd web; npm run build`, recording exact output and artifact status.
2. Use a real browser against the production build for the home, coverage, forecast, and
   recommendation routes. Test representative valid inputs and every defined loading, empty, error,
   retry, and stale-data state; retain route evidence and console/page-error logs.
3. Repeat the browser pass at desktop and mobile viewport sizes, using keyboard-only navigation for
   the main decision flow. Record focus order, accessible names, visible focus, contrast findings,
   and any skipped accessibility check with a reason.
4. Verify that the top-three display, dates, intervals, transport values, and rankings match the
   validated export/API payloads for the same snapshot and inputs.
5. Re-run the README walkthrough from a clean clone or equivalent clean checkout and confirm every
   linked route, metric, screenshot caption, and product-surface claim is current.
6. Record the full browser/runtime evidence in CP-002; a build or screenshot without interaction
   evidence does not pass the portfolio gate.

### Handoff requirements

Update CP-002 after completing all Phase 2 tasks, including the UI routes and public fields
changed, exact build/test commands and results, desktop/mobile browser evidence, accessibility
findings, README walkthrough evidence, residual risks, and a handoff statement. The whole phase then
receives independent review; localized fixes must be recorded in the checkpoint.

### Finish point

Phase 2 is finished only when P2-01 through P2-10 pass and independent review marks CP-002 Approved
and Complete.
The product may not be described as portfolio-ready based on visual polish or build output alone.

## Phase 3 — Defensible ML Engineering

### Goal

Make the modeling and recommendation claims defensible under point-in-time data rules, observed
targets, honest evaluation denominators, transport assumptions, and reproducible uncertainty
comparisons.

### Task table

| ID | Task |
|---|---|
| P3-01 | Point-in-time-safe imputation. |
| P3-02 | Observed-target metrics as the primary evaluation. |
| P3-03 | Rolling-origin evaluation and untouched final holdout. |
| P3-04 | Robust recommendation metrics and matched denominators. |
| P3-05 | Multi-origin and transport-cost backtesting. |
| P3-06 | Coordinate, data, and transport-assumption provenance. |
| P3-07 | Conditional/conformal interval comparison and adoption rule. |
| P3-08 | Numerical miniature end-to-end tests. |
| P3-09 | Phase 3 resume gate. |

### Dependencies

- CP-002 must be independently approved and complete, or the repository owner must explicitly approve a different
  sequencing decision.
- Phase 1's canonical export, metric, as-of, and provenance contracts are prerequisites.
- P3-01 through P3-06 establish trustworthy evaluation inputs; P3-07 compares interval methods;
  P3-08 provides small deterministic regression protection; P3-09 consumes all evidence.

### Public interface changes

- Reports and metrics exports distinguish observed targets from imputed values and publish split,
  origin, denominator, and holdout definitions.
- Backtest outputs expose the as-of origin, realized-target eligibility, transport assumptions, and
  matched denominators needed to interpret regret and coverage.
- Artifact provenance includes coordinates, source data snapshot, transport configuration, interval
  method, and adoption decision.
- Any new metric or field must be versioned and reflected consistently in reports, README, API,
  frontend, schemas, and generated artifacts. No extra crop, state, or horizon is introduced.

### Acceptance criteria

- Imputation uses only information available at the relevant as-of time and is tested against
  future-information leakage.
- Observed targets are the primary evaluation population; imputed targets are labeled, excluded,
  or separately reported according to a documented rule.
- Rolling-origin evaluation is reproducible and the final holdout is untouched until the declared
  final evaluation.
- Recommendation metrics use robust, matched denominators and report eligibility exclusions rather
  than silently dropping dates or markets.
- Backtesting covers multiple origins and explicit transport-cost assumptions.
- Coordinates, source data, model/config versions, and transport assumptions are traceable to each
  result.
- Conditional and conformal interval methods are compared on coverage, width, and failure modes;
  the adopted method follows a documented rule rather than a post-hoc metric selection.
- Numerical miniature tests cover the end-to-end calculations and catch denominator, leakage,
  interval, ranking, and provenance regressions.
- P3-09 passes only with reproducible evidence, aligned documentation, and no unresolved critical
  evaluation or provenance risk.

### Exact verification expectations

1. Run deterministic point-in-time leakage tests with synthetic data whose future values would alter
   an unsafe imputation; the unsafe implementation must fail the test and the approved one must not
   use future rows.
2. Re-run rolling-origin metrics and the untouched final holdout from a fixed snapshot. Record
   origin dates, train/validation/test boundaries, target eligibility, row counts, observed versus
   imputed counts, and every denominator.
3. Re-run recommendation backtests across multiple origins and transport-cost scenarios. Reconcile
   candidate counts, exclusions, regret@K, missed-profit measures, and nearest-mandi baselines to
   the same eligible dates and markets.
4. Validate provenance fields from source data through features, predictions, intervals,
   recommendations, reports, and public exports; a result without an identifiable snapshot,
   coordinate source, or transport assumption fails.
5. Compare conditional and conformal interval candidates on the untouched evaluation protocol,
   including empirical coverage, interval width, nominal level, and observed-target denominator.
   Execute the documented adoption rule and preserve the comparison artifact.
6. Run the numerical miniature end-to-end suite and the complete Python/web quality gates. Record
   exact commands, results, and any intentionally skipped expensive check.
7. Independently inspect the evidence package and confirm that reports, README, metrics,
   generated artifacts, API, and frontend agree before the resume gate is marked complete.

### Handoff requirements

Update CP-003 with the complete evaluation/provenance evidence, exact commands and
results, changed reports/interfaces, holdout and denominator definitions, interval comparison,
miniature-test output, residual risks, and a resume recommendation. Independent review records
findings by severity and all localized fixes, then decides Approved or Changes Requested.

### Explicit Phase 3 resume-grade point

The project reaches a **resume-grade point** only when P3-01 through P3-09 pass, CP-003 is marked
Approved and Complete after independent review, and the evidence package is reproducible with no unresolved critical
evaluation, leakage, interface, or provenance risk. Resume-grade does not authorize scope expansion:
the repository owner must still approve the next material plan before deferred work resumes.

## Explicit exclusions

The rescue plan does not include:

- Additional crops or states.
- 14/30-day horizons.
- Deep learning and transformer forecasting.
- Kubernetes, microservices, mobile apps, and unrelated feature expansion.

These exclusions remain frozen unless the repository owner explicitly approves a material plan change and the
canonical documents are updated first.
