# MandiPulse Final Implementation Plan

Status: approved execution sequence

Last reviewed: 2026-08-22

Inputs: `PRODUCT.md`, `docs/DESIGN.md`, `docs/APP_FLOW.md`, and `docs/COMPLETION_ROADMAP.md`

## 1. Objective

Finish MandiPulse as a defensible, public, resume-quality product without expanding its analytical scope. Preserve the working data, model, export, and cross-language calculation layers; replace the Next.js and Streamlit presentation layers; correct product wording; harden frontend dependencies and tests; then publish verifiable release evidence.

## 2. Operating Rules

1. Preserve existing uncommitted `web/` work until it has been classified as retain, adapt, or replace.
2. Make the public calculation contract correct before building final components around it.
3. Use `docs/DESIGN.md` as the visual source of truth and `docs/APP_FLOW.md` as the behavior source of truth.
4. Keep the two interfaces numerically and semantically aligned; pixel parity is not required.
5. Never change model policy, evaluation splits, or reported metrics as a side effect of interface work.
6. Keep all public surfaces clone-runnable from committed sample and export data without secrets.
7. End every phase at a green, reviewable checkpoint. Do not defer all verification to the end.
8. Limit visual review to two deliberate refinement passes after functional acceptance.

## 3. Phase Summary

| Phase | Outcome | Depends on |
|---|---|---|
| F0 | Safe baseline and retained-work inventory | None |
| F1 | Honest, single decision contract | F0 |
| F2 | Supported, audit-ready frontend foundation | F1 |
| F3 | Shared design foundations and application shells | F2 |
| F4 | Complete Next.js replacement | F3 |
| F5 | Complete Streamlit replacement | F3, stable F4 patterns |
| F6 | Cross-surface automated verification | F4, F5 |
| F7 | Visual, accessibility, and performance acceptance | F6 |
| F8 | Documentation, deployment, and release evidence | F7 |

## 4. F0 — Establish a Safe Baseline

### Tasks

- **F0-01:** Create a clearly named finish branch from the current `main` state.
- **F0-02:** Capture `git status`, local-versus-remote commit state, current checks, build output, and dependency audit in `docs/portfolio/CURRENT_STATE.md`.
- **F0-03:** Classify every changed or untracked file under `web/` as:
  - retain: data contracts, types, verified calculation logic, useful tests;
  - adapt: components whose behavior remains useful but whose presentation is replaced;
  - replace: page composition, generic shell, and legacy visual styling.
- **F0-04:** Capture reference screenshots of all current Next.js and Streamlit routes for regression context only. Do not use them as a visual target.
- **F0-05:** Confirm that committed sample data and web export artifacts are current and contain no secrets or local absolute paths.

### Gate F0

- working changes are understood and recoverable;
- baseline checks and screenshots are stored outside generated build folders;
- no user-owned work has been discarded;
- planned file ownership is clear before implementation starts.

### Suggested checkpoint

`chore: establish final product baseline`

## 5. F1 — Align Product Truth and Calculation Contract

### Decision

Ship a **transport-adjusted** ranking. Display uncertainty as separate evidence. Do not call the current public rank risk-adjusted while interval width is global and constant across candidates.

### Tasks

- **F1-01:** Trace the ranking field from `src/mandipulse/recommend/engine.py` through `scripts/build_web_export.py` and `web/src/lib/`.
- **F1-02:** Introduce or standardize a clear canonical field such as `transport_adjusted_net_price_inr_qtl`. If a field rename would break existing artifacts, provide a temporary explicit compatibility reader and remove it before final release.
- **F1-03:** Update Python and TypeScript ranking functions so names, comments, types, and outputs describe the implemented arithmetic.
- **F1-04:** Keep uncertainty fields in the artifact and result model, but treat them as evidence rather than a rank modifier.
- **F1-05:** Update export schema/version, reports, UI copy, and methodology wording.
- **F1-06:** Add regression fixtures proving candidate order, prices, distance, transport cost, and totals match across Python and TypeScript.
- **F1-07:** Regenerate the sample bundle and static web export; review the diff before accepting it.

