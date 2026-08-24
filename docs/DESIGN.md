<!-- Hallmark pre-emit critique: P5 H5 E5 S5 R5 V4 -->

# MandiPulse Design System

This is the locked visual and interaction specification for the Next.js and Streamlit redesign.
Every UI implementation must read this file before changing a page or component. Product truth lives
in [`PRODUCT.md`](../PRODUCT.md); this file controls presentation, hierarchy, interaction, and visual
consistency.

## Design Read

MandiPulse is an operating tool for a sell decision, with a secondary evidence-reading mode. It must
help a farmer or FPO compare eligible mandis quickly while giving a technical reviewer direct access
to assumptions, model performance, uncertainty, and provenance.

| Dimension | Locked direction |
|---|---|
| Product mode | Operate first, Read second |
| Genre | Modern-minimal technical product |
| Visual world | Market Atlas Workbench |
| Tone | Calm, exact, practical, evidence-led |
| Design variance | 6/10: structured asymmetry, no ornamental chaos |
| Motion intensity | 3/10: state feedback only |
| Visual density | 7/10: compact evidence with deliberate breathing room |
| Primary surface | Next.js static product |
| Secondary surface | Streamlit technical dashboard |

## Thesis

The interface should feel like a field atlas joined to an operations workbench: coordinates,
distances, prices, intervals, and provenance arranged for a real decision. It must not look like a
stock trading terminal, generic SaaS landing page, green agriculture portal, or chart gallery.

The first viewport must answer three questions:

1. What decision can I make here?
2. What is the current best eligible mandi under my assumptions?
3. How current and trustworthy is the evidence?

## Preserve and Replace

### Preserve

- Product name and domain terminology.
- Existing route purposes and working data behavior.
- Canonical as-of policy, input bounds, model metrics, and limitation copy.
- Table, chart, and map accessibility fallbacks.
- Loading, empty, error, stale, and retry behaviors already implemented.

### Replace

- Existing blue-gray Tailwind appearance and generic white cards.
- Stacked page titles followed by repeated bordered panels.
- Three-equal-card recommendation layout.
- Desktop navigation that becomes a horizontally scrolling row on mobile.
- Decorative badges, repeated uppercase labels, and redundant explanations.
- Any visual treatment that implies live data, guaranteed prices, or financial execution.

## Cross-Surface Architecture

Both interfaces share the same hierarchy and vocabulary, but not identical composition.

| Layer | Next.js | Streamlit |
|---|---|---|
| Navigation | Persistent desktop rail; compact mobile header and sheet | Native sidebar with the same labels and order |
| Primary action | Decision controls remain visible beside results | Controls stay near the top and may use sidebar support |
| Result hierarchy | One dominant recommendation, alternatives, then evidence | One dominant recommendation, alternatives, then evidence |
| Detailed evidence | Progressive disclosure and supporting routes | Expanders and dedicated pages |
| Visual system | Full token implementation | Theme config plus restrained, documented CSS |
| Responsive target | 320px through 1440px and wider | 768px through desktop; usable, not optimized, on narrow screens |

Page and navigation order is fixed:

1. Sell decision (`/` in Next.js, landing page in Streamlit)
2. Recommendations (`/recommend`)
3. Forecast (`/forecast`)
4. Data coverage (`/coverage`)

Do not add speculative modules to primary navigation.

## Visual World

The Market Atlas Workbench direction combines four functional references without copying their
decoration:

- Survey field book: coordinates, measurement, compact annotation, and traceable assumptions.
- Route atlas: spatial comparison and distance are part of the decision.
- Commodity bulletin: prices are aligned, dated, and treated as evidence.
- Calibration sheet: uncertainty and model performance are qualified, not celebrated.

The result is cool, light, precise, and materially flat. No glass, glows, fake browser frames,
farming clipart, stock photography, gradient headlines, or simulated trading screens.

## Canonical Tokens

All implementation colors must use semantic tokens. Do not add raw hex, RGB, HSL, or OKLCH values
inside components. Add a named token here first when the system genuinely needs one.

### Light theme

