# Onion/Maharashtra 7-Day LightGBM Metrics

## Summary

- Feature table: `data\processed\onion_maharashtra\feature_table_7d.csv`
- Metrics CSV: `artifacts\metrics\lightgbm_metrics_7d.csv`
- Prediction rows: `artifacts\predictions\lightgbm_predictions_7d.csv`
- Row filter: `all`
- Train rows: 17,353
- Validation rows: 1,272
- Test rows: 1,204
- Markets: 15
- Best test model by MAE: `moving_average_7d` (139.57 INR/quintal)
- LightGBM (level) test MAE: 188.2 INR/quintal
- Moving-average 7d test MAE: 139.57 INR/quintal
- LightGBM (level) MAE delta vs moving_average_7d: 48.63 INR/quintal
- LightGBM (residual) test MAE: 195.63 INR/quintal (delta vs moving_average_7d: +56.06 INR/quintal)

## Overall Metrics

| model | split | rows | mae | rmse | smape_pct | mase |
| --- | --- | --- | --- | --- | --- | --- |
| moving_average_7d | test | 1204 | 139.57 | 332.41 | 11.94 | 0.531 |
| moving_average_30d | test | 1204 | 142.85 | 319.9 | 12.27 | 0.544 |
| seasonal_naive_7d | test | 1204 | 146.26 | 424.18 | 12.2 | 0.557 |
| lightgbm | test | 1204 | 188.2 | 350.67 | 15.78 | 0.716 |
| lightgbm_residual | test | 1204 | 195.63 | 354.96 | 16.35 | 0.744 |
| ridge | test | 1204 | 224.43 | 369.08 | 18.72 | 0.854 |
| lightgbm_residual | validation | 1272 | 125.86 | 318.39 | 10.56 | 0.479 |
| moving_average_7d | validation | 1272 | 126.07 | 329.37 | 10.73 | 0.48 |
| lightgbm | validation | 1272 | 129.42 | 319.48 | 10.83 | 0.493 |
| ridge | validation | 1272 | 135.98 | 329.69 | 11.47 | 0.517 |
| seasonal_naive_7d | validation | 1272 | 138.54 | 428.24 | 11.59 | 0.527 |
| moving_average_30d | validation | 1272 | 159.54 | 336.88 | 13.73 | 0.607 |

## LightGBM (Level) Test Metrics By Mandi

| market_id | market_name | rows | mae | rmse | smape_pct | mase |
| --- | --- | --- | --- | --- | --- | --- |
| 2495 | Pune(Khadiki) | 90 | 138.09 | 172.32 | 12.62 | 0.661 |
| 170 | Pimpalgaon | 78 | 153.45 | 189.49 | 11.23 | 0.609 |
| 3108 | Vashi New Mumbai | 78 | 153.55 | 170.74 | 11.77 | 0.531 |
| 1462 | Satara | 80 | 155.21 | 205.31 | 10.07 | 0.603 |
| 176 | Solapur | 78 | 156.83 | 196.12 | 14.08 | 0.705 |
| 581 | Chattrapati Sambhajinagar | 81 | 169.12 | 209.73 | 19.49 | 0.64 |
| 160 | Kolhapur | 90 | 171.95 | 203.91 | 16.44 | 0.799 |
| 169 | Lasalgaon | 36 | 180.14 | 212.86 | 13.55 | 0.72 |
| 4752 | Pune(Moshi) | 90 | 181.48 | 254.15 | 17.5 | 0.776 |
| 2494 | Pune(Pimpri) | 90 | 192.51 | 256.56 | 13.78 | 0.524 |
| 2484 | Lasalgaon(Niphad) | 78 | 194.15 | 222.44 | 14.85 | 0.682 |
| 172 | Pune | 90 | 216.46 | 908.7 | 12.86 | 0.953 |
| 575 | Manmad | 77 | 217.0 | 284.17 | 18.43 | 0.824 |
| 168 | Nasik | 78 | 259.82 | 306.83 | 24.45 | 0.869 |
| 4751 | Pune(Manjri) | 90 | 273.83 | 489.09 | 24.01 | 0.827 |

## Decision: Residual-Target Reformulation (M3-04)

- Residual-LightGBM test MAE: **195.63 INR/quintal**
- Moving-average baseline test MAE: **139.57 INR/quintal**
- Delta: **+56.06 INR/quintal** (baseline wins)

**Promotion: NO.** The residual-target LightGBM does not beat the moving-average baseline on the held-out test split. The baseline remains the shipped forecaster.
This is an honest outcome: a smaller residual-target variance reduces overfitting but the model has not found exploitable signal beyond the baseline.
Next lever: richer exogenous features (arrivals, weather) or a different model family.

## Interview Note

- Level-LightGBM (absolute target): overfits to training price levels; eats distribution shift on test.
- Residual-LightGBM (target - rolling_mean_7): isolates what the baseline misses; can only add value where real signal exists.
- See Decision section above for the promotion outcome of the residual experiment.
- If neither model beats the baseline, the honest story remains strong: the baseline is tough, and the project reports that transparently.