# MandiPulse India Design Spec

## Product Design Goal

MandiPulse should feel like a credible market intelligence dashboard for agricultural decision-making. It should be clear, data-heavy, and practical. It should not feel like a flashy landing page, a childish agriculture-themed app, or a generic chart gallery.

## Visual Style Direction

| Area | Direction |
|---|---|
| Overall feel | Analytical, calm, credible, decision-focused |
| Density | Medium-high information density, but readable |
| Layout | Dashboard-first, no marketing hero |
| Typography | Clean sans-serif, compact headings, readable table text |
| Cards | Use only for KPIs, repeated metric blocks, and focused panels |
| Decoration | Minimal; avoid farm clipart and decorative gradients |
| Charts | Clear axes, labels, legends, and tooltips |
| Maps | Useful for mandi comparison, not decorative |
| Tone | Professional and practical |

## Color Semantics

Color must reinforce market status and risk.

| Color | Meaning | Usage |
|---|---|---|
| Green | Normal | Normal regime, healthy data, low risk |
| Yellow | Volatile | Elevated volatility, warning, medium risk |
| Red | Crisis/anomaly | Crisis/anomaly, stale data, high risk |
| Blue/neutral | Informational | Forecast lines, selected filters, neutral KPIs |
| Gray | Secondary | Gridlines, disabled states, helper labels |

Rules:

- Do not make the whole UI green.
- Use green/yellow/red only when status has meaning.
- Avoid one-note palettes dominated by a single hue.
- Use red sparingly for true anomaly/crisis states.

## Dashboard Layout

### Global Layout

- Left sidebar for filters/navigation if using Streamlit defaults.
- Main content area with page title, compact description, controls, then outputs.
- Top KPI strip on Overview and Monitoring pages.
- Tables below summary metrics for scan-friendly comparison.
- Charts should have enough width and not be squeezed into tiny cards.

### Navigation

Pages:

1. Overview.
2. Forecast.
3. Mandi Recommendation.
4. Regime / Anomaly.
5. Monitoring.

Optional/future pages should not appear until implemented:

- Arbitrage.
- Similar Days.
- Price Transmission Graph.

## Page Sections

### Overview

Sections:

- KPI strip:
  - Total mandis.
  - Crops tracked.
  - Latest data date.
  - Volatile markets count.
  - Model version.
- Market health chart:
  - Count of normal/volatile/crisis markets.
- Latest prices table:
  - Crop, state, mandi, latest price, recent change.
- Volatile markets table:
  - Crop, mandi, state, regime, reason.

### Forecast

Sections:

- Filter controls:
  - Crop.
  - State.
  - Mandi.
  - Horizon.
- Forecast summary metrics:
  - Forecast price.
  - Lower bound.
  - Upper bound.
  - Confidence level.
  - Regime.
- Price chart:
  - Actual historical price line.
  - Forecast line.
  - Confidence interval band.
- Backtest chart:
  - Actual vs predicted.
- Driver summary:
  - Top forecast drivers.

### Mandi Recommendation

Sections:

- Input controls:
  - Farmer latitude.
  - Farmer longitude.
  - Crop.
  - Quantity.
  - Candidate states.
  - Horizon.
- Recommendation summary:
  - Recommended mandi.
  - Expected net price.
  - Risk level.
  - Reason.
- Ranked mandi table:
  - Rank.
  - Mandi.
  - State.
  - Forecast price.
  - Transport cost.
  - Net expected price.
  - Risk-adjusted score.
  - Regime.
- Map:
  - Farmer location.
  - Candidate mandis.
  - Top recommendation highlighted.

### Regime / Anomaly

Sections:

- Current regime indicator.
- Volatility trend chart.
- Anomaly timeline.
- Recent abnormal movement table.
- Explanation panel.

### Monitoring

Sections:

- Data freshness status.
- Missing data percentage.
- Duplicate/invalid record counts.
- Recent forecast error.
- Empirical interval coverage.
- Drift status.
- API health and latency.
- MLflow model version.

## Component List

