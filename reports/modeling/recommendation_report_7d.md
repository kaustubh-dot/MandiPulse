# Onion/Maharashtra 7-Day Recommendation Report

## Summary

- Farmer latitude: 19.9975
- Farmer longitude: 73.78981
- Quantity: 100.0 quintals
- Candidate state: `maharashtra`
- Road factor: 1.25
- Transport cost assumption: 18.0 INR/km total, divided by quantity
- Uncertainty penalty fraction: 0.25 of interval width
- Production forecast model: `moving_average_7d` via latest `forecast_outputs_7d.csv` artifact

## Top 3 Ranked Mandis

| rank | mandi | district_name | forecast_price_inr_qtl | estimated_transport_cost_inr_qtl | expected_net_price_inr_qtl | uncertainty_penalty_inr_qtl | risk_adjusted_score | risk_level | road_distance_km |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Pune(Pimpri) | Pune | 1392.86 | 34.63 | 1358.23 | 125.0 | 1233.23 | medium | 192.4 |
| 2 | Satara | Satara | 1407.14 | 58.01 | 1349.14 | 125.0 | 1224.14 | medium | 322.26 |
| 3 | Vashi New Mumbai | Mumbai | 1207.14 | 29.41 | 1177.73 | 125.0 | 1052.73 | high | 163.39 |

## Notes

- Distance is haversine distance multiplied by a simple road-factor approximation.
- Transport cost is intentionally transparent and easy to tune for demo sensitivity checks.
- This is decision support, not a guaranteed-profit recommendation.