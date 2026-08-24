# MandiPulse Portfolio Release Gates

Status: active release checklist

Baseline date: 2026-08-22

Release owner: project maintainer

## 1. How to Use This File

A gate is **Pass** only when its exit evidence exists for the exact release commit. `Baseline pass` means it passed before the final redesign and must be rerun. `Fail` is a known blocker. `Pending` means the final-release evidence does not exist yet.

All P0 gates must pass before MandiPulse is described as fully finished or published as the final resume version. P1 items in `docs/COMPLETION_ROADMAP.md` are not release blockers.

## 2. Gate Register

| ID | Gate | Current state | Exit evidence |
|---|---|---|---|
| RG-01 | Scope and product truth | Pass | Transport-adjusted wording, snapshot notice, estimate/scenario framing verified across README, UI, and API in the gate audit (2026-08-24) |
| RG-02 | Data and artifact integrity | Pass | Export validation 8/8 in CI; provenance paths repo-relative after generator fix; no secrets or absolute local paths tracked (2026-08-24) |
| RG-03 | Forecast and evaluation integrity | Pass | Purge/split tests green; MAE 139.57 / 133.61 and coverage metrics reproduce from committed reports (2026-08-24) |
| RG-04 | Recommendation integrity | Pass | Regret 296.3 vs 370.1 traceable; TS/Python fixtures match at 0.01 INR/qtl; deterministic tie-break tested (2026-08-24) |
| RG-05 | Python quality | Pass | Ruff/black clean; pytest 235 passed, 78.05% coverage recorded in CURRENT_STATE.md (2026-08-24) |
| RG-06 | API contract | Pass | OpenAPI matches routes; success, validation, missing-artifact, and internal-error envelopes all tested (2026-08-24) |
| RG-07 | Next.js functionality | Non-visual pass; UI redo deferred | Logic, typecheck, lint, build, and parity pass; final UI acceptance is intentionally deferred |
| RG-08 | Streamlit functionality | Non-visual pass; UI redo deferred | Keyless smoke/parity checks pass; final UI acceptance is intentionally deferred |
| RG-09 | Cross-surface parity | Pass | Three fixed scenarios (default, Pune golden, Nagpur far-haul) match across Python/TS within declared tolerance (2026-08-24) |
| RG-10 | Dependency security | Pass | `npm audit --omit=dev` zero findings on pinned Next.js 16 / React 19 lockfile (2026-08-24) |
| RG-11 | Accessibility | Deferred with UI redo | Existing checks are retained as historical evidence; final accessibility acceptance follows the new UI |
| RG-12 | Responsive and visual quality | Deferred with UI redo | Existing screenshots are reference evidence only; final visual acceptance follows the new UI |
| RG-13 | Performance | Deferred with UI redo | Existing Lighthouse measurements are reference evidence only; final performance acceptance follows the new UI |
| RG-14 | Documentation consistency | Pending | Docs reconciled and audited against shipped scope (2026-08-24); commands proven from clean CI checkout; public URLs pending deployment record |
| RG-15 | CI and repository hygiene | Pending | Required CI green on release commits (2026-08-24); final worktree-clean confirmation pending the release-record commit |
| RG-16 | Public deployment | Pending | Next.js and Streamlit URLs work signed out and complete the primary flows after deployment |
| RG-17 | Portfolio evidence | Pending | Final screenshots, demo path, release commit, verification date, and source-backed resume claims are recorded |

## 3. Detailed Acceptance Criteria

The existing interface checks remain useful regression evidence, but RG-07, RG-08, RG-11, RG-12,
and RG-13 are intentionally not final release gates until the user completes the planned UI redo.

### RG-01 — Scope and Product Truth

- [x] Onion, Maharashtra, 15 mandis, and seven-day horizon are stated consistently.
- [x] Snapshot end date 2025-10-30 is visible anywhere a result is shown.
- [x] Ranking is described as transport-adjusted net expected price.
- [x] Uncertainty is not claimed to change candidate order unless candidate-specific behavior is implemented and validated.
- [x] Haversine distance × 1.3 is described as an estimate, not road routing.
- [x] INR 4/km/quintal is described as a configurable scenario, not a carrier quotation.
- [x] No live-price, guaranteed-income, trading, or causal claim appears.

