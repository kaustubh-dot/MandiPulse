# MandiPulse Current State

Status: active portfolio snapshot

Snapshot date: 2026-08-22

## 1. Summary

MandiPulse has a strong, tested analytical core and functioning Python, API, Streamlit, and Next.js surfaces. It is not yet the final portfolio release. The active phase is end-to-end product hardening: correct public ranking terminology, replace both interfaces, resolve frontend dependency findings, expand product-level tests, reconcile documentation, and verify public deployments.

## 2. Repository Snapshot

| Field | Value |
|---|---|
| Branch | `finish/portfolio-release` (created from `main` at `ef4f393`) |
| Local HEAD | See git log; `main` remains ahead of `origin/main` |
| Remote relationship | Finish branch is local-only until release gates pass |
| Worktree | Inherited `web/` changes classified (see F0 classification below) and committed as the F0 baseline; regenerated export artifacts committed with them |
| Data snapshot | 2025-10-30 |
| Product scope | Onion, Maharashtra, 15 mandis, 7-day horizon |
| Active implementation phase | F8 — documentation and release |
| Last approved analytical checkpoint | CP-003 |
| Next release checkpoint | Pending public deployment verification (RG-16) |
| Next action | Deploy both surfaces from `finish/portfolio-release`, verify signed-out at desktop and mobile sizes, record URLs in the release record, tag the release commit |

### F8 progress (2026-08-24)

Documentation was reconciled with shipped scope and independently audited (four defects
found and fixed: stale test counts in PRODUCT.md, a stale README cross-reference, a
dropped fetch-step command, and the deployment branch pointer). The release branch is
pushed with required CI green on the exact commits. A full release-gate audit against
`RELEASE_GATES.md` found and fixed three evidence defects before flipping RG-01–RG-10 to
Pass: committed Phase 3 reports leaked local absolute paths (the generator now emits
repo-relative provenance paths and the reports were regenerated through it), no test
exercised the API internal-error envelope (added), and cross-surface parity had only two
committed scenarios (a third fixed far-haul scenario, Nagpur 60 qtl, now has a shared
golden fixture asserted by both the Python smoke suite and a TypeScript unit test).
Gates: pytest 233 passed (77.85% coverage), web unit 137, components 34, e2e 17 passed,
ruff/black clean. Remaining for release: deploy both surfaces, verify signed out,
record URLs, tag.

### F7 outcome (2026-08-23)

Both review passes are complete and the deferred accessibility debts are cleared. The
four WCAG-AA token contrast failures were fixed at the token source — light-theme
success, warning, and info darkened minimally in OKLCH space (hue and chroma
preserved) until every pair clears 4.6:1 against paper, paper-2, and surface — and
synchronized across `web/src/app/globals.css`, the canonical `docs/DESIGN.md` block,
`src/mandipulse/app/design.py`, and `.streamlit/config.toml`; the e2e axe allowlist
is now empty and stays green. Refinement fixes from the visual pass: the overview
input-summary panel gained an explicit grid span (its labels were clipped), and the
Decision workbench hints no longer render literal `\u2212` escape text (JSX attributes
do not process JS escapes; real U+2212 characters are used). `formatDateIso` now
rejects impossible day-month combinations. Performance: the forecast chart is
lazy-loaded via `next/dynamic` (matching the existing map pattern), lifting
`/forecast/` from Lighthouse 86 to a 93 median. Final desktop-profile medians
(Lighthouse 13.4.1, Chrome headless, http-server on the static export, 3 runs/route):
performance 98/94/93/94, accessibility 100 on all routes, LCP 1.12-1.64 s,
CLS 0.019-0.043, TBT 0-96 ms. Verification sweep: 4 routes x 7 widths (320-1920) x
2 themes with zero horizontal overflow; keyboard pass (skip link, visible focus rings
on every tab stop, Escape restoring focus from the mobile sheet); reduced-motion
collapses transitions (0.22 s -> 0.12 s); 200% zoom equivalence clean; Streamlit
swept at 768/1024/1440 with zero non-benign console errors. Reference screenshots
frozen in `web/public/screenshots/` (decision, forecast, coverage, dark overview,
mobile sheet). Gates: pytest 230 passed, web unit 113, components 34, e2e 17 passed.

