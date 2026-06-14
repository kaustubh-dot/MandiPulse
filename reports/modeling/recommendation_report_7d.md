# Onion/Maharashtra 7-Day Recommendation Report

## Summary

- Farmer latitude: 19.9975
- Farmer longitude: 73.78981
- Quantity: 100.0 quintals
- Candidate state: `maharashtra`
- Road distance factor: 1.3 (from configs/recommendation.yaml)
- Transport cost: 4.0 INR/km/quintal (from configs/recommendation.yaml)
- Uncertainty penalty weight: 0.3 (from configs/recommendation.yaml)
- Risk thresholds: low ≤ 10%, high ≥ 25% (from configs/recommendation.yaml)
- Production forecast model: `moving_average_7d` via latest `forecast_outputs_7d.csv` artifact

## Top 3 Ranked Mandis

| rank | mandi | district_name | forecast_price_inr_qtl | estimated_transport_cost_inr_qtl | expected_net_price_inr_qtl | uncertainty_penalty_inr_qtl | risk_adjusted_score | risk_level | road_distance_km |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Pimpalgaon | Nashik | 1439.29 | 143.57 | 1295.72 | 150.96 | 1144.75 | high | 35.89 |
| 2 | Lasalgaon | Nashik | 1275.86 | 259.91 | 1015.95 | 150.96 | 864.99 | high | 64.98 |
| 3 | Lasalgaon(Niphad) | Nashik | 1045.71 | 49.92 | 995.8 | 150.96 | 844.83 | high | 12.48 |

## Notes

- Distance is haversine distance multiplied by road_distance_factor from configs/recommendation.yaml.
- Transport cost is INR per km per quintal (load-size-independent), consistent with the config unit.
- This is decision support, not a guaranteed-profit recommendation.