```css
:root {
  color-scheme: light;

  --color-paper: oklch(97.2% 0.008 235);
  --color-paper-2: oklch(94.5% 0.014 235);
  --color-surface: oklch(99% 0.006 235);
  --color-surface-raised: oklch(100% 0.004 235);
  --color-ink: oklch(21% 0.035 248);
  --color-ink-2: oklch(42% 0.035 248);
  --color-muted: oklch(52% 0.028 248);
  --color-rule: oklch(82% 0.018 240);
  --color-rule-strong: oklch(68% 0.025 245);

  --color-accent: oklch(69% 0.17 70);
  --color-accent-ink: oklch(21% 0.04 60);
  --color-focus: oklch(57% 0.19 255);

  --color-success: oklch(51% 0.14 150);
  --color-warning: oklch(53% 0.16 70);
  --color-danger: oklch(55% 0.19 28);
  --color-info: oklch(52.5% 0.15 250);
}
```

### Dark theme

```css
[data-theme="dark"] {
  color-scheme: dark;

  --color-paper: oklch(15% 0.018 248);
  --color-paper-2: oklch(18.5% 0.021 248);
  --color-surface: oklch(21.5% 0.023 248);
  --color-surface-raised: oklch(24.5% 0.025 248);
  --color-ink: oklch(94% 0.01 240);
  --color-ink-2: oklch(78% 0.018 240);
  --color-muted: oklch(68% 0.022 240);
  --color-rule: oklch(34% 0.025 245);
  --color-rule-strong: oklch(48% 0.03 245);

  --color-accent: oklch(76% 0.145 76);
  --color-accent-ink: oklch(18% 0.035 60);
  --color-focus: oklch(72% 0.15 250);

  --color-success: oklch(70% 0.13 150);
  --color-warning: oklch(76% 0.14 76);
  --color-danger: oklch(70% 0.16 28);
  --color-info: oklch(72% 0.13 250);
}
```

### Color rules

- Accent occupies no more than roughly 5% of a viewport.
- Primary actions may use `--color-ink` as the fill. Accent marks selection, focus, or one key value.
- Status colors are reserved for real status. Every status also has a text label or icon.
- Forecast and historical chart series must also differ by line style or marker, not only color.
- Every foreground/background pair must be measured before release. Body text requires WCAG AA
  4.5:1; large text and boundaries require 3:1; aim for 7:1 on primary body text.
- A component that changes its background must explicitly set its foreground token.

## Typography

Use three roles and no additional families:

| Role | Typeface | Weight | Usage |
|---|---|---:|---|
| Display | Barlow Condensed | 700 | Wordmark, page title, primary recommendation value |
| Body | IBM Plex Sans | 400 and 700 | Navigation, labels, prose, controls, tables |
| Numeric | IBM Plex Mono | 500 and 600 | Prices, dates, coordinates, units, ranks, provenance IDs |

Fonts must be bundled or loaded through framework-supported font tooling with `font-display: swap`.
Do not depend on an unverified paid license. Match fallback metrics to prevent layout shift.

```css
:root {
  --font-display: "Barlow Condensed", "Arial Narrow", sans-serif;
  --font-body: "IBM Plex Sans", Arial, sans-serif;
  --font-numeric: "IBM Plex Mono", ui-monospace, monospace;

  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-md: 1.25rem;
  --text-lg: 1.5625rem;
  --text-xl: 1.953rem;
  --text-2xl: 2.441rem;
  --text-3xl: 3.052rem;
  --text-display: clamp(2.75rem, 4vw + 1rem, 5.25rem);
}
```

Rules:

- Body text is at least 16px. Supporting labels may be 14px, never smaller.
- Numeric displays use tabular figures and right alignment where comparison matters.
- Headings stay roman. No italic heading words and no gradient text.
- Use no more than five sizes on one page.
- Page titles target one line on desktop and at most two lines on mobile.
- Body measure stays between 45 and 70 characters.
- Use sentence case. Reserve all caps for short column labels only.

## Spacing, Shape, and Depth