### F6 outcome (2026-08-23)

Release-grade automated verification now covers every layer. Web unit tests (113
node:test assertions via tsx) lock formatters, decision URL-state encode/decode
round-trips, validation matrices, schema guards, and date/rounding edge cases.
Component/integration tests (34 jsdom suites) cover the shell, controls, tables,
charts, and every data state — loading, error/retry, empty, missing-artifact with
recovery, partial/imputed, stale exclusion, and invalid-input preservation. Playwright
end-to-end specs run Chromium at 1440×900 and 390×844 against the production static
export: all routes hydrate with zero console errors, the primary decision flow re-ranks
on a mandi change, serializes to `?lat&lon&q&r&rad`, restores identically after reload,
copies a reproducible link, the mobile sheet behaves as an accessible dialog, and axe
(wcag2a/2aa/21a/21aa) reports no critical or serious violations outside four explicit,
pair-keyed semantic-token contrast allowances recorded for F7 refinement. Streamlit is
verified by nine pytest smoke tests that launch the real app on an ephemeral port,
poll health, execute each page module in-process under bare mode against committed
artifacts, and assert the Pune(Pimpri) golden parity fixture. CI runs lint, typecheck,
parity, component tests, static build, and the browser/accessibility suite with no
private secrets. Gate evidence: full suite green twice from clean processes
(pytest 230 passed, 77.85% coverage; web unit 113, components 34, e2e 17 passed /
3 viewport-scoped skips); an intentional golden-fixture mutation was detected as a
failure and restored. Known observations deferred to F7: four WCAG-AA token contrast
debts in `web/src/components/ui/primitives.tsx` (4.15–3.33 ratios), an AppShell
trailing-slash `aria-current` defect found by e2e and fixed during this phase, and two
minor display-edge findings (`formatDateIso` accepts impossible day-month pairs;
radius-exclusion caption counts only as-of-eligible rows).

### F5 outcome (2026-08-23)

The Streamlit experience was fully rebuilt under the Market Atlas system. The shell
(`app/streamlit_app.py`) and renamed pages (`app/pages/1_Decision.py`, `2_Forecast.py`,
`3_Coverage.py`) match the Next.js contract for navigation names, page order, snapshot
label, units, defaults, and copy. Every page consumes `src/mandipulse/app/design.py`
tokens, formatters, and the Plotly theme, and ranks through the shared Python ranking
implementation via `data_access.py` — no calculation logic is duplicated in page code.
The Decision workbench places inputs beside results on wide screens and in reading order
on narrow screens; missing-artifact states name the absent file instead of rendering
zeros, invalid inputs preserve entered values, and stale mandis warn while staying
visible. In-browser verification from committed sample artifacts (no API key): every
page loads, the map renders via WebGL tiles with the rank-1 dominant marker, the chart
legend keeps the multi-signal distinction (Prediction interval / Observed / Imputed
observation / 7-day forecast) with a data-driven interval label and conformal wording,
coverage shows the full mandi range with definitions and a focus view, and the Pune
parity fixture reproduces exactly (1,393 − 61 = 1,332 INR/qtl net re-rank). Console
output contains only two documented benign classes: Streamlit direct-load health 404s
and Plotly SVG-fallback noise. Gates: pytest 221 passed (75.89% coverage),
ruff/black clean, keyboard and narrow-screen smoke review accepted.

### F4 outcome (2026-08-23)

