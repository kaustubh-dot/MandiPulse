# Onion/Maharashtra 7-Day LightGBM Metrics

## Summary

- Feature table: `data\processed\onion_maharashtra\feature_table_7d.csv`
- Metrics CSV: `artifacts\metrics\lightgbm_metrics_7d.csv`
- Prediction rows: `artifacts\predictions\lightgbm_predictions_7d.csv`
- Row filter: `all`
- Train rows: 17,423
- Validation rows: 1,307
- Test rows: 1,204
- Markets: 15
- Best test model by MAE: `moving_average_7d` (139.57 INR/quintal)
- LightGBM test MAE: 183.54 INR/quintal
- Moving-average 7d test MAE: 139.57 INR/quintal
- LightGBM MAE delta vs moving_average_7d: 43.97 INR/quintal

## Overall Metrics

| model | split | rows | mae | rmse | smape_pct | mase |
| --- | --- | --- | --- | --- | --- | --- |
| moving_average_7d | test | 1204 | 139.57 | 332.41 | 11.94 | 0.531 |
| moving_average_30d | test | 1204 | 142.85 | 319.9 | 12.27 | 0.544 |
| seasonal_naive_7d | test | 1204 | 146.26 | 424.18 | 12.2 | 0.557 |
| lightgbm | test | 1204 | 183.54 | 346.55 | 15.41 | 0.699 |
| ridge | test | 1204 | 224.43 | 369.07 | 18.72 | 0.855 |
| moving_average_7d | validation | 1307 | 125.06 | 329.26 | 10.48 | 0.476 |
| lightgbm | validation | 1307 | 127.76 | 315.5 | 10.6 | 0.486 |
| seasonal_naive_7d | validation | 1307 | 135.09 | 422.34 | 11.19 | 0.514 |
| ridge | validation | 1307 | 138.16 | 326.94 | 11.5 | 0.526 |
| moving_average_30d | validation | 1307 | 154.31 | 330.46 | 13.11 | 0.588 |

## LightGBM Test Metrics By Mandi

| market_id | market_name | rows | mae | rmse | smape_pct | mase |
| --- | --- | --- | --- | --- | --- | --- |
| 2495 | Pune(Khadiki) | 90 | 142.24 | 176.04 | 13.0 | 0.681 |
| 581 | Chattrapati Sambhajinagar | 81 | 149.22 | 185.89 | 17.52 | 0.566 |
| 170 | Pimpalgaon | 78 | 149.9 | 183.38 | 11.03 | 0.595 |
| 176 | Solapur | 78 | 152.32 | 190.29 | 13.72 | 0.684 |
| 3108 | Vashi New Mumbai | 78 | 157.63 | 178.1 | 12.02 | 0.547 |
| 1462 | Satara | 80 | 160.55 | 206.79 | 10.41 | 0.616 |
| 169 | Lasalgaon | 36 | 165.49 | 191.69 | 12.55 | 0.662 |
| 160 | Kolhapur | 90 | 174.89 | 202.51 | 16.76 | 0.813 |
| 4752 | Pune(Moshi) | 90 | 174.94 | 249.29 | 16.85 | 0.75 |
| 2494 | Pune(Pimpri) | 90 | 182.67 | 245.68 | 13.11 | 0.499 |
| 575 | Manmad | 77 | 188.26 | 253.47 | 16.45 | 0.715 |
| 2484 | Lasalgaon(Niphad) | 78 | 192.37 | 219.12 | 14.77 | 0.676 |
| 172 | Pune | 90 | 216.81 | 910.98 | 12.79 | 0.957 |
| 168 | Nasik | 78 | 253.27 | 301.25 | 24.03 | 0.85 |
| 4751 | Pune(Manjri) | 90 | 274.84 | 484.93 | 24.1 | 0.831 |

## Interview Note

- If LightGBM beats the moving average baseline, the nonlinear model earns its place in the MVP loop.
- If it does not, the honest story is still strong: the baseline is tough, and the next lever is target reformulation or richer exogenous features rather than pretending the booster won.