```css
:root {
  --space-3xs: 0.125rem;
  --space-2xs: 0.25rem;
  --space-xs: 0.5rem;
  --space-sm: 0.75rem;
  --space-md: 1rem;
  --space-lg: 1.5rem;
  --space-xl: 2.5rem;
  --space-2xl: 4rem;
  --space-3xl: 6rem;
  --space-4xl: 9rem;

  --radius-control: 0.375rem;
  --radius-panel: 0.5rem;
  --radius-pill: 999px;

  --border-default: 1px;
  --shadow-whisper: 0 1px 2px oklch(20% 0.02 248 / 0.06);

  --z-base: 1;
  --z-raised: 10;
  --z-dropdown: 100;
  --z-sticky: 200;
  --z-modal: 400;
  --z-toast: 500;
  --z-tooltip: 600;
}
```

- Use grid for page layout and flex only for component internals.
- Panels are flat surfaces separated by space or one visible rule.
- Do not put cards inside cards.
- Do not give every section identical padding.
- Radius is tight and functional. Pills are limited to compact filters or status chips.
- Shadow is rare. Use surface lightness and borders for hierarchy.
- Do not use more than one containment layer around a chart or table.

## Next.js Layout System

### Desktop shell

- Persistent left rail: 224px to 240px, fixed within the app viewport.
- Main canvas: maximum 1440px content width, with a 12-column grid.
- Recommendation workbench: controls occupy 4 columns; result and evidence occupy 8 columns.
- Coverage and forecast pages: context column 3 to 4 columns, analysis area 8 to 9 columns.
- The rail contains the wordmark, four primary routes, snapshot status, and one methodology/help
  disclosure. It does not contain social links or a marketing CTA.

### Mobile shell

- Compact header with wordmark, snapshot status, and menu button.
- Navigation opens as a semantic sheet. No horizontally scrolling top navigation.
- Controls appear before results and collapse into one column.
- The top recommendation remains visible without requiring a wide table.
- Large comparison tables become ranked record blocks. The full table may remain in a labeled,
  horizontally scrollable evidence region only when every column is necessary.

### Page composition

- `/`: decision-first overview. One input summary, one dominant recommendation, two alternatives,
  and a short evidence strip. No marketing hero.
- `/recommend`: full decision workbench with inputs, eligibility summary, dominant result, ranked
  alternatives, map, and backtest evidence.
- `/forecast`: selected mandi context, one primary price chart, forecast interval facts, and model
  comparison. The chart is the visual anchor.
- `/coverage`: snapshot health, mandi coverage comparison, missingness, and provenance. Do not turn
  every metric into a card.

## Streamlit Translation

Streamlit must express the same hierarchy with native primitives wherever possible.

- Keep the sidebar for navigation and secondary filters.
- Keep the primary decision controls in the page body so they are visible during a demo.
- Use `st.metric` only for the dominant recommendation and a small number of verified KPIs.
- Prefer bordered groups, columns, and whitespace over injected card markup.
- Use Plotly theme helpers derived from the canonical tokens.
- Use a single, documented style helper module. Do not duplicate CSS strings across pages.
- Avoid brittle selectors when a Streamlit theme setting or native component can do the job.
- Streamlit may default to light mode if framework constraints make dual-theme control unreliable;
  it must still use the light token hierarchy and pass contrast checks.
- Do not imitate the Next.js rail or mobile sheet using unsafe HTML.

## Core Components

### App rail

- Active route uses an accent rule and stronger ink, not a filled blue pill.
- Snapshot status is compact and factual: `Snapshot 30 Oct 2025`.
- Every target is at least 44px high and has an immediate focus ring.

### Decision controls

- Visible label above every field.
- Helper text explains units or assumptions, not the obvious location of the field.
- Input and button heights match at 44px minimum.
- Border width never changes between default, hover, focus, error, or success.
- Validate on blur, then on change after the field has been touched.
- Current valid values must be shareable through URL query parameters in Next.js.

### Primary recommendation

- One dominant result, not three equal cards.
- Required visible facts: rank, mandi, district, forecast target date, as-of date, forecast price,
  transport estimate, expected net price, lot estimate, distance, and risk label.
- Explain the rank in one direct sentence.
- State that the transport rate and road factor are assumptions.
- Until candidate-specific uncertainty is validated, do not claim uncertainty changes rank order.

### Alternative recommendations