All four Next.js routes were rebuilt under the Market Atlas system on top of
`web/src/components/ui/primitives.tsx`. The overview route (`/`) is now a
decision-first technical overview: thesis, live decision preview at artifact
defaults (input summary, dominant recommendation, two alternatives), evaluation
facts traced to committed artifacts (shipped moving-average policy and MAE,
unshipped model comparison, interval level vs observed coverage, regret@1 vs
nearest-mandi), a four-step ranking pipeline, and an anchored method section
(`#method`) disclosing scope, temporal evaluation, uncertainty policy, and
explicit non-goals. The workbench serializes all five decision inputs to URL
query parameters with per-field validation that preserves entered values;
forecast separates observed/imputed/forecast values by label, stroke, marker,
and color; coverage compares mandis without a KPI wall and names missing
artifacts instead of rendering zeros. Cross-route `/​#method` links scroll
correctly after the async bundle commits. Corrective fixes during verification:
a duplicated percent in the interval label (`90%%` → `90%`). Gates:
lint/typecheck clean, npm test 52/52, production static export 7/7 routes;
in-browser verification from the export server: zero console errors across all
routes and full navigation, no horizontal overflow at 320/768/1024/1440/1920 px,
dark toggle persists, mobile sheet opens as an accessible dialog with Escape
restoring focus, and a Pune location change re-ranks with URL state serialized.

### F3 outcome (2026-08-23)

