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
| Active implementation phase | F5 — complete Streamlit replacement |
| Last approved analytical checkpoint | CP-003 |
| Next release checkpoint | Pending |
| Next action | Rebuild the Streamlit shell and three pages against `src/mandipulse/app/design.py`; then expand automated verification |

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
| P0 | Both interfaces are explicitly non-final | Next.js replacement RESOLVED in F4; complete F5 for Streamlit under the locked design contracts |
| P0 | Frontend verification is logic-heavy and experience-light | Add component, browser, accessibility, responsive, and performance gates |
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
