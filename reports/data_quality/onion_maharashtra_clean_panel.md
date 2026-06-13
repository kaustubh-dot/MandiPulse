# Clean Onion/Maharashtra Panel

## Summary

- raw_selected_rows: 24192
- invalid_rows_dropped: 0
- duplicate_market_date_rows: 3127
- panel_rows: 31950
- observed_rows: 22627
- imputed_rows: 6031
- missing_long_gap_rows: 3292
- market_count: 15
- date_min: 2020-01-01
- date_max: 2025-10-30

## Market Coverage

| market_id | market_name | district | panel_days | observed_days | imputed_days | missing_long_gap_days | first_date | last_date | observed_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2494 | Pune(Pimpri) | pune | 2130 | 1656 | 215 | 259 | 2020-01-01 | 2025-10-30 | 77.75 |
| 2495 | Pune(Khadiki) | pune | 2130 | 1620 | 330 | 180 | 2020-01-01 | 2025-10-30 | 76.06 |
| 172 | Pune | pune | 2130 | 1587 | 406 | 137 | 2020-01-01 | 2025-10-30 | 74.51 |
| 581 | Chattrapati Sambhajinagar | aurangabad | 2130 | 1554 | 428 | 148 | 2020-01-01 | 2025-10-30 | 72.96 |
| 4752 | Pune(Moshi) | pune | 2130 | 1529 | 390 | 211 | 2020-01-01 | 2025-10-30 | 71.78 |
| 160 | Kolhapur | kolhapur | 2130 | 1527 | 474 | 129 | 2020-01-01 | 2025-10-30 | 71.69 |
| 4751 | Pune(Manjri) | pune | 2130 | 1527 | 315 | 288 | 2020-01-01 | 2025-10-30 | 71.69 |
| 170 | Pimpalgaon | nashik | 2130 | 1521 | 365 | 244 | 2020-01-01 | 2025-10-30 | 71.41 |
| 3108 | Vashi New Mumbai | mumbai | 2130 | 1516 | 445 | 169 | 2020-01-01 | 2025-10-30 | 71.17 |
| 169 | Lasalgaon | nashik | 2130 | 1454 | 402 | 274 | 2020-01-01 | 2025-10-30 | 68.26 |
| 575 | Manmad | nashik | 2130 | 1444 | 413 | 273 | 2020-01-01 | 2025-10-30 | 67.79 |
| 1462 | Satara | satara | 2130 | 1440 | 463 | 227 | 2020-01-01 | 2025-10-30 | 67.61 |
| 176 | Solapur | solapur | 2130 | 1420 | 490 | 220 | 2020-01-01 | 2025-10-30 | 66.67 |
| 168 | Nasik | nashik | 2130 | 1416 | 468 | 246 | 2020-01-01 | 2025-10-30 | 66.48 |
| 2484 | Lasalgaon(Niphad) | nashik | 2130 | 1416 | 427 | 287 | 2020-01-01 | 2025-10-30 | 66.48 |

## Cleaning Rules

- Dropped rows with non-positive modal price or invalid min/modal/max order.
- Aggregated duplicate market-date rows using min(min), max(max), median(modal).
- Built a daily panel for the selected MVP mandis.
- Forward-filled only internal gaps of 3 days or less.
- Kept longer missing gaps as `missing_long_gap` rows.