The Market Atlas Workbench foundations shipped on both surfaces. Next.js carries the full
light+dark OKLCH token set through Tailwind v4 `@theme inline` (semantic tokens only),
the three brand fonts via `next/font`, the desktop decision rail with mobile top bar and
navigation sheet (Escape closes, focus restores), a no-flash theme initializer with an
accessible toggle, and numeric formatters mirroring the Python module. Streamlit gained
`src/mandipulse/app/design.py` as its single presentation source (tokens with documented
hex approximations, formatters, Plotly theme, one scoped CSS injection) plus a token-derived
`.streamlit/config.toml`. A static-export RSC path mismatch (vercel/next.js#85374) is worked
around by a documented build adapter until the upstream fix ships. In-browser verification
from the production export: zero console errors across all routes and full navigation,
no horizontal overflow at 320/768/1024/1440/1920 px, dark theme persists via the toggle,
and the mobile sheet behaves as an accessible dialog. Gates: pytest 221 passed
(76.35% coverage), ruff/black clean, npm test 52/52, lint/typecheck/build clean.

### F2 outcome (2026-08-22)

Migrated to supported dependencies: Next.js 16.3 with Turbopack builds and the static export
retained (`trailingSlash: true`, unoptimized images), React 19, react-leaflet 5,
Tailwind v4 via `@tailwindcss/postcss` (legacy config deleted; `shadow-sm` -> `shadow-xs`),
TypeScript ~6.0.3, and ESLint 9 flat config using native `eslint-config-next` exports.
New `lint`/`typecheck` scripts run in CI alongside tests and build on Node 24
(`web/.nvmrc` = 24). Production audit now reports zero vulnerabilities (baseline: three high).
React-hooks lint findings were fixed properly: artifact ranking config is adopted during
render once per bundle, and retry loading is event-driven. All gates green post-migration:
lint/typecheck clean, npm test 52/52, production static export built and smoke-served.

### F1 outcome (2026-08-22)

The public ranking contract is now transport-adjusted: `transport_adjusted_net_price_inr_qtl`
numerically equals `expected_net_price_inr_qtl`; ranking sorts by expected net price
descending with a deterministic market-id tie-break; `uncertainty_penalty_inr_qtl` remains as
evidence-only because the global interval width is identical across candidates. Export bundle
and JSON schemas bumped to v2.0.0 (schemas moved to `schemas/web_export/v2/`). Regenerated
artifacts committed. Gates rerun on this branch: pytest 207 passed (74.90% coverage),
ruff/black clean, export validation 8/8, npm test 52/52 passing against the new bundle,
production build clean, and a repo-wide wording sweep leaves only rule/gate definitions and
visibly qualified historical annotations.

### F0 incident record: locked artifact ACLs (2026-08-22)

All 7 tracked JSON artifacts plus an untracked `manifest.json` under `web/public/data/`
had been rewritten by a sandbox process with restrictive ACLs that denied this account
read access. Resolution, without elevation:

1. The directory was renamed aside and a clean one created in its place.
2. Tracked artifacts were restored from git HEAD via `git checkout HEAD -- web/public/data`.
3. Regeneration (`python scripts/build_web_export.py`) replaced all 8 files from committed
   sample inputs; `scripts/validate_web_export.py` passed 8/8 including manifest hash checks.
4. The unreadable sandbox copies are quarantined untracked at `.tmp/data_locked_acl_quarantine/`
   for optional elevated cleanup later; nothing references them.

Root cause of the earlier web test failure: the committed generator had evolved past the
committed artifacts (meta gained `snapshot_date`, `candidate_policy`, `ranking.max_alternatives`;
recommendations capped by `max_alternatives`). Regeneration re-aligned data with code.

### F0 classification of inherited `web/` changes

| Class | Files | Disposition |
|---|---|---|
| Retain (contracts, logic, tests) | `src/lib/types.ts`, `src/lib/policy.ts`, `src/lib/useAsyncData.ts`, `test/transport.parity.test.ts` | Kept as the target artifact contract; field rename lands here in F1 |
| Retain then adapt in F1 | `src/lib/transport.ts`, `src/lib/data.ts` | Calculation/loading behavior kept; ranking field renamed with the bundle |
| Adapt (behavior kept, presentation replaced in F3-F5) | `DataState.tsx`, `RecommendationControls.tsx`, `TopRecommendations.tsx`, `ForecastChart.tsx`, `HonestResultsTable.tsx`, `BacktestSummary.tsx`, `RecommendTable.tsx`, page data-loading patterns in all four routes | Reused inside the new shell |
| Replace | `NavBar.tsx`, `SampleBanner.tsx`, `MandiMap.tsx`, `globals.css` theme | Rail/sheet shell, snapshot notice, map markers, and Market Atlas tokens replace them |
| Generated evidence | `public/screenshots/recommendation-flow.svg` | Committed as inherited evidence; reviewed again during F7 freeze |
| Regenerated | `public/data/*.json` + `manifest.json` | Restored from HEAD, then rebuilt by `build_web_export.py` to realign with the evolved generator |

## 3. Verified Baseline

### Analytical and Python layer (rerun on `finish/portfolio-release`, 2026-08-22)

- 206 Python tests passed (`pytest -q`), coverage 74.90% against the 70% floor.
- Ruff and Black passed (`ruff check`, `black --check`; 70 files unchanged).
- Strict web-export validation passed 8/8 after regeneration, including manifest artifact,
   input, code, and config hash verification.
- Unchanged analytical facts from CP-003: 31,950-row clean panel across 15 mandis; shipped
   moving-average policy held-out test MAE 139.57 INR/quintal; Phase 3 observed-target holdout
   792 rows at MAE 133.61 with 86.87% conditional-residual / 90.91% split-conformal coverage;
   recommendation mean regret@1 296.3 vs 370.1 nearest-mandi (74.4% win rate).

### Frontend layer (rerun on `finish/portfolio-release`, 2026-08-22)

- 52 TypeScript logic/parity assertions passed (`npm test`) after artifact realignment.
- Production build passed: Next.js 14.2.35, seven static routes prerendered
   (`/`, `/recommend`, `/forecast`, `/coverage` + not-found).
- The production dependency audit reports three high-severity findings in the current tree
   (Next.js 14.2.35 advisories plus bundled postcss); remediation is the F2 controlled
   migration to a supported Next.js major.
- No component-state, browser-flow, route-level accessibility, or production performance suite has been accepted yet.
- The current Next.js and Streamlit interfaces are functional but explicitly scheduled for complete UI/UX replacement.
- Baseline route screenshots for regression context only are stored outside version control
   at `.tmp/baseline-screenshots/` (four routes x 1440 px and 390 px, full page).

These are baseline results, not final-release evidence. They must be rerun on the exact release commit.

## 4. Product Truth Requiring Correction

The current public recommendation score applies a shared global interval width. Because that uncertainty term is constant across candidates, it does not change their order. The resume-ready product will therefore:

- rank mandis by transport-adjusted net expected price;
- display forecast uncertainty separately;
- remove unsupported public `risk-adjusted` ranking language;
- keep candidate-specific uncertainty as optional future research, not a release prerequisite.

Transport remains a scenario estimate based on haversine distance multiplied by 1.3 and a configurable rate currently represented as INR 4/km/quintal. It is not route navigation or a carrier quotation.

## 5. Active Design Decision

The locked direction is **Market Atlas Workbench**: a calm, exact decision tool combining field-atlas, surveyor, logistics, and calibration-sheet cues.

- Primary mode: operate first, read second.
- Tone: technical, grounded, and precise.
- Visual genre: modern minimal with a cool mineral base, deep blue-black structure, and signal-marigold emphasis.
- Type: Barlow Condensed for display, IBM Plex Sans for interface/body copy, and IBM Plex Mono for numbers and evidence.
- Structure: persistent decision rail, recommendation workbench, map and evidence views, and a readable long-form method page.
- Explicit removals: generic card grids, blue software-dashboard chrome, marketing hero composition, decorative farming imagery, glass effects, and constant entrance animation.

The complete contract is in `docs/DESIGN.md` and `docs/APP_FLOW.md`. No source interface code has been changed as part of the planning pass.

## 6. Active Blockers

| Priority | Blocker | Required resolution |
|---|---|---|
| P0 | Public ranking vocabulary overstates uncertainty behavior | RESOLVED in F1 — transport-adjusted contract shipped (v2.0.0 export) |
| P0 | Three high-severity production dependency findings | RESOLVED in F2 — zero audit findings on supported Next.js 16/React 19 |
| P0 | Both interfaces are explicitly non-final | RESOLVED in F4 (Next.js) and F5 (Streamlit) — both surfaces rebuilt under the locked design contracts |
| P0 | Frontend verification is logic-heavy and experience-light | RESOLVED in F6 — component, browser, accessibility, responsive, and Streamlit smoke gates are automated and pinned in CI |
| P0 | Active and historical docs contradict current repository state | Reconcile public docs before release |
| P0 | Final public URLs and CI evidence do not exist | Deploy, verify signed out, and record the exact release commit |

Resolved in F0: inherited `web/` work is classified (see F0 classification in section 2) and
committed; locked export artifacts were regenerated from committed inputs (incident record above).

## 7. Frozen Scope

The finish track does not include additional crops, states, horizons, live data ingestion, logistics quotations, trading, accounts, admin tools, microservices, Kubernetes, or more complex modeling without a demonstrated evaluation gain.

This protects the strongest interview narrative: a temporally evaluated forecast connected to a transparent, transport-aware market decision, supported by reproducible artifacts and consistent product surfaces.

## 8. Source of Truth

- Product: `PRODUCT.md`
- Design: `docs/DESIGN.md`
- Behavior: `docs/APP_FLOW.md`
- Remaining work: `docs/COMPLETION_ROADMAP.md`
- Execution sequence: `docs/IMPLEMENTATION_PLAN.md`
- Release acceptance: `docs/portfolio/RELEASE_GATES.md`
- Live checklist: `TODO.md`
- Historical evidence: `docs/portfolio/CHECKPOINTS.md`

Update this snapshot whenever a complete phase passes its gate. Do not mark the project fully finished until every release gate passes on the public release commit.
