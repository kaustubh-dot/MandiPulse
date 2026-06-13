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

Color must reinforce status and risk.

| Color | Meaning | Usage |
|---|---|---|
| Green | Healthy/low risk | Good data coverage, low recommendation risk |
| Yellow | Warning/medium risk | Elevated uncertainty, stale-ish data, medium risk |
| Red | Problem/high risk | Stale data, missing model, high risk |
| Blue/neutral | Informational | Forecast lines, selected filters, neutral KPIs |
| Gray | Secondary | Gridlines, disabled states, helper labels |

Rules:

- Do not make the whole UI green.
- Use green/yellow/red only when status has meaning.
- Avoid one-note palettes dominated by a single hue.
- Use red sparingly for true user-impacting problems.

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
