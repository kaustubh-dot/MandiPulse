# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

- Primary product surface: Next.js static export in `web/`.
- Secondary analytical surface: Streamlit in `app/`.
- Supporting interface: FastAPI snapshot service in `api/`.
- Shared computation: Python package under `src/mandipulse/` plus generated, schema-validated
  public artifacts.

## Users

- Small Maharashtra onion farmers comparing where to sell a crop lot.
- Farmer Producer Organizations comparing mandis for an aggregated sale.
- Market analysts inspecting coverage, forecasts, assumptions, and backtest evidence.
- Technical reviewers evaluating the project's data, ML, API, and product-engineering decisions.

The public interface must not assume that every user understands forecasting terminology. Technical
evidence should remain available without obstructing the primary sell-decision workflow.

## Product Purpose

MandiPulse helps a user compare selected Maharashtra onion mandis using a 7-day price forecast,
estimated transport cost, uncertainty evidence, and historical recommendation performance. Success
means a user can identify the best eligible mandi under stated assumptions, understand why it ranks
there, and recognize the limits of the result.

## Positioning

The product does not stop at crop-price prediction. It converts a point-in-time forecast into a
transport-aware sell decision and binds the displayed result to reproducible data, model,
configuration, and evaluation evidence.

## Operating Context

- The current public dataset is a frozen portfolio snapshot ending on 2025-10-30.
- The supported scope is Onion, Maharashtra, 15 mandis, and a 7-day forecast horizon.
- A user chooses a farmer location, quantity, transport rate, and maximum travel radius.
- The system filters candidates to the canonical forecast as-of date and configured policy bounds.
- The system estimates road distance as haversine distance multiplied by a configurable factor.
- Results are decision support, not live quotes, guaranteed prices, route plans, or profit promises.
- The repository must remain clone-runnable without a live data-service credential.

## Capabilities and Constraints

### Confirmed capabilities

- Leakage-aware daily panel construction and temporal evaluation.
- Baseline, LightGBM, and residual-model comparison with an honestly selected moving-average model.
- Forecast intervals with measured coverage and an observed-target Phase 3 evaluation.
- Transport-cost-aware candidate scoring and regret-at-K backtesting.
- Streamlit, FastAPI, and static Next.js surfaces over committed demonstration artifacts.
- Strict JSON schemas, finite-value validation, a provenance manifest, and Python/TypeScript parity.

### Release constraints

- The current global public interval width gives every eligible candidate the same uncertainty
  penalty in a snapshot. It does not change the ranking order. The finished product must describe
  the ranking as transport-adjusted net expected price unless a future, separately validated
  candidate-specific uncertainty method is promoted.
- The transport rate is a configurable scenario, not a carrier quote.
- The road-distance factor is an approximation, not route-engine output.
- The Next.js dependency tree has been migrated to supported versions (Next.js 16, React 19,
  Tailwind v4); the production audit reports zero unresolved findings.
- The rebuilt Next.js experience is committed on `finish/portfolio-release`. Release evidence must be
  rerun on the exact release commit.
- Streamlit remains a secondary technical-review surface. It must share product terminology and
  semantic tokens with Next.js, but it does not need pixel-identical composition.

## Brand Commitments

- Product name: MandiPulse India.
- Voice: direct, practical, evidence-led, calm, and explicit about assumptions.
- Avoid decorative agriculture imagery, rural stereotypes, financial-trading hype, and prediction
  certainty language.
- Never fabricate users, savings, deployment status, live freshness, testimonials, or commercial
  outcomes.

## Evidence on Hand

- 31,950-row clean panel across 15 mandis in the audited local dataset.
- Shipped 7-day moving-average forecast with 139.57 INR/qtl test MAE in the public v1 evidence.
- Phase 3 observed-target holdout: 792 eligible rows, 133.61 INR/qtl MAE, and 90.91% adopted
  split-conformal coverage for the internal evaluation population.
- Public recommendation backtest: mean regret@1 of 296.3 INR/qtl versus 370.1 INR/qtl for the
  nearest-mandi baseline; the recommendation beats nearest on 74.4% of evaluated dates.
- 230 passing Python tests with 77.85% coverage from the latest verification.
- 113 web unit assertions, 34 component suites, and 17 Playwright end-to-end checks
  (desktop and mobile, with automated accessibility scans) on the release branch.
- Eight strict web JSON artifacts with verified schema, finite-value, and manifest-hash checks.
- No verified production-user count, profit improvement, request volume, or public API deployment.

## Product Principles

1. Put the sell decision before model exposition.
2. Show assumptions beside derived values, not in distant documentation.
3. Prefer an honest baseline and clear limitation over a stronger-sounding unsupported claim.
4. Keep every public metric traceable to a generated artifact or test.
5. Make the primary workflow understandable without hiding the technical evidence reviewers need.

## Accessibility and Inclusion

- Target WCAG 2.2 AA for both public surfaces.
- Do not communicate risk, freshness, or selection using color alone.
- Maintain keyboard access, visible focus, semantic labels, text alternatives, and table fallbacks for
  visualizations.
- Use plain-language definitions for mandi, quintal, as-of date, interval, regret, and transport
  assumptions.
- Support 320, 375, 414, 768, 1024, and 1440 pixel viewport checks for the Next.js surface.

## Open Product Decisions

- Whether to deploy the optional FastAPI service publicly. The Next.js static product does not
  require it.
- Whether a later research phase should attempt candidate-specific uncertainty. This is not required
  for the portfolio release if the ranking language is corrected now.
- Whether to support Marathi localization after the English portfolio release. Localization is not
  part of the current finish scope.
