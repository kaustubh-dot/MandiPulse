# Onion/Maharashtra 7-Day Forecast Intervals

## Summary

- Feature table: `data\processed\onion_maharashtra\feature_table_7d.csv`
- Production forecast model for MVP intervals: `moving_average_7d`
- Row filter used for calibration/evaluation: `all`
- Confidence level: 0.90
- Validation residual lower adjustment: -207.14 INR/quintal
- Validation residual upper adjustment: 292.86 INR/quintal

## Empirical Interval Performance

| split | rows | empirical_coverage | avg_interval_width_inr_qtl | median_interval_width_inr_qtl |
| --- | --- | --- | --- | --- |
| test | 1204 | 0.8663 | 500.0 | 500.0 |
| validation | 1307 | 0.9036 | 500.0 | 500.0 |

## Latest Forecast Output Preview

| mandi | as_of_date | forecast_price_inr_qtl | lower_bound_inr_qtl | upper_bound_inr_qtl |
| --- | --- | --- | --- | --- |
| chattrapati_sambhajinagar | 2025-10-18 | 664.2857142857143 | 457.1428571428572 | 957.1428571428572 |
| kolhapur | 2025-10-30 | 928.5714285714286 | 721.4285714285714 | 1221.4285714285716 |
| lasalgaon | 2025-10-16 | 1075.0 | 867.8571428571429 | 1367.857142857143 |
| lasalgaonniphad | 2025-10-18 | 1045.7142857142858 | 838.5714285714287 | 1338.5714285714287 |
| manmad | 2025-10-17 | 964.2857142857144 | 757.1428571428573 | 1257.1428571428573 |
| nasik | 2025-10-18 | 794.4285714285714 | 587.2857142857143 | 1087.2857142857142 |
| pimpalgaon | 2025-10-17 | 1114.2857142857142 | 907.1428571428571 | 1407.142857142857 |
| pune | 2025-10-30 | 1128.571428571429 | 921.4285714285718 | 1421.4285714285718 |
| punekhadiki | 2025-10-30 | 842.8571428571429 | 635.7142857142858 | 1135.7142857142858 |
| punemanjri | 2025-10-30 | 1142.857142857143 | 935.7142857142858 | 1435.7142857142858 |
| punemoshi | 2025-10-30 | 992.8571428571428 | 785.7142857142857 | 1285.7142857142858 |
| punepimpri | 2025-10-30 | 1392.857142857143 | 1185.7142857142858 | 1685.7142857142858 |
| satara | 2025-10-19 | 1407.142857142857 | 1200.0 | 1700.0 |
| solapur | 2025-10-18 | 992.8571428571428 | 785.7142857142857 | 1285.7142857142858 |
| vashi_new_mumbai | 2025-10-17 | 1207.142857142857 | 1000.0 | 1500.0 |

## Notes

- Intervals are empirical residual intervals calibrated on the validation split and evaluated on the held-out test split.
- This keeps the uncertainty story aligned with the current MVP decision to ship the strongest honest baseline first.
- Bounds are not guarantees; the dashboard should present them as uncertainty estimates with measured coverage.