- Present ranks 2 and 3 as compact comparisons adjacent to or below the dominant result.
- Do not repeat every field from the primary result. Show the differences that matter.
- The full eligible list follows as a table or mobile record list.

### Data tables

- Numeric columns are right-aligned and use the numeric font.
- Units belong in headers.
- Sticky headers are allowed only when the table is long enough to need them.
- One divider between rows, not borders on every side.
- Sorting is keyboard accessible and announced.
- On mobile, use record blocks for the recommendation result. Preserve an accessible table for
  evidence-heavy views when comparison across columns is essential.

### Charts

- Historical actual: solid ink-blue line.
- Forecast: dashed accent line with a distinct marker.
- Interval: low-chroma accent band; not the only signal of uncertainty.
- Tooltips include date, units, and whether a value is observed, imputed, or forecast.
- Legends are always visible when more than one series exists.
- Axes include units. Avoid rotated labels unless no readable alternative exists.
- No default library rainbow palette, gradient fill, 3D chart, or animated entrance.
- Every chart has an adjacent textual summary and data-table fallback.

### Map

- The map supports spatial comparison; it is never decorative.
- Farmer location, selected mandi, and alternatives use distinct shapes plus labels.
- Provide the same locations and distances in a table.
- Missing coordinates produce a specific warning and preserve the non-map result.
- Do not recolor the entire base map to match the brand.

### Freshness and limitation notice

- One persistent snapshot notice per page is enough.
- Use neutral information styling unless the data contract is actually invalid.
- The notice names the date and says `Frozen demonstration data`, not `Live` or `Updated`.
- Detailed limitations belong in progressive disclosure, not repeated blue alert boxes.

### Loading, empty, error, and stale states

- Skeletons match the final layout for predictable content.
- Empty states name what is missing, why it matters, and the next available action.
- Errors name the failed artifact or action and provide a retry or regeneration command.
- Stale is a data state, not an application failure.
- Focus moves to the state message only when the state change follows a user action.

## Interaction and Motion

```css
:root {
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-in: cubic-bezier(0.7, 0, 0.84, 0);
  --ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);
  --dur-micro: 120ms;
  --dur-short: 220ms;
  --dur-long: 420ms;
}
```

- No page-wide scroll reveals.
- Animate only transform and opacity.
- A control press may move by 1px. Cards do not universally lift or scale.
- Re-ranking uses a short opacity transition and preserves focus and scroll position.
- Map and chart transitions may show state change, but must never delay the new value.
- Tooltips open after 800ms on hover and immediately on focus.
- Focus rings appear instantly and never animate.
- Reduced motion collapses spatial motion to an opacity transition of 150ms or less.
- No parallax, cursor followers, marquee text, infinite ambient loops, or bounce easing.

## Interaction State Contract

Every interactive component must define:

1. Default
2. Hover where a fine pointer exists
3. Focus-visible
4. Active or pressed
5. Disabled with a reason
6. Loading
7. Error
8. Success

Success is silent when the result is already visible. Use alerts only when the effect is otherwise
hidden or when recovery is needed.

## Copy System

Use concrete labels and verbs.

| Avoid | Use |
|---|---|
| Optimize your outcome | Compare mandis |
| Unlock better prices | View sell options |
| Smart recommendation | Best eligible mandi |
| Confidence score | Observed interval coverage |
| Live market price | Frozen snapshot price |
| Risk-adjusted rank | Transport-adjusted rank |
| Something went wrong | Forecast data could not be loaded |

Additional rules:

- Define `quintal`, `as-of date`, `forecast interval`, and `regret` where first encountered.
- Use `INR/qtl` consistently in compact displays and `INR per quintal` in explanatory copy.
- Do not write guarantees, profit promises, customer claims, or vague superlatives.
- Keep recommendation explanations under 30 words.
- Button labels use a direct verb and remain on one line.

## Responsive Contract

Required Next.js review widths: 320, 375, 414, 768, 1024, and 1440 CSS pixels.