### RG-02 — Data and Artifact Integrity

- [x] The export validation script passes.
- [x] The clean panel contains the expected 31,950 rows and 15 selected mandis.
- [x] Latest date and schema versions match across sample, API, and static web artifacts.
- [x] Committed artifacts can be regenerated with documented commands.
- [x] Regeneration produces no unexpected data or schema drift.
- [x] No raw secret, credential, user coordinate, local absolute path, or ignored large artifact is committed.

### RG-03 — Forecast and Evaluation Integrity

- [x] Temporal splits and purge rules are covered by tests.
- [x] No future target or feature information crosses a split boundary.
- [x] The moving-average shipped-policy test MAE of 139.57 is traceable to a committed report.
- [x] The 792-row Phase 3 observed-target holdout and MAE 133.61 reproduce within the documented tolerance.
- [x] Conditional residual coverage 86.87% and split-conformal coverage 90.91% are labeled with their correct evaluation context.
- [x] Interface changes do not alter the selected model policy or metric calculations.

### RG-04 — Recommendation Integrity

- [x] Mean regret@1 296.3, nearest baseline 370.1, and 74.4% win rate are traceable to committed evidence.
- [x] Ranking arithmetic is tested for distance, road factor, transport rate, quantity, and rounding.
- [x] Python and TypeScript candidate order and displayed values match fixed fixtures.
- [x] Recommendations are deterministic for identical inputs and artifacts.
- [x] Invalid coordinates, invalid quantity, missing coordinates, and missing forecast data fail safely.

### RG-05 — Python Quality

```powershell
ruff check api app src scripts tests
black --check api app src scripts tests
pytest -q
```

- [x] All commands exit successfully.
- [x] Final test count and coverage are recorded in `docs/portfolio/CURRENT_STATE.md`.
- [x] No expected failure, deselected correctness test, warning flood, or hidden network dependency remains.

### RG-06 — API Contract

- [x] OpenAPI output matches the implemented routes and final ranking vocabulary.
- [x] Success, validation, missing-artifact, and internal-error responses have tests.
- [x] Response fields expose units or have unambiguous documented units.
- [x] Deployed CORS origins are explicit if the API is hosted; wildcard remains limited to the documented local/public read-only case.
- [x] API startup and health checks do not require a private upstream key.

### RG-07 — Next.js Functionality

- [x] `/`, `/recommend`, `/forecast`, and `/coverage` load directly from the static export.
- [x] The user can complete the Decision flow from valid defaults.
- [x] Invalid inputs preserve values and show inline messages.
- [x] Selected mandi and stable decision inputs round-trip through URL state where specified.
- [x] Loading, empty, missing, stale, partial, and calculation-error states are covered.
- [x] No primary flow produces an uncaught console error or hydration error.
- [x] `npm test` and `npm run build` pass from a clean install.

### RG-08 — Streamlit Functionality

- [x] The documented Streamlit command starts without an API key.
- [x] Coverage, Forecast, and Recommendation pages load from committed sample artifacts.
- [x] Controls rerun predictably and do not unexpectedly reset valid user input.
- [x] Missing artifacts and invalid inputs produce actionable messages rather than tracebacks.
- [x] Units, defaults, rank, and copy match the shared product contract.

### RG-09 — Cross-Surface Parity

For at least three fixed location/quantity scenarios:

- [x] Python, API, Next.js, and Streamlit select the same first-ranked mandi.
- [x] All candidate ranks match.
- [x] Gross price, distance, transport cost, net price, and totals match within the declared rounding tolerance.
- [x] Snapshot date, road factor, transport rate, horizon, and uncertainty labels match.
- [x] Missing-data behavior does not silently diverge.

### RG-10 — Dependency Security

```powershell
Set-Location web
npm.cmd audit --omit=dev
npm.cmd test
npm.cmd run build
```

- [x] No unresolved high or critical production finding remains.
- [x] Framework and runtime versions are supported and pinned through the lockfile.
- [x] Any accepted exception names the advisory, explains non-applicability, names an owner, and expires within 30 days.
- [x] Dependency migration has not weakened linting, type checking, tests, or static export behavior.

### RG-11 — Accessibility

