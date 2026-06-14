# Onion/Maharashtra 7-Day Baseline Metrics

## Summary

- Feature table: `data\processed\onion_maharashtra\feature_table_7d.csv`
- Prediction rows: `reports\modeling\baseline_predictions_7d.csv`
- Train rows: 17,493
- Validation rows: 1,307
- Test rows: 1,204
- Markets: 15
- Train dates: 2020-01-31 to 2025-04-26
- Validation dates: 2025-04-27 to 2025-07-25
- Test dates: 2025-07-26 to 2025-10-23
- Best test baseline by MAE: `moving_average_7d` (142.45 INR/quintal)

## Overall Metrics

| model | split | rows | mae | rmse | smape_pct | mase |
| --- | --- | --- | --- | --- | --- | --- |
| moving_average_7d | validation | 1307 | 128.29 | 330.64 | 10.75 | 0.49 |
| seasonal_naive_7d | validation | 1307 | 135.09 | 422.34 | 11.19 | 0.516 |
| ridge | validation | 1307 | 143.73 | 329.98 | 11.93 | 0.549 |
| moving_average_30d | validation | 1307 | 158.26 | 332.87 | 13.47 | 0.604 |
| moving_average_7d | test | 1204 | 142.45 | 333.53 | 12.17 | 0.544 |
| moving_average_30d | test | 1204 | 144.27 | 320.58 | 12.38 | 0.551 |
| seasonal_naive_7d | test | 1204 | 146.26 | 424.18 | 12.2 | 0.558 |
| ridge | test | 1204 | 239.03 | 377.63 | 19.71 | 0.912 |

## Best Test Baseline By Mandi

| market_id | market_name | rows | mae | rmse | smape_pct | mase |
| --- | --- | --- | --- | --- | --- | --- |
| 1462 | Satara | 80 | 61.52 | 85.02 | 4.23 | 0.237 |
| 160 | Kolhapur | 90 | 87.3 | 116.23 | 9.0 | 0.407 |
| 2495 | Pune(Khadiki) | 90 | 99.76 | 120.94 | 9.28 | 0.478 |
| 581 | Chattrapati Sambhajinagar | 81 | 104.48 | 125.8 | 13.1 | 0.397 |
| 3108 | Vashi New Mumbai | 78 | 105.95 | 129.96 | 8.24 | 0.37 |
| 169 | Lasalgaon | 36 | 116.57 | 155.56 | 8.72 | 0.466 |
| 170 | Pimpalgaon | 78 | 117.22 | 141.35 | 8.8 | 0.465 |
| 2484 | Lasalgaon(Niphad) | 78 | 117.25 | 147.17 | 9.01 | 0.412 |
| 176 | Solapur | 78 | 129.72 | 158.66 | 12.24 | 0.585 |
| 2494 | Pune(Pimpri) | 90 | 146.43 | 181.42 | 10.95 | 0.401 |
| 575 | Manmad | 77 | 147.27 | 195.44 | 13.49 | 0.559 |
| 4752 | Pune(Moshi) | 90 | 158.1 | 229.76 | 15.74 | 0.681 |
| 168 | Nasik | 78 | 180.3 | 225.21 | 18.32 | 0.608 |
| 4751 | Pune(Manjri) | 90 | 256.98 | 518.3 | 22.47 | 0.779 |
| 172 | Pune | 90 | 271.98 | 962.38 | 15.76 | 1.206 |

## Baseline Definitions

- `seasonal_naive_7d`: predicts the 7-day-ahead price as the current as-of date modal price. This is an explicit naive benchmark, not a feature used by Ridge.
- `moving_average_7d`: predicts using the past-only 7-day rolling mean.
- `moving_average_30d`: predicts using the past-only 30-day rolling mean.
- `ridge`: linear baseline using lag, rolling, return, calendar, market, and district features. It excludes current-day modal price and future target columns.

## Metric Notes

- MAE/RMSE are INR per quintal.
- sMAPE is percentage error.
- MASE is scaled by the average absolute 7-day seasonal difference in the training period.
- Splits are date-based only; no random split is used.