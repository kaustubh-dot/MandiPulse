# Onion/Maharashtra 7-Day Recommendation Backtest

## Method

- Forecast model: `moving_average_7d` (moving-average baseline, the shipped MVP forecaster)
- Backtest split: `test`
- Interval calibration: lower residual -210.36, upper residual 292.86 INR/quintal
- Leakage safeguard: predictions come from the leakage-safe baseline predictions artifact
  (`baseline_predictions_7d.csv`), which uses only information up to each as-of date.
- Realized price: modal price from the clean panel at as-of date + 7 days
  (±2-day tolerance; observed rows preferred over imputed).
- Farmer location: (19.9975, 73.78981) — Nashik region
- Road distance factor: 1.3
- Transport cost: 4.0 INR/km/quintal
- Uncertainty penalty weight: 0.3

## Summary Metrics

| metric | value |
| --- | --- |
| Regret@1 (mean) | 296.3 INR/qtl |
| Regret@1 (median) | 0.0 INR/qtl |
| Optimal rate@1 (top-1 captured best mandi) | 58.9% |
| Beats nearest-mandi@1 | 78.8% |
| Regret@3 (mean) | 191.0 INR/qtl |
| Regret@3 (median) | 0.0 INR/qtl |
| Optimal rate@3 (top-3 captured best mandi) | 87.8% |
| Beats nearest-mandi@3 | 89.4% |
| Nearest-mandi baseline regret (mean) | 370.1 INR/qtl |
| Nearest-mandi baseline regret (median) | 225.1 INR/qtl |
| As-of dates evaluated | 90 |
| Date range | 2025-07-26 → 2025-10-23 |
| Mandi-dates dropped (no realized price) | 0 |

## Verdict

The model's top-1 recommendation achieves **mean regret@1 of 296.3 INR/qtl**, which is better than the nearest-mandi baseline (370.1 INR/qtl). The ranking earns its place over the naive strategy.

## Assumptions and Caveats

- Realized-price tolerance: ±2 days. Observed rows preferred; imputed used as fallback.
- Transport cost is haversine × road_factor × cost_per_km — same formula as the recommendation engine.
- This is offline evaluation on historical data; past regret does not guarantee future performance.
- This is decision support, not a guaranteed-profit recommendation.