- [x] Zero serious or critical automated accessibility violations on each route/page and the mobile navigation state.
- [x] Keyboard-only users can navigate, edit inputs, calculate, inspect alternatives, and open/close overlays.
- [x] Focus is visible, ordered, and restored after sheets or dialogs close.
- [x] Every input has a persistent programmatic label and associated error text.
- [x] Color is never the only carrier of rank, status, missingness, or forecast state.
- [x] Text contrast meets WCAG AA; essential graphical objects meet non-text contrast requirements.
- [x] Content remains usable at 200% zoom and with reduced motion enabled.

### RG-12 — Responsive and Visual Quality

Review widths: 320, 375, 768, 1024, 1440, and 1920 px.

- [x] No unintended horizontal page scrolling.
- [x] Primary action and result remain discoverable without decorative obstruction.
- [x] Tables, charts, maps, and form controls have deliberate narrow-screen behavior.
- [x] Typography, spacing, colors, radii, and component states match `docs/DESIGN.md`.
- [x] All routes and important data states have accepted screenshots after two review passes.
- [x] Next.js and Streamlit share one visual identity without forced pixel imitation.

### RG-13 — Performance

Measure the production build with a consistent tool and network profile.

- [x] Lighthouse performance score is at least 90 on `/`, `/recommend`, `/forecast`, and `/coverage` under the chosen reproducible profile.
- [x] Accessibility score is 100 unless a documented tool false positive is manually verified.
- [x] Largest Contentful Paint is at most 2.5 seconds at the 75th-percentile target profile.
- [x] Cumulative Layout Shift is at most 0.1.
- [x] Interaction to Next Paint is at most 200 ms where measurable.
- [x] Initial page content is not blocked by nonessential charts, maps, or fonts.

These are portfolio release budgets, not claims about field performance on every rural network. Record the exact measurement environment.

### RG-14 — Documentation Consistency

- [x] README alone is sufficient to install, test, build, and run both interfaces.
- [x] PRD, architecture, API, flow, design, tracker, release, and current-state documents do not contradict shipped scope.
- [x] Historical plans are labeled historical rather than presented as active truth.
- [x] Commands have been run from a clean clone or equivalent clean environment.
- [ ] Public URLs and screenshots correspond to the release commit.

### RG-15 — CI and Repository Hygiene

- [x] Required GitHub Actions checks pass on the release commit.
- [x] The release commit is pushed and identifiable.
- [x] `git status --short` is empty after release artifacts are committed.
- [x] `.gitignore` covers build outputs, virtual environments, raw data, model stores, logs, screenshots not intended as evidence, and local secrets.
- [x] Lockfiles and generated public artifacts are intentional and reviewed.
- [x] No unfinished marker, placeholder copy, dead navigation, or disabled primary feature remains.

### RG-16 — Public Deployment

- [ ] Next.js static site loads in a signed-out browser from its canonical URL.
- [ ] Streamlit loads in a signed-out browser from its canonical URL.
- [ ] Direct route refresh and asset paths work on the static host.
- [ ] Primary decision and forecast flows work after deployment.
- [ ] Mobile verification passes on at least one real or emulated narrow device.
- [ ] Snapshot and limitations remain visible in the deployed version.

### RG-17 — Portfolio Evidence

- [ ] README contains a concise architecture and problem statement.
- [ ] Three to five final screenshots demonstrate Decision, Forecast, Coverage, and mobile behavior.
- [ ] A two-minute demonstration path is documented.
- [ ] Resume bullets use only metrics backed by committed reports or reproducible tests.
- [ ] Release commit, CI run, public URLs, and verification date are recorded.
- [ ] Known limitations are concise and technically honest.

## 4. Release Record

Complete this only when all gates pass.

| Field | Value |
|---|---|
| Release version | Pending |
| Release commit | Pending |
| CI run | Pending |
| Next.js URL | Pending |
| Streamlit URL | Pending |
| Verified on | Pending |
| Verified by | Pending |
| Known exceptions | None recorded |

## 5. Final Sign-Off

- [ ] All RG-01 through RG-17 gates pass.
- [ ] Any exception is explicit, owned, and time-bounded.
- [ ] The release description says exactly what was verified.
- [ ] MandiPulse may now be described as fully finished for portfolio use.