### Gate F1

```powershell
ruff check app src scripts tests
black --check app src scripts tests
pytest -q
Set-Location web
npm.cmd test
```

Also require a repository-wide wording search with no unsupported public `risk-adjusted` claim.

### Suggested checkpoint

`fix: align recommendation contract with transport-adjusted ranking`

## 6. F2 — Upgrade and Secure the Frontend Foundation

### Tasks

- **F2-01:** Read the official migration notes for the selected supported Next.js and React versions. Record meaningful breaking changes in the implementation PR or tracker.
- **F2-02:** Upgrade production and development dependencies intentionally; do not use an unreviewed force-fix as the migration strategy.
- **F2-03:** Decide whether Tailwind remains useful for the replacement. If retained, upgrade and define tokens in one source. If removed, delete its configuration and dependencies completely.
- **F2-04:** Keep static export as a hard requirement unless a documented product need requires a server runtime.
- **F2-05:** Replace deprecated framework patterns, resolve type changes, and keep image/font behavior compatible with static hosting.
- **F2-06:** Run the production audit, unit tests, and static build after each dependency group rather than after one large upgrade.
- **F2-07:** Update `.github/workflows/ci.yml` if Node version, caching, or commands change.

### Gate F2

```powershell
Set-Location web
npm.cmd audit --omit=dev
npm.cmd test
npm.cmd run build
```

Required result: no unresolved high or critical production finding unless a written, expiry-dated exception proves that a finding cannot affect the static deployment.

### Suggested checkpoint

`build: migrate frontend to supported dependencies`

## 7. F3 — Build Shared Design Foundations

### Next.js targets

- `web/src/app/globals.css`: color, typography, spacing, focus, motion, and data-visualization tokens from `docs/DESIGN.md`.
- `web/src/app/layout.tsx`: fonts, metadata, skip link, root shell, and snapshot context.
- replace `web/src/components/NavBar.tsx` with the responsive application rail/sheet model.
- add a small set of primitives for controls, field messages, status, evidence blocks, tables, and page framing.
- retain Lucide or one equivalent icon family only; no mixed icon sources.

### Streamlit targets

- add a shared module under `src/mandipulse/app/` for page configuration, token values, formatters, and reusable evidence/status rendering;
- update `app/streamlit_app.py` to establish page title, navigation, snapshot context, and accessibility-conscious global styles;
- keep custom CSS narrow and documented; prefer semantic Streamlit components where they meet the design.

### Tasks

- **F3-01:** Implement light and dark tokens, with light as the initial release priority.
- **F3-02:** Add Barlow Condensed, IBM Plex Sans, and IBM Plex Mono with resilient fallbacks and controlled font loading.
- **F3-03:** Implement the desktop decision rail, mobile top bar, navigation sheet, main content measure, and evidence footer.
- **F3-04:** Implement form controls with labels, instructions, error text, disabled state, and visible keyboard focus.
- **F3-05:** Implement a single data-state contract for loading, empty, partial, stale, and error states.
- **F3-06:** Add numeric format helpers so INR/quintal, distance, dates, quantities, percentages, and intervals render consistently.
- **F3-07:** Verify the shell at 320, 768, 1024, 1440, and 1920 px before page work proceeds.

### Gate F3

- tokens, type scale, focus treatment, spacing, and shell match `docs/DESIGN.md`;
- shell contains no generic metric-card grid, decorative hero image, glass panel, or unsupported control;
- navigation is keyboard operable and does not trap focus;
- every primitive has default, hover, focus, disabled, and error behavior where applicable.

### Suggested checkpoint

`feat: establish MandiPulse application design system`

## 8. F4 — Replace the Next.js Experience

### F4-A Overview and Method — `web/src/app/page.tsx`

- present the product thesis and scope without a marketing-style hero;
- make `Compare mandis` the clear next action;
- show evaluation facts with split labels and evidence links;
- explain the data-to-decision pipeline and limitations;
- remove generic feature-card sections and promotional copy.

### F4-B Decision Workbench — `web/src/app/recommend/page.tsx`

