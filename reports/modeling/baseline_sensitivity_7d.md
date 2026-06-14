# Onion/Maharashtra 7-Day Baseline Sensitivity (Observed-Only vs All)

## Summary

- Feature table: `data\processed\onion_maharashtra\feature_table_7d.csv`

## All rows (imputed + observed)

| model | split | rows | mae | rmse | smape_pct | mase |
| --- | --- | --- | --- | --- | --- | --- |
| moving_average_7d | test | 1204 | 139.57 | 332.41 | 11.94 | 0.531 |
| moving_average_30d | test | 1204 | 142.85 | 319.9 | 12.27 | 0.544 |
| seasonal_naive_7d | test | 1204 | 146.26 | 424.18 | 12.2 | 0.557 |
| ridge | test | 1204 | 224.43 | 369.07 | 18.72 | 0.855 |
| moving_average_7d | validation | 1307 | 125.06 | 329.26 | 10.48 | 0.476 |
| seasonal_naive_7d | validation | 1307 | 135.09 | 422.34 | 11.19 | 0.514 |
| ridge | validation | 1307 | 138.16 | 326.94 | 11.5 | 0.526 |
| moving_average_30d | validation | 1307 | 154.31 | 330.46 | 13.11 | 0.588 |

## Observed-only rows

| model | split | rows | mae | rmse | smape_pct | mase |
| --- | --- | --- | --- | --- | --- | --- |
| moving_average_7d | test | 792 | 133.61 | 246.89 | 11.73 | 0.435 |
| moving_average_30d | test | 792 | 136.76 | 228.08 | 12.08 | 0.446 |
| seasonal_naive_7d | test | 792 | 146.07 | 411.66 | 12.22 | 0.476 |
| ridge | test | 792 | 228.93 | 306.76 | 19.31 | 0.746 |
| moving_average_7d | validation | 985 | 127.46 | 362.81 | 10.45 | 0.415 |
| seasonal_naive_7d | validation | 985 | 139.77 | 475.9 | 11.19 | 0.456 |
| ridge | validation | 985 | 141.44 | 361.98 | 11.49 | 0.461 |
| moving_average_30d | validation | 985 | 158.7 | 365.46 | 13.22 | 0.517 |

## Notes

- If observed-only MAE differs substantially from all-rows MAE, imputation is affecting scores.
- This check isolates the forward-fill from modeling quality.