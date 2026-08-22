# MandiPulse Current State

Status: active portfolio snapshot

Snapshot date: 2026-08-22

## 1. Summary

MandiPulse has a strong, tested analytical core and functioning Python, API, Streamlit, and Next.js surfaces. It is not yet the final portfolio release. The active phase is end-to-end product hardening: correct public ranking terminology, replace both interfaces, resolve frontend dependency findings, expand product-level tests, reconcile documentation, and verify public deployments.

## 2. Repository Snapshot

| Field | Value |
|---|---|
| Branch | `main` |
| Local HEAD | `df32e89` |
| Remote relationship | One local commit ahead of `origin/main` at snapshot time |
| Worktree | Existing `web/` changes are modified/untracked and intentionally not committed; final-planning documents are also being updated |
| Data snapshot | 2025-10-30 |
| Product scope | Onion, Maharashtra, 15 mandis, 7-day horizon |
| Active implementation phase | F0 — safe baseline and frontend inventory |
| Last approved analytical checkpoint | CP-003 |
| Next release checkpoint | Pending |
| Next action | Classify existing `web/` work, then execute F1 calculation-contract alignment before visual implementation |

## 3. Verified Baseline

### Analytical and Python layer

- 206 Python tests passed at the last full gate.
- Measured Python coverage was 74.90%, above the configured 70% floor.
- Ruff and Black passed.
- Strict web-export validation passed for the committed data contract.
- The clean panel contains 31,950 rows across 15 selected mandis.
- The shipped moving-average forecast policy records held-out test MAE of 139.57 INR/quintal.
- The Phase 3 observed-target holdout contains 792 rows with MAE 133.61.
- Phase 3 interval results record 86.87% conditional-residual coverage and 90.91% split-conformal coverage.
- Recommendation evaluation records mean regret@1 of 296.3 versus 370.1 for nearest-mandi and beats nearest in 74.4% of evaluated cases.

### Frontend layer

- 52 TypeScript logic/parity assertions passed on 2026-08-22.
- The current Next.js project compiled, type-checked, and generated its seven static routes.
- The production dependency audit reported three high-severity findings in the current dependency tree.
- No component-state, browser-flow, route-level accessibility, or production performance suite has been accepted yet.
- The current Next.js and Streamlit interfaces are functional but explicitly scheduled for complete UI/UX replacement.

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
| P0 | Existing frontend work is uncommitted | Preserve and classify it before replacement |
| P0 | Public ranking vocabulary overstates uncertainty behavior | Complete F1 contract alignment across all surfaces |
| P0 | Three high-severity production dependency findings | Controlled supported-version migration and clean audit |
| P0 | Both interfaces are explicitly non-final | Complete F3-F5 under the locked design and flow contracts |
| P0 | Frontend verification is logic-heavy and experience-light | Add component, browser, accessibility, responsive, and performance gates |
| P0 | Active and historical docs contradict current repository state | Reconcile public docs before release |
| P0 | Final public URLs and CI evidence do not exist | Deploy, verify signed out, and record the exact release commit |

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
