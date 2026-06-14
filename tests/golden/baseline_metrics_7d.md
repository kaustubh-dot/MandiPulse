# Onion/Maharashtra 7-Day Baseline Metrics

## Summary

- Feature table: `data\processed\onion_maharashtra\feature_table_7d.csv`
- Prediction rows: `artifacts\predictions\baseline_predictions_7d.csv`
- Train rows: 17,353
- Validation rows: 1,272
- Test rows: 1,204
- Markets: 15
- Row filter: `all`
- Observed targets in train: 13,900
- Observed targets in validation: 1,039
- Observed targets in test: 919
- Train dates: 2020-01-31 to 2025-04-12
- Validation dates: 2025-04-20 to 2025-07-18
- Test dates: 2025-07-26 to 2025-10-23
- Best test baseline by MAE: `moving_average_7d` (139.57 INR/quintal)
- Ridge test MAE: 224.43 INR/quintal
- Next sanity check: run observed-only/imputation sensitivity before treating LightGBM as the next guaranteed step.

## Overall Metrics

| model | split | rows | mae | rmse | smape_pct | mase |
| --- | --- | --- | --- | --- | --- | --- |
| moving_average_7d | validation | 1272 | 126.07 | 329.37 | 10.73 | 0.48 |
| ridge | validation | 1272 | 135.98 | 329.69 | 11.47 | 0.517 |
| seasonal_naive_7d | validation | 1272 | 138.54 | 428.24 | 11.59 | 0.527 |
| moving_average_30d | validation | 1272 | 159.54 | 336.88 | 13.73 | 0.607 |
| moving_average_7d | test | 1204 | 139.57 | 332.41 | 11.94 | 0.531 |
| moving_average_30d | test | 1204 | 142.85 | 319.9 | 12.27 | 0.544 |
| seasonal_naive_7d | test | 1204 | 146.26 | 424.18 | 12.2 | 0.557 |
| ridge | test | 1204 | 224.43 | 369.08 | 18.72 | 0.854 |

## Best Test Baseline By Mandi

| market_id | market_name | rows | mae | rmse | smape_pct | mase |
| --- | --- | --- | --- | --- | --- | --- |
| 1462 | Satara | 80 | 60.27 | 85.66 | 4.15 | 0.234 |
| 160 | Kolhapur | 90 | 88.41 | 119.13 | 9.13 | 0.411 |
| 2495 | Pune(Khadiki) | 90 | 96.75 | 120.43 | 8.99 | 0.463 |
| 3108 | Vashi New Mumbai | 78 | 100.55 | 125.54 | 7.85 | 0.348 |
| 581 | Chattrapati Sambhajinagar | 81 | 104.77 | 126.35 | 13.2 | 0.396 |
| 2484 | Lasalgaon(Niphad) | 78 | 110.77 | 141.24 | 8.51 | 0.389 |
| 170 | Pimpalgaon | 78 | 111.26 | 135.08 | 8.36 | 0.442 |
| 169 | Lasalgaon | 36 | 116.21 | 152.06 | 8.68 | 0.465 |
| 176 | Solapur | 78 | 132.14 | 162.9 | 12.45 | 0.594 |
| 575 | Manmad | 77 | 139.54 | 190.74 | 12.89 | 0.53 |
| 2494 | Pune(Pimpri) | 90 | 142.46 | 178.61 | 10.67 | 0.388 |
| 4752 | Pune(Moshi) | 90 | 155.32 | 225.76 | 15.38 | 0.664 |
| 168 | Nasik | 78 | 176.4 | 218.69 | 17.94 | 0.59 |
| 4751 | Pune(Manjri) | 90 | 253.49 | 517.96 | 22.1 | 0.765 |
| 172 | Pune | 90 | 270.08 | 962.24 | 15.58 | 1.189 |

## Baseline Definitions

- `seasonal_naive_7d`: predicts the 7-day-ahead price as the current as-of date modal price.
- `moving_average_7d`: predicts using the 7-day rolling mean available on the as-of date.
- `moving_average_30d`: predicts using the 30-day rolling mean available on the as-of date.
- `ridge`: linear baseline using lag, rolling, return, calendar, market, and district features.

## Metric Notes

- MAE/RMSE are INR per quintal.
- sMAPE is percentage error.
- MASE is scaled by the average absolute 7-day seasonal difference in the training period.
- Splits are date-based only; no random split is used.
- The training split is purged by the forecast horizon so no training target resolves inside the validation window.
- The validation split is also purged by the forecast horizon so no validation target resolves inside the test window (both gaps = horizon_days = 7 days).