- Mobile-first styles, with content-driven `min-width` breakpoints.
- `html` and `body` use `overflow-x: clip`.
- No `100vw` layout widths and no `h-screen`; use percentages and dynamic viewport units.
- Image-bearing tracks use `minmax(0, 1fr)`.
- Clickable labels never wrap. Collapse the container or shorten the label.
- Display headings use `overflow-wrap: anywhere` and `min-width: 0`.
- Touch targets are at least 44 by 44 CSS pixels, preferably 48px on coarse pointers.
- No hover-only information or action.
- Mobile tables require a deliberate alternative, not accidental horizontal overflow.

## Accessibility Contract

- WCAG 2.2 AA is the release floor.
- Semantic heading order and landmarks are mandatory.
- A skip link is the first focusable element.
- Focus-visible rings must reach at least 3:1 contrast against both control and page.
- Form errors use `aria-invalid` and `aria-describedby`.
- Dynamic recommendation changes use a restrained `aria-live="polite"` summary.
- Charts and maps have textual summaries and tabular fallbacks.
- Risk, freshness, selection, and series identity never rely on color alone.
- Test keyboard-only operation, 200% zoom, reduced motion, dark mode where supported, and common
  color-vision simulations.

## Performance Contract

- Next.js targets: LCP below 2.5s, INP below 200ms, CLS below 0.1 on the deployed static build.
- Keep the initial route lightweight. Load map and heavy chart code only where used.
- Reserve chart and map dimensions to prevent layout shift.
- Do not add a motion library unless CSS cannot express a required state transition.
- Use no WebGL, video, background canvas, or decorative image-generation assets in the operating UI.
- A local production build and Lighthouse report are required before release.

## Anti-Template Bans

- No centered marketing hero.
- No three equal recommendation cards.
- No icon-above-heading feature grid.
- No card-inside-card nesting.
- No pure black or pure white base surfaces.
- No purple-blue gradient, glow, glass panel, gradient text, or ambient blob.
- No fake browser, phone, terminal, or operating-system chrome.
- No decorative farm photos, leaf icons, commodity illustrations, or map textures.
- No pill for every label.
- No uppercase eyebrow above every section.
- No repeated blue information alert for ordinary context.
- No font smaller than 14px for readable content.
- No arbitrary z-index values.
- No invented metric, user, testimonial, freshness, or outcome.

## Implementation Mapping

### Next.js

- Add `web/src/styles/tokens.css` as the canonical CSS token implementation.
- Keep `web/src/app/globals.css` as the framework entry and import tokens before component rules.
- Add shared shell, rail, mobile navigation, field, state, result, table, and evidence components.
- Keep data loading, policy logic, and route ownership intact during the visual rewrite.
- Use one icon family only. Prefer Phosphor if a new dependency is approved; otherwise use text and
  native controls instead of mixing icon sets.

### Streamlit

- Add `src/mandipulse/app/design.py` for Plotly templates, numeric formatting, semantic colors, and
  any carefully scoped shared CSS.
- Update `.streamlit/config.toml` from these tokens.
- Refactor pages to call shared presentation helpers rather than duplicating markup and styles.
- Keep calculation and artifact-loading logic outside page modules.

## Release Acceptance Checklist

- [ ] Product hierarchy matches this specification on both surfaces.
- [ ] The main recommendation is visually dominant and alternatives remain comparable.
- [ ] Public copy says transport-adjusted ranking unless candidate-specific uncertainty is promoted.
- [ ] All tokens are named; no component-level color or font improvisation remains.
- [ ] Contrast, keyboard, screen-reader, 200% zoom, and reduced-motion checks pass.
- [ ] Next.js passes 320, 375, 414, 768, 1024, and 1440 width reviews with no overflow.
- [ ] Streamlit pages remain usable at tablet and desktop widths.
- [ ] Loading, empty, error, stale, disabled, and success states are implemented.
- [ ] Tables, charts, and maps each have an accessible fallback.
- [ ] Production screenshots show real project data and carry no fabricated claim.
- [ ] Lighthouse and bundle checks meet the performance contract.
- [ ] A bounded visual review is complete: one desktop/mobile defect pass, one confirmation pass.

## Change Control

This file is the system authority. A page may vary composition within its assigned job, but it may
not introduce a new palette, font family, radius system, motion language, or navigation pattern.
Amend this document first when a genuine cross-surface need appears.
