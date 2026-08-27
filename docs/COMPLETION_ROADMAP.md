# MandiPulse End-to-End Completion Roadmap

Status: historical finish inventory

Last audited: 2026-08-22

> **Historical document.** Retained for narrative and decision context only; it is not active truth.
> Superseded by `docs/IMPLEMENTATION_PLAN.md` (approved execution sequence) and `TODO.md` (live
> worklist). Content below describes the repository as it was when this roadmap was written.

Scope: portfolio-quality Onion / Maharashtra / seven-day product

## 1. Verdict

MandiPulse is not fully finished yet. The data, modeling, recommendation, API, and artifact layers are substantial and tested. The remaining work is concentrated in product truth, a complete replacement of both interfaces, frontend security and test depth, documentation consistency, and public release evidence.

The project is ready to enter a focused finish track. It does not need a wider crop/state scope or a more complex model to be credible on a resume.

## 2. Verified Baseline

| Area | Current evidence | Status |
|---|---|---|
| Data | 15 Maharashtra onion mandis; 31,950-row clean panel; snapshot through 2025-10-30 | Strong |
| Forecast policy | Moving-average policy selected on held-out test MAE of 139.57 INR/quintal | Strong |
| Phase 3 evaluation | 792-row observed-target holdout; MAE 133.61; conditional residual coverage 86.87%; split-conformal coverage 90.91% | Strong |
| Recommendation evaluation | Mean regret@1 296.3 vs nearest-mandi 370.1; beats nearest in 74.4% of evaluated cases | Strong, with wording correction required |
| Python quality | 206 tests passing; 74.90% measured coverage; Ruff and Black clean at last verified checkpoint | Passing |
| Frontend logic | 52 TypeScript tests passing, including Python/TypeScript ranking parity | Passing but too narrow |
| Frontend build | Next.js static export builds all seven generated routes | Passing |
| Dependency audit | Three high-severity production dependency findings in the current `web` lockfile | Failing release gate |
| Next.js UX | Functional but scheduled for full replacement | Not final |
| Streamlit UX | Functional but scheduled for full replacement | Not final |
| Deployment | Final Next.js deployment and post-redesign Streamlit verification are not complete | Not final |
| Git state | `main` is one local commit ahead of `origin/main`; frontend work is intentionally uncommitted | Needs reconciliation |

These results are a point-in-time baseline. Every gate must be rerun after the redesign and dependency migration.

## 3. Release Blockers

### P0-01 — Reconcile the frontend working tree

The existing `web/` changes must be reviewed before the replacement begins. Preserve useful data-contract and parity work; replace presentation code under the new system. Do not blindly commit the current frontend or discard it wholesale.

Exit evidence:

- a dedicated finish branch with an explicit, project-appropriate name;
- an inventory of retained versus replaced frontend files;
- no unrelated changes mixed into redesign commits;
- clean status at final release.

### P0-02 — Align the public decision claim with the calculation

The current public uncertainty penalty is constant across candidates because the same global interval width is used. It therefore does not change rank order. Calling the result `risk-adjusted` overstates the behavior.

Required decision for the resume-ready release:

- rank by `transport-adjusted net expected price`;
- show forecast uncertainty separately as decision evidence;
- update Python names where necessary, TypeScript names, export schema, UI copy, API documentation, tests, and reports so the contract is consistent.

Candidate-specific uncertainty may be researched later, but it is not required to ship a strong project.

Exit evidence:

- no public `risk-adjusted recommendation` wording;
- identical ranking for fixed Python and TypeScript fixtures;
- methodology states exactly what does and does not affect rank;
- no unsupported financial-outcome language.

### P0-03 — Resolve production dependency findings

The current `npm audit --omit=dev` reports three high-severity findings involving the installed Next.js dependency chain, Nano ID, and PostCSS. The audit's automatic force path proposes a major Next.js upgrade, so this is a controlled migration rather than an automatic lockfile rewrite.

Exit evidence:

- supported framework and dependency versions selected intentionally;
- migration notes for breaking changes;
- `npm audit --omit=dev` reports no unresolved high or critical findings, or a documented, time-bounded exception with demonstrated non-applicability;
- tests and static export pass on the upgraded stack.

### P0-04 — Replace the Next.js interface

Rebuild the Next.js experience from the information architecture and design system in `docs/DESIGN.md` and `docs/APP_FLOW.md`.

Required scope:

- global shell and responsive navigation;
- overview/method page;
- decision workbench;
- forecast exploration;
- coverage/provenance;
- all data and error states;
- accessible keyboard and focus behavior;
- shareable decision state where technically appropriate;
- static-export compatibility.

Exit evidence:

- no legacy presentation components remain without deliberate approval;
- all four routes meet their page contracts;
- screenshots pass desktop and mobile visual review;
- no horizontal scrolling at 320 px;
- production build succeeds.

### P0-05 — Replace the Streamlit interface

Rebuild Streamlit with the same product contract and visual language while respecting Streamlit's rendering model.

