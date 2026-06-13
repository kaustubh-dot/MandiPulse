# Onion/Maharashtra 7-Day Feature Table

## Summary

- Panel rows: 31,950
- Trainable rows: 20,004
- Markets: 15
- Date range: 2020-01-01 to 2025-10-30
- Target: `target_price_t_plus_7`
- Leakage rule: lag and rolling features are shifted; rolling windows exclude current row.

## Trainable Rows By Market

| market_id | market_name | panel_rows | trainable_rows | first_date | last_date | trainable_pct |
| --- | --- | --- | --- | --- | --- | --- |
| 4752 | Pune(Moshi) | 2130 | 1632 | 2020-01-01 00:00:00 | 2025-10-30 00:00:00 | 76.62 |
| 172 | Pune | 2130 | 1597 | 2020-01-01 00:00:00 | 2025-10-30 00:00:00 | 74.98 |
| 160 | Kolhapur | 2130 | 1550 | 2020-01-01 00:00:00 | 2025-10-30 00:00:00 | 72.77 |
| 581 | Chattrapati Sambhajinagar | 2130 | 1540 | 2020-01-01 00:00:00 | 2025-10-30 00:00:00 | 72.3 |
| 2495 | Pune(Khadiki) | 2130 | 1493 | 2020-01-01 00:00:00 | 2025-10-30 00:00:00 | 70.09 |
| 2494 | Pune(Pimpri) | 2130 | 1460 | 2020-01-01 00:00:00 | 2025-10-30 00:00:00 | 68.54 |
| 4751 | Pune(Manjri) | 2130 | 1384 | 2020-01-01 00:00:00 | 2025-10-30 00:00:00 | 64.98 |
| 3108 | Vashi New Mumbai | 2130 | 1339 | 2020-01-01 00:00:00 | 2025-10-30 00:00:00 | 62.86 |
| 176 | Solapur | 2130 | 1223 | 2020-01-01 00:00:00 | 2025-10-30 00:00:00 | 57.42 |
| 170 | Pimpalgaon | 2130 | 1209 | 2020-01-01 00:00:00 | 2025-10-30 00:00:00 | 56.76 |
| 575 | Manmad | 2130 | 1185 | 2020-01-01 00:00:00 | 2025-10-30 00:00:00 | 55.63 |
| 1462 | Satara | 2130 | 1182 | 2020-01-01 00:00:00 | 2025-10-30 00:00:00 | 55.49 |
| 168 | Nasik | 2130 | 1095 | 2020-01-01 00:00:00 | 2025-10-30 00:00:00 | 51.41 |
| 169 | Lasalgaon | 2130 | 1061 | 2020-01-01 00:00:00 | 2025-10-30 00:00:00 | 49.81 |
| 2484 | Lasalgaon(Niphad) | 2130 | 1054 | 2020-01-01 00:00:00 | 2025-10-30 00:00:00 | 49.48 |

## Notes

- Rows with missing lag/rolling features or missing target are not trainable.
- Current-day modal price is retained for diagnostics but should not be used as a model feature.
- Use `feature_row_valid == True` for baseline/model training.