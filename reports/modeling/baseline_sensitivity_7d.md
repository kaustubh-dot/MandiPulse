# Onion/Maharashtra 7-Day Baseline Sensitivity (Observed-Only vs All)

## Summary

- Feature table: `data\processed\onion_maharashtra\feature_table_7d.csv`

## All rows (imputed + observed)

| model | split | rows | mae | rmse | smape_pct | mase |
| --- | --- | --- | --- | --- | --- | --- |
| moving_average_7d | test | 1204 | 139.57 | 332.41 | 11.94 | 0.531 |
| moving_average_30d | test | 1204 | 142.85 | 319.9 | 12.27 | 0.544 |
| seasonal_naive_7d | test | 1204 | 146.26 | 424.18 | 12.2 | 0.557 |
| ridge | test | 1204 | 224.43 | 369.08 | 18.72 | 0.854 |
| moving_average_7d | validation | 1272 | 126.07 | 329.37 | 10.73 | 0.48 |
| ridge | validation | 1272 | 135.98 | 329.69 | 11.47 | 0.517 |
| seasonal_naive_7d | validation | 1272 | 138.54 | 428.24 | 11.59 | 0.527 |
| moving_average_30d | validation | 1272 | 159.54 | 336.88 | 13.73 | 0.607 |

## Observed-only rows

| model | split | rows | mae | rmse | smape_pct | mase |
| --- | --- | --- | --- | --- | --- | --- |
| moving_average_7d | test | 792 | 133.61 | 246.89 | 11.73 | 0.435 |
| moving_average_30d | test | 792 | 136.76 | 228.08 | 12.08 | 0.446 |
| seasonal_naive_7d | test | 792 | 146.07 | 411.66 | 12.22 | 0.476 |
| ridge | test | 792 | 228.94 | 306.77 | 19.31 | 0.746 |
| moving_average_7d | validation | 959 | 129.62 | 365.37 | 10.75 | 0.422 |
| ridge | validation | 959 | 140.1 | 365.85 | 11.48 | 0.456 |
| seasonal_naive_7d | validation | 959 | 143.48 | 482.69 | 11.57 | 0.467 |
| moving_average_30d | validation | 959 | 163.63 | 371.93 | 13.78 | 0.533 |

## Notes

- If observed-only MAE differs substantially from all-rows MAE, imputation is affecting scores.
- This check isolates the forward-fill from modeling quality.