Required scope:

- shared navigation labels and product copy;
- page-level layout helpers and design tokens;
- data coverage, forecast, and recommendation flows;
- equivalent validation, missing-artifact, and stale-data states;
- same units, rounding, defaults, and candidate order as Next.js.

Exit evidence:

- all pages run from the documented command with sample artifacts and no secret;
- primary flow works at laptop and narrow widths;
- parity fixtures match Next.js and Python;
- no injected styling hides required focus, labels, errors, or native controls.

### P0-06 — Expand frontend verification

The current TypeScript suite proves calculation parity but does not prove the application experience.

Required additions:

- unit tests for formatting, validation, schema handling, and query-state helpers;
- component or integration tests for all primary data states;
- browser tests for route navigation, recommendation inputs/results, mandi selection, and narrow-screen navigation;
- automated accessibility checks on every route;
- visual snapshots or a documented screenshot set for desktop and mobile;
- performance verification on the production export.

Exit evidence:

- tests fail on an intentional contract break and pass after restoration;
- zero serious or critical automated accessibility violations;
- no uncaught console errors on primary browser flows;
- performance budgets in `docs/portfolio/RELEASE_GATES.md` pass.

### P0-07 — Make documentation internally consistent

Several older planning documents describe Streamlit, tests, and model persistence as absent even though they now exist. Public documentation must describe the repository as it is, not its earlier plan.

Required updates:

- README setup, architecture, screenshots, and deployed URLs;
- PRD and architecture wording where it contradicts shipped scope;
- API and export schema documentation after the ranking rename;
- tracker, current-state, and release instructions;
- portfolio metrics tied to reports and test output;
- historical blueprint clearly labeled historical or archived.

Exit evidence:

- repository-wide search finds no contradictory scope claims;
- a fresh clone can install, test, build, and run from README alone;
- every resume metric has a committed evidence source.

### P0-08 — Complete public release evidence

The project is resume-ready only after the final revision is independently observable.

Required work:

- push the finished branch and merge through a green CI run;
- deploy the Next.js static product;
- redeploy and verify Streamlit after its redesign;
- verify all public links in a signed-out browser;
- capture final screenshots and a concise demonstration path;
- record the release commit and verification date.

Exit evidence:

- public URLs load without authentication;
- primary flows work from a clean browser session;
- CI is green on the release commit;
- README points to the verified URLs and screenshots;
- the repository has no generated clutter or uncommitted release changes.

## 4. Important, Non-Blocking Finish Work

These items improve maintainability but do not justify delaying the portfolio release if all P0 gates pass:

| ID | Item | Why it helps |
|---|---|---|
| P1-01 | Add a repository license after choosing the intended reuse terms | Removes ambiguity for public portfolio use |
| P1-02 | Add lightweight analytics without raw location or quantity capture | Shows which routes and actions are actually used |
| P1-03 | Add automated screenshot comparison after the first stable visual baseline | Protects the redesigned interface from regression |
| P1-04 | Add candidate-specific uncertainty only after a sound validation study | Makes uncertainty capable of changing ranking honestly |
| P1-05 | Publish a short technical case study | Helps interviewers understand decisions without reading the full repository |

## 5. Explicitly Deferred

Do not expand into these areas before the portfolio release:

- additional crops, states, or horizons;
- live price ingestion or production scheduling;
- trade execution, bookings, payments, or logistics quotations;
- complex deep-learning models merely to increase model complexity;
- Kubernetes, a broad microservice split, or production monitoring infrastructure;
- causal price claims;
- route-accurate travel or carrier pricing without a validated provider;
- a generic admin dashboard, account system, or notification center.

These additions increase surface area without improving the central interview story: rigorous temporal modeling connected to a transparent, transport-aware market decision.

## 6. Dependency Order

```text
P0-01 working-tree safety
  -> P0-02 product/calculation truth
  -> P0-03 dependency migration
  -> P0-04 shared Next.js foundations
       -> P0-05 Streamlit translation
       -> P0-06 cross-surface verification
  -> P0-07 documentation consistency
  -> P0-08 public release evidence
```

Some work can overlap after P0-02, but product naming and schema decisions must precede component implementation and screenshots.

## 7. Definition of Finished

MandiPulse is fully finished for resume use only when:

- [ ] every P0 gate in `docs/portfolio/RELEASE_GATES.md` passes;
- [ ] the public calculation and language are aligned;
- [ ] both interfaces follow `docs/DESIGN.md` and `docs/APP_FLOW.md`;
- [ ] production dependencies have no unresolved high or critical audit finding;
- [ ] Python, TypeScript, browser, parity, accessibility, and build checks pass;
- [ ] CI is green on the exact public release commit;
- [ ] Next.js and Streamlit public URLs are verified after deployment;
- [ ] README claims, screenshots, metrics, and commands match that commit;
- [ ] the worktree is clean and the release is tagged or otherwise recorded.

Until then, describe the project as feature-complete in its analytical core and in final product hardening—not as fully shipped.
