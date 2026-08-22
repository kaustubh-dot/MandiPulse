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
| RG-01 | Scope and product truth | Fail | Public naming, schemas, reports, and UI describe transport-adjusted ranking; uncertainty is represented accurately |
| RG-02 | Data and artifact integrity | Baseline pass | Export validation passes; sample and web artifacts are current, schema-versioned, secret-free, and reproducible |
| RG-03 | Forecast and evaluation integrity | Baseline pass | Temporal tests pass; shipped-policy and Phase 3 metrics reproduce within documented tolerance |
| RG-04 | Recommendation integrity | Baseline pass with wording blocker | Regret evaluation reproduces; Python and TypeScript fixtures match; unsupported risk-adjusted wording is absent |
| RG-05 | Python quality | Baseline pass | Ruff and Black pass; all Python tests pass; coverage report is recorded |
| RG-06 | API contract | Baseline pass | API tests and OpenAPI checks pass; fields, descriptions, CORS/deployment settings, and errors match final contract |
| RG-07 | Next.js functionality | Pending | All four route contracts and primary browser flows pass from the production static export |
| RG-08 | Streamlit functionality | Pending | All pages and the primary decision flow pass with sample artifacts and no secret |
| RG-09 | Cross-surface parity | Pending | Fixed fixtures produce identical rank, amounts, units, rounding, defaults, snapshot wording, and uncertainty treatment |
| RG-10 | Dependency security | Fail | Production audit has no unresolved high/critical issue, or a reviewed time-bounded exception exists |
| RG-11 | Accessibility | Pending | Automated and manual checks meet the thresholds below on both interfaces |
| RG-12 | Responsive and visual quality | Pending | Accepted screenshots and manual review cover all routes, states, and required viewport sizes |
| RG-13 | Performance | Pending | Production pages meet the budgets below and have no unexplained regression |
| RG-14 | Documentation consistency | Fail | README and active docs match the final commit, commands, scope, metrics, limitations, and URLs |
| RG-15 | CI and repository hygiene | Pending | Required CI is green on release commit; worktree is clean; no generated or secret files are tracked accidentally |
| RG-16 | Public deployment | Pending | Next.js and Streamlit URLs work signed out and complete the primary flows after deployment |
| RG-17 | Portfolio evidence | Pending | Final screenshots, demo path, release commit, verification date, and source-backed resume claims are recorded |

## 3. Detailed Acceptance Criteria

### RG-01 — Scope and Product Truth

- [ ] Onion, Maharashtra, 15 mandis, and seven-day horizon are stated consistently.
- [ ] Snapshot end date 2025-10-30 is visible anywhere a result is shown.
- [ ] Ranking is described as transport-adjusted net expected price.
- [ ] Uncertainty is not claimed to change candidate order unless candidate-specific behavior is implemented and validated.
- [ ] Haversine distance × 1.3 is described as an estimate, not road routing.
- [ ] INR 4/km/quintal is described as a configurable scenario, not a carrier quotation.
- [ ] No live-price, guaranteed-income, trading, or causal claim appears.

### RG-02 — Data and Artifact Integrity

- [ ] The export validation script passes.
- [ ] The clean panel contains the expected 31,950 rows and 15 selected mandis.
- [ ] Latest date and schema versions match across sample, API, and static web artifacts.
- [ ] Committed artifacts can be regenerated with documented commands.
- [ ] Regeneration produces no unexpected data or schema drift.
- [ ] No raw secret, credential, user coordinate, local absolute path, or ignored large artifact is committed.

### RG-03 — Forecast and Evaluation Integrity

- [ ] Temporal splits and purge rules are covered by tests.
- [ ] No future target or feature information crosses a split boundary.
- [ ] The moving-average shipped-policy test MAE of 139.57 is traceable to a committed report.
- [ ] The 792-row Phase 3 observed-target holdout and MAE 133.61 reproduce within the documented tolerance.
- [ ] Conditional residual coverage 86.87% and split-conformal coverage 90.91% are labeled with their correct evaluation context.
- [ ] Interface changes do not alter the selected model policy or metric calculations.

### RG-04 — Recommendation Integrity

- [ ] Mean regret@1 296.3, nearest baseline 370.1, and 74.4% win rate are traceable to committed evidence.
- [ ] Ranking arithmetic is tested for distance, road factor, transport rate, quantity, and rounding.
- [ ] Python and TypeScript candidate order and displayed values match fixed fixtures.
- [ ] Recommendations are deterministic for identical inputs and artifacts.
- [ ] Invalid coordinates, invalid quantity, missing coordinates, and missing forecast data fail safely.

### RG-05 — Python Quality

```powershell
ruff check api app src scripts tests
black --check api app src scripts tests
pytest -q
```

- [ ] All commands exit successfully.
- [ ] Final test count and coverage are recorded in `docs/portfolio/CURRENT_STATE.md`.
- [ ] No expected failure, deselected correctness test, warning flood, or hidden network dependency remains.

### RG-06 — API Contract

