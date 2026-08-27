<!-- Hallmark · pre-emit critique: P5 H5 E5 S5 R5 V5 -->

# Quiet Exchange Interface Design

**Status:** Approved through the design-direction gallery on 2026-08-24.

**Audience:** Resume reviewers, interviewers, technical evaluators, farmers/FPO operators, and project maintainers.

**Primary job:** Let a reviewer or operator understand the transport-adjusted mandi recommendation, its assumptions, and its evidence without mistaking frozen demonstration data for a live trading product.

## Locked Direction

- **Streamlit:** Quiet Exchange.
- **Next.js:** Quiet Exchange, with functional maps but no decorative geographic layer.
- **Shared tone:** Minimal, professional, assured, evidence-led.
- **Motion:** Opacity, selection, and 1 px press feedback only. No GSAP, Three.js, parallax, ambient loops, or page-wide scroll reveals.
- **Data and behavior:** Preserve every current route, artifact loader, decision formula, URL parameter, state message, chart fallback, map fallback, and accessibility behavior.

The implementation must not copy the preview gallery's miniature markup into production. It must translate the approved visual DNA through the existing Next.js and Streamlit component boundaries.

## Design Thesis

Quiet Exchange treats the sell decision like a carefully edited exchange ledger: warm vellum, graphite text, oxblood emphasis, large editorial whitespace, and one dominant answer. It avoids both generic SaaS cards and financial-terminal theater.

Geography appears only where it carries decision evidence. Maps use neutral graphite markers, an oxblood rank-one marker, rectangular labels, OpenStreetMap attribution, and a tabular fallback. Decorative contours, route atmosphere, agricultural imagery, and theme-specific green accents are excluded.

## Canonical Light Tokens

These OKLCH values are the source of truth. Streamlit uses the listed sRGB approximations because its theme configuration does not consume OKLCH.

| Role | OKLCH | Streamlit hex | Usage |
|---|---|---|---|
| Paper | `oklch(96% 0.012 75)` | `#f7f1e9` | Page canvas |
| Paper 2 | `oklch(92% 0.016 75)` | `#ebe3d9` | Sidebar and quiet bands |
| Surface | `oklch(98% 0.008 75)` | `#fcf8f3` | Inputs and data regions |
| Surface raised | `oklch(99% 0.006 75)` | `#fefbf7` | Popovers and tooltips only |
| Ink | `oklch(20% 0.012 55)` | `#1a1511` | Primary text |
| Ink 2 | `oklch(38% 0.012 55)` | `#48413c` | Secondary text |
| Muted | `oklch(45% 0.012 55)` | `#5b544f` | Supporting labels |
| Rule | `oklch(82% 0.012 70)` | `#c9c3bc` | Dividers |
| Rule strong | `oklch(68% 0.018 70)` | `#a0978d` | Input and table boundaries |
| Accent | `oklch(38% 0.13 18)` | `#781827` | Oxblood action and selection |
| Accent soft | `oklch(91% 0.03 18)` | `#f5dada` | Selected row or forecast band |
| Accent ink | `oklch(96% 0.012 75)` | `#f7f1e9` | Text on oxblood |
| Focus | `oklch(48% 0.15 18)` | `#a12e3c` | Immediate focus ring |
| Success | `oklch(45% 0.13 145)` | `#146720` | Verified success state |
| Warning | `oklch(48% 0.13 70)` | `#8a4c00` | Verified warning state |
| Danger | `oklch(48% 0.15 18)` | `#a12e3c` | Error state |
| Info | `oklch(45% 0.06 235)` | `#315b72` | Neutral information state |

Both surfaces remain vellum, graphite, and oxblood. State colors are reserved for semantic feedback.

## Next.js Dark Tokens

The existing theme toggle remains. Its dark mode becomes warm charcoal rather than blue-black.

| Role | OKLCH | sRGB approximation |
|---|---|---|
| Paper | `oklch(16% 0.012 55)` | `#110c08` |
| Paper 2 | `oklch(20% 0.014 55)` | `#1b1410` |
| Surface | `oklch(24% 0.012 55)` | `#241e1a` |
| Surface raised | `oklch(28% 0.014 55)` | `#2f2722` |
| Ink | `oklch(94% 0.012 75)` | `#f0eae3` |
| Ink 2 | `oklch(78% 0.012 75)` | `#bcb6af` |
| Muted | `oklch(68% 0.014 55)` | `#9f9690` |
| Rule | `oklch(34% 0.018 55)` | `#40362f` |
| Rule strong | `oklch(48% 0.02 55)` | `#675b53` |
| Accent | `oklch(72% 0.12 18)` | `#e68488` |
| Accent soft | `oklch(28% 0.05 18)` | `#3a1c20` |
| Accent ink | `oklch(16% 0.012 55)` | `#110c08` |
| Focus | `oklch(72% 0.14 18)` | `#ef7d83` |
| Success | `oklch(70% 0.1 145)` | `#76af77` |
| Warning | `oklch(76% 0.11 70)` | `#dba25b` |
| Danger | `oklch(72% 0.14 18)` | `#ef7d83` |
| Info | `oklch(70% 0.07 235)` | `#7aa8bd` |

## Typography

Use exactly three roles:

| Role | Typeface | Weights | Usage |
|---|---|---|---|
| Display | Cormorant Garamond | 400, 600 | Wordmark, page title, recommendation name |
| Body | Manrope | 400, 600, 700 | Navigation, controls, prose, table labels |
| Numeric | IBM Plex Mono | 400, 600 | Prices, dates, units, ranks, coordinates |

Next.js loads all three through `next/font/google`. Streamlit declares the same preferred stacks with `Georgia`, `Segoe UI`, and `Cascadia Mono` fallbacks so the offline demonstration stays readable if the named web fonts are unavailable.