| Component | Usage |
|---|---|
| KPI metric | Overview and Monitoring summaries |
| Filter control | Crop, state, mandi, horizon |
| Segmented control/selectbox | Forecast horizon selection |
| Numeric input | Quantity, latitude, longitude |
| Multi-select | Candidate states |
| Status badge | Normal, volatile, crisis/anomaly |
| Line chart | Price history and forecast |
| Confidence band | Forecast uncertainty |
| Bar chart | Feature importance, market health counts |
| Table | Ranked mandis, latest prices, anomalies |
| Map | Farmer location and candidate mandis |
| Alert box | Data stale, high risk, missing model |
| Tooltip/help text | Explain technical terms briefly |

## Chart Types

| Chart | Purpose |
|---|---|
| Line chart | Historical price, forecast, volatility over time |
| Line chart with band | Forecast plus uncertainty interval |
| Bar chart | Top drivers, market health count, missingness by mandi |
| Scatter/map points | Candidate mandi locations |
| Table with conditional formatting | Recommendations and anomalies |
| Small KPI trend | Recent forecast error or freshness |

## Map and Table Usage

### Map

Use maps only where location affects the decision:

- Farmer location.
- Candidate mandis.
- Recommended mandi.
- Approximate distance or transport cost.

Map requirements:

- Recommended mandi should be visually distinct.
- Points should not rely on color alone; use label or marker size where possible.
- If coordinates are missing, show a clear warning and table fallback.

### Tables

Tables are central to the app because the recommendation is comparative.

Recommended table behavior:

- Sort ranked mandis by risk-adjusted score.
- Use conditional formatting for risk and regime.
- Keep numeric columns aligned.
- Show INR/quintal units in column labels or captions.
- Avoid too many decimal places.

## Empty, Loading, and Error States

### Empty States

| Context | Message Direction |
|---|---|
| No crop selected | Ask user to select crop |
| No mandi selected | Ask user to select mandi |
| No candidate mandis | Ask user to widen candidate states |
| No model result | Explain model artifact is unavailable |
| No regime data | Forecast can continue, but regime is unavailable |

### Loading States

- Show a spinner or skeleton for forecast generation.
- Show loading placeholder for recommendation table.
- Show map loading state separately from table results.
- Avoid clearing old results until new request succeeds.

### Error States

| Error | UI Behavior |
|---|---|
| API unavailable | Show service error and suggest retry |
| Model unavailable | Show model status warning |
| Data stale | Show yellow or red freshness status depending on age |
| Invalid coordinates | Show validation message near inputs |
| Unsupported horizon | Restrict selector to valid options |
| Insufficient history | Suggest another mandi or crop |

## Mobile Responsiveness Notes (Non-MVP)

Mobile responsiveness is not an MVP requirement. Streamlit has limited mobile support and this is not a mobile-targeted project. The following guidelines are for future reference only.

Streamlit is not a perfect mobile framework, but the layout should remain usable:

- Stack KPI cards vertically on narrow screens.
- Keep filters above outputs.
- Avoid wide charts with tiny labels.
- Let tables scroll horizontally if necessary.
- Maps should be full-width on mobile.
- Avoid placing more than two compact metrics per row on small screens.

## Demo Screenshots to Capture Later

Capture these after implementation:

1. Overview page with market health summary.
2. Forecast page showing confidence interval band.
3. Recommendation page showing ranked mandis and map.
4. Regime/anomaly page showing volatile market reason.
5. Monitoring page showing data freshness and model version.
6. API docs page from FastAPI `/docs`.
7. MLflow experiment comparison page.
8. Docker Compose running services, if useful for README.

## Design Principles

- Clear: the user should understand the recommendation quickly.
- Credible: show uncertainty, data freshness, and model version.
- Data-heavy but readable: use tables and charts without clutter.
- Not flashy: avoid decorative visuals that reduce trust.
- Not childish agriculture theme: no cartoon farming motifs.
- Decision-first: forecast outputs should feed a selling decision.
- Honest: show limitations and high-risk warnings.
- Consistent: green/yellow/red should always mean normal/volatile/crisis.

## MVP Design Acceptance Checklist

- [ ] First screen communicates market intelligence, not generic prediction.
- [ ] Forecast chart includes uncertainty interval.
- [ ] Recommendation table includes transport cost and net price.
- [ ] Regime labels use green/yellow/red semantics.
- [ ] Monitoring page makes data/model reliability visible.
- [ ] Empty and error states are understandable.
- [ ] Mobile layout remains usable.
- [ ] No optional advanced module appears before it exists.

