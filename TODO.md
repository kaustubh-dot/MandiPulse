# MandiPulse Active TODO

Last reviewed: 2026-08-22

The detailed execution sequence is in [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md). Release is governed by [docs/portfolio/RELEASE_GATES.md](docs/portfolio/RELEASE_GATES.md). Historical completed work remains in [docs/TRACKER.md](docs/TRACKER.md) and [docs/portfolio/CHECKPOINTS.md](docs/portfolio/CHECKPOINTS.md).

## F0 — Safe baseline

- [x] **F0-01:** Create the final finish branch.
- [x] **F0-02:** Classify every current `web/` change as retain, adapt, or replace.
- [x] **F0-03:** Capture baseline route screenshots and rerunnable verification output.
- [x] **F0-04:** Confirm committed sample/export artifacts contain no secrets or local paths.

## F1 — Product and calculation truth

- [x] **F1-01:** Replace public risk-adjusted wording with transport-adjusted ranking terminology.
- [x] **F1-02:** Standardize the ranking field across Python, API, export, TypeScript, tests, reports, and copy.
- [x] **F1-03:** Keep uncertainty visible as evidence but separate from the current rank.
- [x] **F1-04:** Regenerate sample and web export artifacts and approve the contract diff.
- [x] **F1-05:** Rerun Python and TypeScript parity gates.

## F2 — Dependency and security migration

- [x] **F2-01:** Select supported Next.js, React, and related dependency versions from official migration guidance.
- [x] **F2-02:** Complete the controlled migration and update CI runtime/configuration.
- [x] **F2-03:** Reach a clean high/critical production dependency audit.
- [x] **F2-04:** Pass web tests, type checking, and static export on the upgraded stack.

## F3 — Shared design foundations

- [x] **F3-01:** Implement the locked tokens, typography, layout, focus, and motion system.
- [x] **F3-02:** Build the Next.js application rail and mobile navigation sheet.
- [x] **F3-03:** Build reusable controls, evidence, data-state, table, and page-frame primitives.
- [x] **F3-04:** Add shared Streamlit presentation and formatting helpers.
- [x] **F3-05:** Accept the shell at 320, 768, 1024, 1440, and 1920 px.

## F4 — Next.js replacement

- [x] **F4-01:** Rebuild overview and method route.
- [x] **F4-02:** Rebuild the recommendation workbench and shareable decision state.
- [x] **F4-03:** Rebuild forecast exploration and chart semantics.
- [x] **F4-04:** Rebuild coverage and provenance view.
- [x] **F4-05:** Implement every loading, empty, missing, partial, stale, invalid, and error state.
- [x] **F4-06:** Pass responsive review and production static export.

## F5 — Streamlit replacement

- [ ] **F5-01:** Rebuild the global Streamlit shell and navigation.
- [ ] **F5-02:** Rebuild Coverage, Forecast, and Recommendation pages.
- [ ] **F5-03:** Match Next.js units, defaults, copy, states, and ranking semantics.
- [ ] **F5-04:** Pass laptop, narrow-screen, keyboard, and sample-artifact smoke review.

## F6 — Automated release verification

- [ ] **F6-01:** Add frontend unit tests for validation, formatting, schema, and URL state.
- [ ] **F6-02:** Add component/integration tests for primary UI and all data states.
- [ ] **F6-03:** Add desktop/mobile browser tests for every route and primary flow.
- [ ] **F6-04:** Add automated accessibility checks.
- [ ] **F6-05:** Add final cross-surface parity and Streamlit smoke checks.
- [ ] **F6-06:** Run all required checks in CI without private secrets.

## F7 — Acceptance

- [ ] **F7-01:** Complete structural visual review pass.
- [ ] **F7-02:** Complete refinement visual review pass and freeze reference screenshots.
- [ ] **F7-03:** Pass keyboard, focus, contrast, zoom, and reduced-motion checks.
- [ ] **F7-04:** Meet the documented production performance budgets.

## F8 — Documentation and release

- [ ] **F8-01:** Reconcile README, PRD, architecture, API, release, and historical plan wording.
- [ ] **F8-02:** Add final screenshots, evidence-backed metrics, limitations, and demo path.
- [ ] **F8-03:** Push and obtain green CI on the exact release commit.
- [ ] **F8-04:** Deploy and verify Next.js and Streamlit in signed-out browsers.
- [ ] **F8-05:** Record URLs, release commit, verification date, and final gate results.
- [ ] **F8-06:** Confirm clean worktree and mark the portfolio release complete.

## Not Required for This Release

- additional crops, states, and horizons;
- live data ingestion or trade execution;
- deeper models without a demonstrated evaluation gain;
- route-accurate logistics pricing without a validated provider;
- Kubernetes, microservices, accounts, admin panels, or notification systems.