Rules:

- Headings remain roman; no italic display text.
- Page titles use sentence case and fit within two lines at 320 px.
- Body text is at least 16 px; supporting labels are at least 14 px.
- Numeric comparison uses tabular figures and right alignment.
- No more than five visible text sizes per page.

## Shape, Spacing, and Containment

- Keep the existing 4 px spacing scale.
- Controls may use a 3–6 px radius. Data panels and tables are square or nearly square.
- Prefer open sections with one top or bottom rule over bordered cards.
- Never nest a bordered panel inside another bordered panel.
- Preserve generous whitespace around the dominant recommendation; evidence may remain dense.
- Accent fill stays below roughly 5% of a viewport.

## Next.js Composition

### Shell

- Keep the persistent desktop rail and semantic mobile sheet.
- Make the rail visually quieter: vellum background, hairline right rule, editorial wordmark, four routes, snapshot, method disclosure, and theme toggle.
- Active navigation uses an oxblood rule and stronger ink, never a filled pill.
- Main content remains capped at 1440 px and uses open left/right margins.
- The mobile sheet must trap focus, close on Escape or navigation, restore focus, and prevent background scrolling.

### Overview `/`

1. Frozen snapshot line.
2. Quiet Exchange statement: one short page title and one explanatory paragraph.
3. One dominant recommendation with price and decision facts.
4. Two compact alternatives.
5. Evaluation and method evidence in open ruled sections.

This is an operating view, not a marketing hero.

### Decision `/recommend`

- Desktop: narrow controls column and wide result/evidence column.
- Mobile: controls, compare action, primary result, alternatives, table, map, evidence.
- The top recommendation uses editorial scale and open space instead of a thick left-striped card.
- The map uses square framing, neutral graphite candidate markers, an oxblood rank-one marker, and rectangular labels.
- Keep OpenStreetMap attribution and the tabular distance fallback.

### Forecast `/forecast`

- One chart remains the anchor.
- Observed history stays graphite; forecast stays dashed oxblood; uncertainty stays oxblood-soft.
- Keep chart/table toggle, tooltip semantics, units, legends, and data table fallback.

### Coverage `/coverage`

- Use ledger-like sections and aligned tables rather than metric-card grids.
- Provenance, missingness, and model evidence remain factual and visible.

## Geographic Evidence in Next.js

- The real Leaflet map is the only geographic visual.
- Use semantic tokens only; no inline raw colors or theme-specific green role.
- Candidate markers are neutral; the first-ranked mandi uses oxblood plus its text label.
- When map tiles fail, the bounded map region retains a quiet ruled fallback and an explicit status message.
- No decorative contour, route, crop, or agricultural illustration may sit behind page content.

## Streamlit Composition

Streamlit implements the same Quiet Exchange system.

- Keep the native sidebar and native navigation.
- Use one shared `mandipulse.app.design` module for tokens, Plotly defaults, shared CSS, and repeated heading/snapshot helpers.
- Landing page: one recommendation, two alternatives, one evaluation summary, one method disclosure.
- Decision page: controls column first, dominant result second, then eligible table, map, evidence, and regret evaluation.
- Forecast page: selector, mandi identity, one dominant forecast value, interval facts, chart, model evidence, data quality.
- Coverage page: snapshot range, comparable-mandi table, one focused-mandi chart, model evidence, provenance.
- Use `st.metric` only for the dominant recommendation or forecast and a small number of verified KPIs.
- Avoid injected card markup and brittle selectors. Scoped CSS may set typography, spacing, dividers, sidebar surface, metrics, inputs, and focus states.
- Streamlit defaults to the light Quiet Exchange theme.

## States and Accessibility

- WCAG 2.2 AA is the floor.
- Keep a skip link as the first focusable Next.js element.
- Keep heading order and landmarks valid on every route.
- Every interactive control implements default, hover, focus-visible, active, disabled, loading, error, and success.
- Focus rings appear immediately at 3:1 or better.
- Form errors use `aria-invalid` and `aria-describedby`.
- Dynamic recommendation changes use one restrained polite live region.
- Status, risk, freshness, selection, and chart series never rely on color alone.
- Charts and maps retain textual summaries and tabular fallbacks.
- Verify Next.js at 320, 375, 414, 768, 1024, and 1440 px.
- Verify Streamlit at 768, 1024, 1280, and 1440 px; narrow screens must remain usable even when not optimized.

## Performance and Scope

- Do not add a motion library, WebGL, video, or generated decorative imagery.
- Keep Leaflet and Recharts lazy or route-local where they already are.
- Preserve dimensions for charts and maps to avoid CLS.
- Do not change recommendation math, policy, artifacts, API contracts, route ownership, or product copy meaning.
- Do not delete production files during the redesign. The unused `NavBar.tsx` remains outside this plan. The user later explicitly approved removing Garden Atlas visuals, so the retired `ContourField.tsx` is the sole cleanup exception.

## Acceptance Criteria

- Both surfaces clearly read as the same Quiet Exchange product family.
- Next.js carries only functional geographic evidence; both surfaces otherwise share the same Quiet Exchange identity.
- One recommendation is visually dominant; alternatives remain comparable.
- Real frozen evidence is used throughout; no fabricated metric or live-data claim appears.
- No card-inside-card nesting, gradient text, glass, glows, generic hero, or three-equal-card result layout remains.
- Next.js unit, component, type, lint, build, axe, and Playwright flows pass.
- Streamlit design, data-access, module smoke, and server health tests pass.
- Browser review finds no overflow, clipped controls, two-line clickable labels, or unreadable contrast at the required widths.