- [ ] OpenAPI output matches the implemented routes and final ranking vocabulary.
- [ ] Success, validation, missing-artifact, and internal-error responses have tests.
- [ ] Response fields expose units or have unambiguous documented units.
- [ ] Deployed CORS origins are explicit if the API is hosted; wildcard remains limited to the documented local/public read-only case.
- [ ] API startup and health checks do not require a private upstream key.

### RG-07 — Next.js Functionality

- [ ] `/`, `/recommend`, `/forecast`, and `/coverage` load directly from the static export.
- [ ] The user can complete the Decision flow from valid defaults.
- [ ] Invalid inputs preserve values and show inline messages.
- [ ] Selected mandi and stable decision inputs round-trip through URL state where specified.
- [ ] Loading, empty, missing, stale, partial, and calculation-error states are covered.
- [ ] No primary flow produces an uncaught console error or hydration error.
- [ ] `npm test` and `npm run build` pass from a clean install.

### RG-08 — Streamlit Functionality

- [ ] The documented Streamlit command starts without an API key.
- [ ] Coverage, Forecast, and Recommendation pages load from committed sample artifacts.
- [ ] Controls rerun predictably and do not unexpectedly reset valid user input.
- [ ] Missing artifacts and invalid inputs produce actionable messages rather than tracebacks.
- [ ] Units, defaults, rank, and copy match the shared product contract.

### RG-09 — Cross-Surface Parity

For at least three fixed location/quantity scenarios:

- [ ] Python, API, Next.js, and Streamlit select the same first-ranked mandi.
- [ ] All candidate ranks match.
- [ ] Gross price, distance, transport cost, net price, and totals match within the declared rounding tolerance.
- [ ] Snapshot date, road factor, transport rate, horizon, and uncertainty labels match.
- [ ] Missing-data behavior does not silently diverge.

### RG-10 — Dependency Security

```powershell
Set-Location web
npm.cmd audit --omit=dev
npm.cmd test
npm.cmd run build
```

- [ ] No unresolved high or critical production finding remains.
- [ ] Framework and runtime versions are supported and pinned through the lockfile.
- [ ] Any accepted exception names the advisory, explains non-applicability, names an owner, and expires within 30 days.
- [ ] Dependency migration has not weakened linting, type checking, tests, or static export behavior.

### RG-11 — Accessibility

- [ ] Zero serious or critical automated accessibility violations on each route/page and the mobile navigation state.
- [ ] Keyboard-only users can navigate, edit inputs, calculate, inspect alternatives, and open/close overlays.
- [ ] Focus is visible, ordered, and restored after sheets or dialogs close.
- [ ] Every input has a persistent programmatic label and associated error text.
- [ ] Color is never the only carrier of rank, status, missingness, or forecast state.
- [ ] Text contrast meets WCAG AA; essential graphical objects meet non-text contrast requirements.
- [ ] Content remains usable at 200% zoom and with reduced motion enabled.

### RG-12 — Responsive and Visual Quality

Review widths: 320, 375, 768, 1024, 1440, and 1920 px.

- [ ] No unintended horizontal page scrolling.
- [ ] Primary action and result remain discoverable without decorative obstruction.
- [ ] Tables, charts, maps, and form controls have deliberate narrow-screen behavior.
- [ ] Typography, spacing, colors, radii, and component states match `docs/DESIGN.md`.
- [ ] All routes and important data states have accepted screenshots after two review passes.
- [ ] Next.js and Streamlit share one visual identity without forced pixel imitation.

### RG-13 — Performance

Measure the production build with a consistent tool and network profile.

- [ ] Lighthouse performance score is at least 90 on `/`, `/recommend`, `/forecast`, and `/coverage` under the chosen reproducible profile.
- [ ] Accessibility score is 100 unless a documented tool false positive is manually verified.
- [ ] Largest Contentful Paint is at most 2.5 seconds at the 75th-percentile target profile.
- [ ] Cumulative Layout Shift is at most 0.1.
- [ ] Interaction to Next Paint is at most 200 ms where measurable.
- [ ] Initial page content is not blocked by nonessential charts, maps, or fonts.

These are portfolio release budgets, not claims about field performance on every rural network. Record the exact measurement environment.

### RG-14 — Documentation Consistency

- [ ] README alone is sufficient to install, test, build, and run both interfaces.
- [ ] PRD, architecture, API, flow, design, tracker, release, and current-state documents do not contradict shipped scope.
- [ ] Historical plans are labeled historical rather than presented as active truth.
- [ ] Commands have been run from a clean clone or equivalent clean environment.
- [ ] Public URLs and screenshots correspond to the release commit.

### RG-15 — CI and Repository Hygiene

- [ ] Required GitHub Actions checks pass on the release commit.
- [ ] The release commit is pushed and identifiable.
- [ ] `git status --short` is empty after release artifacts are committed.
- [ ] `.gitignore` covers build outputs, virtual environments, raw data, model stores, logs, screenshots not intended as evidence, and local secrets.
- [ ] Lockfiles and generated public artifacts are intentional and reviewed.
- [ ] No unfinished marker, placeholder copy, dead navigation, or disabled primary feature remains.

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