- compose inputs and results according to `docs/APP_FLOW.md`;
- adapt or replace `RecommendationControls`, `TopRecommendations`, `RecommendTable`, and `MandiMap`;
- preserve inputs on validation and calculation errors;
- expose the active road factor and rate as assumptions;
- show recommendation arithmetic, alternatives, table, map, and uncertainty evidence;
- serialize stable decision state to query parameters without putting private data in analytics;
- provide a copy-link action with confirmation that does not interrupt keyboard flow.

### F4-C Forecast — `web/src/app/forecast/page.tsx`

- implement mandi selection with URL state;
- adapt or replace `ForecastChart` and `BacktestSummary`;
- separate observed, imputed, and forecast values by label, stroke, marker, and color;
- show interval method and coverage labels accurately;
- provide a direct path back to the decision flow.

### F4-D Coverage — `web/src/app/coverage/page.tsx`

- show snapshot range, selected mandis, row definitions, and per-mandi comparability;
- adapt or replace `HonestResultsTable` and `DataState`;
- make gaps and trainability legible without an ornamental KPI wall;
- name missing artifacts instead of substituting zero values.

### F4-E Responsive and data states

- verify all routes at the required viewport set;
- implement loading, stale, missing, partial, empty, and calculation-error examples;
- ensure tables have a deliberate narrow-screen strategy;
- disable nonessential motion under `prefers-reduced-motion`.

### Gate F4

```powershell
Set-Location web
npm.cmd test
npm.cmd run build
```

Manual acceptance:

- all route contracts pass;
- browser console is clean;
- no content is clipped or horizontally scrolls at 320 px;
- all claims can be traced to committed artifacts or reports;
- static export contains the expected routes and assets.

### Suggested checkpoints

- `feat: rebuild product overview and application shell`
- `feat: rebuild transport decision workbench`
- `feat: rebuild forecast and coverage evidence views`

## 9. F5 — Replace the Streamlit Experience

### Targets

- `app/streamlit_app.py`
- `app/pages/1_Data_Coverage.py`
- `app/pages/2_Forecast.py`
- `app/pages/3_Recommendation.py`
- shared helpers under `src/mandipulse/app/`

### Tasks

- **F5-01:** Match navigation names, page order, snapshot label, units, defaults, and copy to the Next.js contract.
- **F5-02:** Rebuild coverage as an evidence-led view with mandi focus and explicit row definitions.
- **F5-03:** Rebuild forecast with accurate history/forecast distinction and interval context.
- **F5-04:** Rebuild recommendation with inputs beside results on wide screens and in reading order on narrow screens.
- **F5-05:** Use the shared Python ranking implementation directly; do not duplicate calculation logic in page code.
- **F5-06:** Implement actionable missing-artifact and invalid-input states.
- **F5-07:** Check keyboard navigation, focus visibility, zoom, contrast, and Streamlit rerun behavior.

### Gate F5

```powershell
streamlit run app\streamlit_app.py
pytest -q
```

Manual acceptance requires every page to load from committed sample artifacts without an API key and to reproduce fixed parity fixtures.

### Suggested checkpoint

`feat: rebuild Streamlit decision experience`

## 10. F6 — Add Release-Grade Automated Verification

### Test layers

- **F6-01 Unit:** formatting, validation, query encoding/decoding, schema guards, rounding, and derived display values.
- **F6-02 Component/integration:** shell, navigation, controls, recommendation result, alternatives, tables, charts, and every data state.
- **F6-03 Browser:** open all routes; complete the primary decision flow; change mandi; navigate at desktop and mobile sizes; copy a reproducible link; verify no console error.
- **F6-04 Accessibility:** run Axe or an equivalent engine on every stable route and primary modal/sheet state.
- **F6-05 Contract:** regenerate web export and compare schema/version; run Python/TypeScript parity fixtures.
- **F6-06 Streamlit smoke:** start the application, verify health, load each page, and exercise a recommendation fixture.
- **F6-07 CI:** run all relevant checks in `.github/workflows/ci.yml` with deterministic versions and caching.

### Likely file additions

