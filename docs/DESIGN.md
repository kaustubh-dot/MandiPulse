# MandiPulse Design Spec

## Product Design Goal

MandiPulse should feel like a credible market-intelligence dashboard for agricultural decision-making. It should be clear, data-heavy, and practical. It should not feel like a flashy landing page, a childish agriculture-themed app, or a generic chart gallery.

The MVP interface is a Streamlit dashboard over local artifacts for Onion/Maharashtra only.

## Visual Direction

| Area | Direction |
|---|---|
| Overall feel | Analytical, calm, credible, decision-focused |
| Density | Medium-high information density, but readable |
| Layout | Dashboard-first, no marketing hero |
| Typography | Clean sans-serif, compact headings, readable table text |
| Cards | Use only for KPIs, repeated metrics, and focused panels |
| Decoration | Minimal; avoid farm clipart and decorative gradients |
| Charts | Clear axes, labels, legends, and tooltips |
| Maps | Useful for mandi comparison, not decorative |
| Tone | Professional and practical |

## Color Semantics

Color must reinforce status and risk. Hex values below are the canonical tokens
(see [Design System Tokens](#design-system-tokens) for the full palette). All text-on-surface
pairings meet WCAG AA (4.5:1); status fills meet 3:1 for graphical use.

| Color | Meaning | Hex (text / fill) | Usage |
|---|---|---|---|
| Green | Healthy/low risk | `#15803D` / `#16A34A` | Good data coverage, low recommendation risk |
| Yellow/Amber | Warning/medium risk | `#B45309` / `#D97706` | Elevated uncertainty, stale-ish data, medium risk |
| Red | Problem/high risk | `#B91C1C` / `#DC2626` | Stale data, missing model, high risk |
| Blue/neutral | Informational | `#1E40AF` / `#3B82F6` | Forecast lines, selected filters, neutral KPIs |
| Gray | Secondary | `#475569` / `#E2E8F0` | Gridlines, disabled states, helper labels |

Rules:

- Do not make the whole UI green.
- Use green/yellow/red only when status has meaning.
- Avoid one-note palettes dominated by a single hue.
- Use red sparingly for true user-impacting problems.

## Design System Tokens

Concrete, implementation-ready tokens for the Streamlit MVP. Style direction: **Data-Dense
Dashboard** (BI/analytics, space-efficient, maximum data visibility, WCAG AA). These values are
mirrored in [`.streamlit/config.toml`](../.streamlit/config.toml) for the app theme; keep the two
in sync. Provenance: generated and validated with the `ui-ux-pro-max` design skill, then adjusted
for this product's risk semantics.

### Color Palette

| Role | Token | Hex | Notes |
|---|---|---|---|
| Primary / brand | `--color-primary` | `#1E40AF` | Selected filters, neutral KPIs, primary actions |
| Secondary | `--color-secondary` | `#3B82F6` | Secondary series, links, subtle emphasis |
| Accent / forecast | `--color-accent` | `#D97706` | Forecast line + highlights (amber, distinct from blue history) |
| Background (page) | `--color-background` | `#F8FAFC` | App canvas |
| Surface (card) | `--color-surface` | `#FFFFFF` | KPI cards, panels |
| Muted surface | `--color-muted` | `#E9EEF6` | Sidebar, secondary panels, table header fill |
| Border | `--color-border` | `#CBD5E1` | Card/table borders, dividers (visible, not faint) |
| Foreground (text) | `--color-foreground` | `#0F172A` | Body and table text (slate-900) |
| Secondary text | `--color-text-muted` | `#475569` | Captions, helper text, units (slate-600) |
| Gridline | `--color-grid` | `#E2E8F0` | Chart gridlines (low-contrast, never compete with data) |
| Success / low risk | `--color-success` | `#15803D` | Risk badge text; fill `#16A34A` |
| Warning / med risk | `--color-warning` | `#B45309` | Risk badge text; fill `#D97706` |
| Danger / high risk | `--color-danger` | `#B91C1C` | Risk badge text; fill `#DC2626` |

Rule: never convey status by color alone — pair every risk color with an icon or text label
(e.g. `● Low`, `▲ Medium`, `■ High`).

### Typography

| Use | Font | Rationale |
|---|---|---|
| Headings & body | **Fira Sans** (400/500/600/700) | Clean, compact, credible analytical sans |
| Numeric / tabular data | **Fira Code** (tabular figures) | Prices, INR/quintal columns, metrics — prevents column jitter |

- Base body size 16px, line-height 1.5; table text may step down to 14px but no smaller.
- Type scale: 12 / 14 / 16 / 20 / 24 / 32. Weight for hierarchy: 600–700 headings, 400 body, 500 labels.
- Use tabular figures for every numeric column and KPI value so digits align.

### Spacing & Layout

- 4 / 8 px spacing rhythm; section spacing tiers 16 / 24 / 32.
- Dashboard grid, no marketing hero. KPI strip → primary chart/table → supporting detail.
- Keep numeric columns right-aligned; show units (INR/quintal) in the column label or caption.

### Chart Specifications

Library: Plotly (charts) + Folium/PyDeck (maps). Apply these per chart family:

| Chart | When | Encoding |
|---|---|---|
| **Line + confidence band** | 7-day price forecast | Historical actual: solid `#1E40AF`. Forecast: **dashed** `#D97706`. Interval: same-hue fill at 15% opacity. Distinguish actual vs forecast by line style, not color alone. |
| **Bar (sorted desc)** | Baseline vs model comparison; coverage by mandi | One bar per category, sorted by value, value labels visible. Use for ≤15 categories, else table. |
| **Choropleth / bubble map** | Farmer ↔ candidate mandis, transport distance | Single-hue gradient or sized bubbles; highlight top recommendation; always provide the ranked table as the accessible fallback. |

Cross-cutting chart rules: legends always visible with line-style described; tooltips show exact
values; gridlines `#E2E8F0`; label axes with units; show a "No data" empty state and a skeleton
while loading; respect `prefers-reduced-motion` (data must read without animation).

### Effects & Anti-Patterns

- Allowed: hover tooltips, row highlight on hover, chart zoom, smooth (150–300ms) filter transitions.
- Avoid: ornate decoration, farm clipart, decorative gradients, emoji-as-icons, one-note all-green
  palettes, charts without filtering or legends.

## MVP Navigation

Pages:

1. Data Coverage.
2. Forecast.
3. Mandi Recommendation.

Do not show Regime/Anomaly, Monitoring, API Docs, Similar Days, Arbitrage, or Price Transmission pages in the MVP navigation.

## Page Requirements

### Data Coverage

Sections:

- KPI strip:
  - Selected mandis.
  - Latest available date.
  - Observed rows.
  - Imputed rows.
  - Trainable feature rows.
- Coverage chart by mandi.
- Missingness or gap summary by mandi.
- Selected mandi list table.
- Data caveat panel explaining that local cached data is used.

### Forecast

Sections:

- Filter controls:
  - Crop, fixed to Onion for MVP.
  - State, fixed to Maharashtra for MVP.
  - Mandi.
  - Horizon, fixed to 7 days for MVP.
- Forecast summary metrics:
  - Forecast price.
  - Lower bound.
  - Upper bound.
  - Confidence level.
- Price chart:
  - Historical modal price.
  - Forecast marker/line.
  - Uncertainty interval when available.
- Baseline comparison:
  - Seasonal naive.
  - Moving average.
  - Ridge/linear baseline.
  - LightGBM once trained.

### Mandi Recommendation

Sections:

- Input controls:
  - Farmer latitude.
  - Farmer longitude.
  - Quantity.
  - Transport cost assumption.
  - Candidate mandi filter.
- Recommendation summary:
  - Recommended mandi.
  - Expected net price.
  - Risk level.
  - Explanation.
- Ranked mandi table:
  - Rank.
  - Mandi.
  - District.
  - Forecast price.
  - Estimated transport cost.
  - Net expected price.
  - Uncertainty penalty.
  - Risk-adjusted score.
- Map:
  - Farmer location.
  - Candidate mandis.
  - Top recommendation highlighted.

## Component List

| Component | Usage |
|---|---|
| KPI metric | Data coverage and forecast summaries |
| Filter control | Mandi and optional date controls |
| Selectbox | Mandi selection |
| Numeric input | Quantity, latitude, longitude, transport assumptions |
| Slider | Transport-cost sensitivity |
| Line chart | Price history and forecast |
| Confidence band | Forecast uncertainty |
| Bar chart | Coverage and baseline comparison |
| Table | Ranked mandis and coverage details |
| Map | Farmer location and candidate mandis |
| Alert box | Missing model, stale data, missing coordinates |
| Tooltip/help text | Explain technical terms briefly |

## Tables and Maps

Tables are central because the product is comparative.

Recommended table behavior:

- Sort ranked mandis by risk-adjusted score.
- Keep numeric columns aligned.
- Show INR/quintal units in column labels or captions.
- Avoid unnecessary decimals.
- Show assumptions near derived numbers.

Use maps only where location affects the decision:

- Farmer location.
- Candidate mandis.
- Recommended mandi.
- Approximate distance or transport cost.

If coordinates are missing, show a clear warning and table fallback.

## Empty and Error States

| Context | Message direction |
|---|---|
| No mandi selected | Ask user to select a mandi |
| No model result | Explain model artifact is unavailable |
| Missing coordinates | Explain recommendation cannot run until coordinates are filled |
| Unsupported horizon | Restrict selector to 7 days |
| Insufficient history | Suggest another mandi |
| Missing local data | Show the script command needed to regenerate artifacts |

## Demo Screenshots to Capture Later

Capture these after implementation:

1. Data Coverage page showing selected mandis and coverage.
2. Forecast page showing historical price, forecast, interval, and baseline comparison.
3. Recommendation page showing ranked mandis and map.
4. MLflow experiment comparison page, if useful after modeling.

## MVP Design Acceptance Checklist

- [ ] First screen communicates market decision intelligence, not generic prediction.
- [ ] Forecast chart includes uncertainty once intervals exist.
- [ ] Recommendation table includes transport cost and net price.
- [ ] Data coverage and model limitations are visible.
- [ ] Empty and error states are understandable.
- [ ] No optional advanced module appears before it exists.
- [ ] Palette and fonts match [Design System Tokens](#design-system-tokens) / `.streamlit/config.toml`.
- [ ] Risk status uses icon or text in addition to color (never color alone).
- [ ] Numeric columns use tabular figures and show INR/quintal units.
- [ ] Text-on-surface pairings pass WCAG AA (4.5:1); chart series readable without color.
