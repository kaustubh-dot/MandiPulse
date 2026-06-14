# Onion/Maharashtra 7-Day Forecast Intervals

## Summary

- Feature table: `data\processed\onion_maharashtra\feature_table_7d.csv`
- Production forecast model for MVP intervals: `moving_average_7d`
- Row filter used for calibration/evaluation: `all`
- Confidence level: 0.90
- Validation residual lower adjustment: -210.36 INR/quintal
- Validation residual upper adjustment: 292.86 INR/quintal

## Empirical Interval Performance

| split | coverage_type | rows | empirical_coverage | avg_interval_width_inr_qtl | median_interval_width_inr_qtl |
| --- | --- | --- | --- | --- | --- |
| test | coverage (out-of-sample) | 1204 | 0.8671 | 503.21 | 503.21 |
| validation | coverage (in-sample calibration) | 1272 | 0.9002 | 503.21 | 503.21 |

## Latest Forecast Output Preview

| mandi | as_of_date | forecast_price_inr_qtl | lower_bound_inr_qtl | upper_bound_inr_qtl |
| --- | --- | --- | --- | --- |
| Chattrapati Sambhajinagar | 2025-10-30 | 950.0 | 739.642857142857 | 1242.857142857143 |
| Kolhapur | 2025-10-30 | 928.5714285714286 | 718.2142857142856 | 1221.4285714285716 |
| Lasalgaon | 2025-10-30 | 1275.857142857143 | 1065.5 | 1568.7142857142858 |
| Lasalgaon(Niphad) | 2025-10-18 | 1045.7142857142858 | 835.3571428571428 | 1338.5714285714287 |
| Manmad | 2025-10-17 | 964.2857142857144 | 753.9285714285714 | 1257.1428571428573 |
| Nasik | 2025-10-18 | 794.4285714285714 | 584.0714285714284 | 1087.2857142857142 |
| Pimpalgaon | 2025-10-30 | 1439.2857142857142 | 1228.928571428571 | 1732.142857142857 |
| Pune | 2025-10-30 | 1128.571428571429 | 918.2142857142859 | 1421.4285714285718 |
| Pune(Khadiki) | 2025-10-30 | 842.8571428571429 | 632.4999999999999 | 1135.7142857142858 |
| Pune(Manjri) | 2025-10-30 | 1142.857142857143 | 932.4999999999999 | 1435.7142857142858 |
| Pune(Moshi) | 2025-10-30 | 992.8571428571428 | 782.4999999999998 | 1285.7142857142858 |
| Pune(Pimpri) | 2025-10-30 | 1392.857142857143 | 1182.5 | 1685.7142857142858 |
| Satara | 2025-10-19 | 1407.142857142857 | 1196.7857142857142 | 1700.0 |
| Solapur | 2025-10-18 | 992.8571428571428 | 782.4999999999998 | 1285.7142857142858 |
| Vashi New Mumbai | 2025-10-30 | 1414.2857142857142 | 1203.928571428571 | 1707.142857142857 |

## Notes

- Intervals are empirical residual intervals calibrated on the validation split and evaluated on the held-out test split.
- This keeps the uncertainty story aligned with the current MVP decision to ship the strongest honest baseline first.
- Bounds are not guarantees; the dashboard should present them as uncertainty estimates with measured coverage.