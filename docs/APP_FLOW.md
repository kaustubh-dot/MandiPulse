# MandiPulse India App Flow

## MVP Flow

The narrowed MVP is an offline Streamlit dashboard for Onion mandis in Maharashtra. It reads saved local artifacts; it does not require a live CEDA key, FastAPI service, regime/anomaly module, or monitoring stack.

## End-User Journey

1. User opens the Streamlit dashboard.
2. User checks the static data coverage summary.
3. User selects one of the 15 Maharashtra onion mandis.
4. User reviews historical price, 7-day forecast, uncertainty interval, and baseline comparison.
5. User enters farmer latitude, longitude, and quantity.
6. System ranks candidate mandis by forecast net price after transport cost.
7. User reviews the top 3 alternatives and the assumptions behind the ranking.

## Dashboard Pages

### Page 1: Data Coverage

Purpose: prove the dataset is usable before showing predictions.

Sections:

- Loaded data range.
- Selected 15 mandis.
- Observed, imputed, and long-gap missing rows.
- Duplicate handling summary.
- Trainable rows by mandi.

Primary action:

- Continue only if the chosen mandi has enough trainable rows.

### Page 2: Forecast

Purpose: show 7-day price expectations honestly.

Sections:

- Mandi selector.
- Historical modal price chart.
- 7-day forecast and uncertainty interval.
- Baseline vs model metrics.
- Notes on missingness and imputation.

Primary action:

- Continue to recommendation with the selected forecast date.

### Page 3: Recommendation

Purpose: answer where to sell after transport cost.

Sections:

- Farmer latitude and longitude.
- Quantity in quintals.
- Transport assumptions.
- Ranked top 3 mandis.
- Forecast price, estimated transport cost, net expected price, and risk flag.
- Map of farmer and candidate mandis once coordinates are available.

Primary action:

- Compare whether a higher gross price survives transport cost.

## Forecast Flow

1. Load `data/processed/onion_maharashtra/feature_table_7d.csv`.
2. Filter to `feature_row_valid == True`.
3. Apply temporal split.
4. Compare naive/seasonal/moving-average baselines.
5. Train or load the 7-day model.
6. Produce forecast, interval, and backtest metrics.
7. Render results in Streamlit.

Expected output:

- Forecast price.
- Lower and upper bound.
- Confidence level or residual interval method.
- Baseline comparison.
- Data-quality context.

## Recommendation Flow

1. Load latest forecast per selected mandi.
2. Load selected mandi metadata and coordinates.
3. Estimate road distance from farmer to mandi using haversine distance times road factor.
4. Estimate transport cost per quintal.
5. Calculate expected net price.
6. Apply uncertainty penalty.
7. Rank mandis and show top 3.

Expected output:

- Recommended mandi.
- Forecast gross price.
- Estimated transport cost.
- Expected net price per quintal.
- Risk level.
- Ranked alternatives.

## Error States

| Scenario | User-Facing Behavior |
|---|---|
| Mandi has insufficient trainable rows | Disable forecast and suggest another selected mandi |
| Missing model artifact | Show baseline-only results until model is trained |
| Missing mandi coordinates | Disable recommendation but keep forecast available |
| Forecast interval very wide | Show high-risk warning, not a confident recommendation |
| Long missing gaps | Show data-quality warning and exclude affected rows from training |

## Demo Flow

1. Start with the framing: "This is not generic crop price prediction; it is a mandi decision product."
2. Show the data coverage report and selected 15 mandis.
3. Show a 7-day forecast for Lasalgaon or Pimpalgaon.
4. Compare model performance against naive baselines.
5. Enter a farmer location and show transport-adjusted ranking.
6. Close with the engineering story: CEDA data grab, clean panel, leakage-safe features, temporal validation, and Streamlit product.

## Guardrails

- Do not add FastAPI to the MVP.
- Do not add regime/anomaly pages to the MVP.
- Do not add Tomato, Karnataka, Uttar Pradesh, or 14/30-day horizons until the Onion/Maharashtra 7-day loop works.
- Do not present forecasts without baseline comparison.
- Do not hide missingness or imputation.
