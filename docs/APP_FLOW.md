# MandiPulse India App Flow

## End-User Journey

1. User opens the dashboard.
2. User checks overall market health and data freshness.
3. User selects crop, state, mandi, and forecast horizon.
4. User reviews forecast price, uncertainty interval, market regime, and top drivers.
5. User enters farmer location, crop, quantity, candidate states, and horizon.
6. System ranks candidate mandis by risk-adjusted expected net price after transport cost.
7. User reviews recommended mandi, alternatives, map/table context, and risk.
8. User checks regime/anomaly page if market looks volatile.
9. User checks monitoring page to understand data/model reliability.

## Dashboard Page-by-Page Flow

### Page 1: Overview

Purpose: show whether the system is up to date and what the current market looks like.

Sections:

- KPI strip:
  - Total mandis tracked.
  - Crops tracked.
  - Latest data date.
  - Active volatile markets.
  - Current model version.
- Market health summary:
  - Normal, volatile, crisis/anomaly counts.
- Latest price snapshot:
  - Crop/state filters.
  - Top recent price moves.
- Volatile market table:
  - Crop, mandi, state, regime, reason.

Primary action:

- Select a mandi and continue to Forecast View.

### Page 2: Forecast

Purpose: show future price expectations with uncertainty.

Sections:

- Filter panel:
  - Crop.
  - State.
  - Mandi.
  - Forecast horizon: 7, 14, 30 days.
- Forecast chart:
  - Historical actual price.
  - Forecast line.
  - Confidence interval band.
- Backtest chart:
  - Actual vs predicted for recent test period.
- Forecast details:
  - Forecast price.
  - Lower bound.
  - Upper bound.
  - Confidence level.
  - Market regime.
  - Top drivers.

Primary action:

- Continue to recommendation using selected crop and horizon.

### Page 3: Mandi Recommendation

Purpose: answer where to sell after transport cost and forecast uncertainty.

Sections:

- Input panel:
  - Farmer latitude and longitude.
  - Crop.
  - Quantity in quintals.
  - Candidate states.
  - Horizon.
- Recommended mandi summary:
  - Recommended mandi.
  - Expected net price per quintal.
  - Estimated transport cost.
  - Risk level.
  - Reason.
- Ranked alternatives table:
  - Rank.
  - Mandi.
  - State.
  - Forecast price.
  - Transport cost.
  - Net expected price.
  - Uncertainty interval.
  - Risk-adjusted score.
  - Regime.
- Map:
  - Farmer location.
  - Candidate mandis.
  - Recommended mandi highlighted.

Primary action:

- Compare top mandis and inspect forecast/regime details.

### Page 4: Regime / Anomaly

Purpose: explain whether the market is normal, volatile, or abnormal.

Sections:

- Regime indicator:
  - Normal, volatile, crisis/anomaly.
- Volatility chart:
  - Rolling 7-day and 30-day volatility.
- Anomaly timeline:
  - Dates with abnormal returns or price jumps.
- Reason panel:
  - Example: "7-day volatility is 2.4x above normal."
- Recent abnormal movements table:
  - Date.
  - Price.
  - Return.
  - Z-score or anomaly score.

Primary action:

- Use risk context before trusting recommendation.

### Page 5: Monitoring

Purpose: show reliability of data, model, and API.

Sections:

- Data freshness:
  - Latest available date.
  - Days since last update.
- Data quality:
  - Missing percentage by crop/state/mandi.
  - Duplicate count.
  - Invalid value count.
- Forecast performance:
  - Recent MAE/RMSE/sMAPE.
  - Error trend by horizon.
- Drift:
  - Feature drift summary.
  - Price distribution shift.
- System metrics:
  - API status.
  - Model version.
  - Inference success rate.
  - Recent latency.

Primary action:

- Confirm demo/system reliability before presenting decisions.

## Forecast Flow

1. User selects crop, state, mandi, and horizon.
2. Dashboard sends request to `POST /forecast`.
3. API validates request.
4. API loads latest feature row and model artifact.
5. API generates forecast for selected horizon.
6. API attaches uncertainty interval.
7. API fetches or computes regime label.
8. API returns forecast response with top drivers.
9. Dashboard renders chart, interval band, and explanation.

Expected output:

- Forecast price.
- Lower and upper bound.
- Confidence level.
- Market regime.
- Top drivers.
- Backtest context if available.

## Mandi Recommendation Flow

1. User enters farmer location, crop, quantity, candidate states, and horizon.
2. Dashboard sends request to `POST /recommend`.
3. API identifies candidate mandis within selected states.
4. API forecasts price for each candidate mandi.
5. API estimates transport cost per quintal.
6. API calculates expected net price.
7. API applies uncertainty penalty.
8. API ranks mandis by risk-adjusted score.
9. API returns recommended mandi and alternatives.
10. Dashboard renders recommendation summary, ranked table, and map.

Expected output:

- Recommended mandi.
- Expected net price per quintal.
- Transport cost estimate.
- Risk level.
- Ranked alternatives.
- Reason.

## Regime / Anomaly Flow

1. User selects crop and mandi or arrives from forecast page.
2. Dashboard calls `GET /regime`.
3. API retrieves recent price history and precomputed regime state.
4. API returns current regime, reason, volatility values, and anomaly dates.
5. Dashboard renders regime badge, volatility chart, and anomaly timeline.

Regime labels:

- Normal.
- Volatile.
- Crisis/anomaly.

## Monitoring / Admin Flow

1. User opens Monitoring page.
2. Dashboard calls `GET /metrics`.
3. API returns current data, model, and system metrics.
4. Dashboard highlights freshness, missingness, drift, and forecast error.
5. User can identify whether the app is demo-ready.

## Error States and Empty States

| Scenario | User-Facing Behavior |
|---|---|
| Crop has no data | Show "No data available for this crop in the selected scope." |
| Mandi has insufficient history | Disable forecast and suggest another mandi |
| Horizon not supported | Show valid options: 7, 14, 30 |
| Missing farmer location | Prompt for latitude and longitude |
| No candidate mandis found | Ask user to widen candidate states |
| Model artifact missing | Show service unavailable message and log error |
| Data stale | Show warning with latest data date |
| API request fails | Show retry message and preserve current filters |
| Forecast interval very wide | Show high-risk warning, not a confident recommendation |
| Regime unavailable | Show "Regime not available for selected market" and continue forecast display |

## Loading States

- Forecast chart skeleton while forecast loads.
- Recommendation table skeleton while candidate mandis are ranked.
- Map placeholder while coordinates load.
- Monitoring metric placeholders while API responds.

## Demo Flow for Placement / Interview Presentation

1. Start with the project framing:
   - "This is not generic crop price prediction. It is a mandi decision intelligence system."
2. Show Overview:
   - Crops, mandis, latest data date, volatile markets.
3. Show Forecast:
   - Select Onion, Maharashtra, Lasalgaon, 14 days.
   - Explain temporal validation and uncertainty band.
4. Show Recommendation:
   - Enter farmer location and quantity.
   - Show how a high gross price can lose after transport cost.
5. Show Regime / Anomaly:
   - Highlight volatile market period and reason.
6. Show Monitoring:
   - Data freshness, missingness, forecast error, model version.
7. Close with engineering:
   - FastAPI, Streamlit, MLflow, Docker, tests, monitoring.

## Flow Guardrails

- The app should always lead with decision context, not only charts.
- The recommendation page must include transport cost and uncertainty.
- Forecasts should never be presented without intervals.
- Regime labels should be cautious and explainable.
- Optional advanced modules should not appear in the main nav until implemented.