- `web/src/**/*.test.ts` or `*.test.tsx` beside tested modules;
- `web/e2e/` for browser flows;
- browser and accessibility configuration at `web/` root;
- a small Streamlit smoke script or test under `tests/`;
- stable fixtures shared through committed JSON where practical.

### Gate F6

- all Python and web tests pass twice from clean processes;
- the test suite detects an intentional parity mismatch;
- every route has an automated accessibility scan;
- primary browser flow passes at desktop and mobile viewports;
- no required check depends on a private secret.

### Suggested checkpoint

`test: cover final cross-surface product flows`

## 11. F7 — Visual, Accessibility, and Performance Acceptance

### Pass 1: structural review

- compare every route against `docs/DESIGN.md` and `docs/APP_FLOW.md`;
- correct hierarchy, information density, spacing, chart legibility, and narrow-screen order;
- verify all states rather than only the happy path;
- inspect Next.js and Streamlit side by side for semantic drift.

### Pass 2: refinement

- correct typography rhythm, optical alignment, focus styling, copy precision, and motion timing;
- remove any leftover generic component composition or decoration;
- freeze accepted reference screenshots.

### Required checks

- keyboard-only completion of primary flows;
- 200% zoom without lost content or controls;
- light and dark contrast where both themes ship;
- reduced-motion behavior;
- production Lighthouse or equivalent measurements;
- no layout shift from font or chart loading;
- no oversized decorative media in the initial viewport.

### Gate F7

Meet every threshold in `docs/portfolio/RELEASE_GATES.md`. Any exception must identify owner, reason, user impact, and expiry date.

### Suggested checkpoint

`fix: complete visual and accessibility acceptance`

## 12. F8 — Documentation, Deployment, and Release

### Documentation

- **F8-01:** Update README install, run, test, build, architecture summary, screenshots, limitations, and live URLs.
- **F8-02:** Reconcile `docs/PRD.md`, `docs/ARCHITECTURE.md`, `RELEASE.md`, and the historical blueprint with the final product scope.
- **F8-03:** Update export schema documents after the ranking-contract change.
- **F8-04:** Update `docs/TRACKER.md`, `TODO.md`, and `docs/portfolio/CURRENT_STATE.md` with final evidence.
- **F8-05:** Verify every resume metric against a committed report or reproducible command.

### Deployment

- **F8-06:** Push the finish branch and require green CI on the exact commit.
- **F8-07:** Deploy the Next.js static export with `web` as the project root or the documented equivalent.
- **F8-08:** Redeploy Streamlit and verify sample-artifact startup.
- **F8-09:** Test both public URLs signed out, at desktop and mobile sizes.
- **F8-10:** Capture final screenshots, release commit, verification date, and known limitations.
- **F8-11:** Merge, tag or record the release, and confirm a clean worktree.

### Gate F8

All rows in `docs/portfolio/RELEASE_GATES.md` are Pass, every public link resolves, CI is green, and the repository state matches the evidence shown publicly.

### Suggested checkpoints

- `docs: align portfolio evidence with final product`
- `release: publish MandiPulse portfolio build`

## 13. Final Command Matrix

Run commands from the repository root unless noted.

```powershell
# Python quality and behavioral checks
ruff check app src scripts tests
black --check app src scripts tests
pytest -q

# Regenerate committed demo and web contracts when source artifacts change
python scripts\build_demo_sample.py
python scripts\build_web_export.py

# Web quality and production export
Set-Location web
npm.cmd audit --omit=dev
npm.cmd test
npm.cmd run build

# Local analytical interface
Set-Location ..
streamlit run app\streamlit_app.py
```

Add browser, accessibility, and performance commands to this matrix once their tooling is selected in F6; then pin them in CI and README.

## 14. Commit Discipline

- one coherent concern per commit;
- regenerated artifacts committed with the source change that required them;
- no build output, environment files, raw data, local model stores, or test recordings unless explicitly designated as release evidence;
- no dependency lockfile change without its manifest change and passing audit/build evidence;
- no final squash that makes calculation corrections indistinguishable from visual replacement unless the project owner explicitly wants that history.
