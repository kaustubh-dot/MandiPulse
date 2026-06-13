# Onion/Maharashtra Data Profile

## Dataset

- Input: `data\raw\ceda\onion_maharashtra\onion_maharashtra_prices_raw.csv`
- Rows: 86,052
- Markets: 125
- Districts: 25
- Date range: 2020-01-01 to 2025-10-30
- Invalid price rows: 0
- Duplicate market-date rows: 13,379

## Top Markets By Coverage

| market_id | market_name | district_id | district_name | rows | valid_rows | active_days | first_date | last_date | median_modal_price | min_modal_price | max_modal_price | valid_row_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2494 | Pune(Pimpri) | 521 | Pune | 1656 | 1656 | 1656 | 2020-01-01 | 2025-10-30 | 1500.0 | 350.0 | 6400.0 | 100.0 |
| 2495 | Pune(Khadiki) | 521 | Pune | 1620 | 1620 | 1620 | 2020-01-01 | 2025-10-30 | 1300.0 | 500.0 | 4600.0 | 100.0 |
| 172 | Pune | 521 | Pune | 1587 | 1587 | 1587 | 2020-01-01 | 2025-10-30 | 1300.0 | 500.0 | 11000.0 | 100.0 |
| 581 | Chattrapati Sambhajinagar | 515 | Aurangabad | 1554 | 1554 | 1554 | 2020-01-02 | 2025-10-30 | 1000.0 | 143.0 | 6000.0 | 100.0 |
| 4752 | Pune(Moshi) | 521 | Pune | 1529 | 1529 | 1529 | 2020-05-18 | 2025-10-30 | 1000.0 | 350.0 | 6200.0 | 100.0 |
| 160 | Kolhapur | 530 | Kolhapur | 1527 | 1527 | 1527 | 2020-01-01 | 2025-10-30 | 1400.0 | 600.0 | 13000.0 | 100.0 |
| 4751 | Pune(Manjri) | 521 | Pune | 1527 | 1527 | 1527 | 2020-05-15 | 2025-10-30 | 1300.0 | 500.0 | 5700.0 | 100.0 |
| 170 | Pimpalgaon | 516 | Nashik | 1880 | 1880 | 1521 | 2020-01-01 | 2025-10-30 | 1600.0 | 450.0 | 6180.0 | 100.0 |
| 3108 | Vashi New Mumbai | 519 | Mumbai | 1516 | 1516 | 1516 | 2020-01-01 | 2025-10-30 | 1650.0 | 750.0 | 6000.0 | 100.0 |
| 169 | Lasalgaon | 516 | Nashik | 1854 | 1854 | 1454 | 2020-01-01 | 2025-10-30 | 1620.0 | 300.0 | 5851.0 | 100.0 |
| 575 | Manmad | 516 | Nashik | 1783 | 1783 | 1444 | 2020-01-01 | 2025-10-30 | 1500.0 | 100.0 | 5300.0 | 100.0 |
| 1462 | Satara | 527 | Satara | 1440 | 1440 | 1440 | 2020-01-02 | 2025-10-29 | 1500.0 | 600.0 | 5000.0 | 100.0 |
| 176 | Solapur | 526 | Solapur | 1499 | 1499 | 1420 | 2020-01-01 | 2025-10-30 | 1200.0 | 300.0 | 4200.0 | 100.0 |
| 2484 | Lasalgaon(Niphad) | 516 | Nashik | 1654 | 1654 | 1416 | 2020-01-01 | 2025-10-30 | 1580.0 | 441.0 | 5800.0 | 100.0 |
| 168 | Nasik | 516 | Nashik | 1566 | 1566 | 1416 | 2020-01-01 | 2025-10-30 | 1500.0 | 300.0 | 6000.0 | 100.0 |
| 4750 | Lasalgaon(Vinchur) | 516 | Nashik | 1603 | 1603 | 1399 | 2020-05-15 | 2025-10-30 | 1580.0 | 500.0 | 5725.0 | 100.0 |
| 2488 | Pimpalgaon Baswant(Saykheda) | 516 | Nashik | 1535 | 1535 | 1360 | 2020-01-01 | 2025-10-30 | 1425.0 | 400.0 | 5700.0 | 100.0 |
| 1459 | Karad | 527 | Satara | 1360 | 1360 | 1360 | 2020-01-01 | 2025-10-29 | 2000.0 | 800.0 | 15000.0 | 100.0 |
| 1471 | Vaijpur | 515 | Aurangabad | 1405 | 1405 | 1349 | 2020-01-01 | 2025-10-30 | 1385.0 | 425.0 | 5000.0 | 100.0 |
| 574 | Chandvad | 516 | Nashik | 1554 | 1554 | 1348 | 2020-01-01 | 2025-10-30 | 1510.0 | 200.0 | 6000.0 | 100.0 |

## Notes

- Select the first 10-15 markets only after checking missingness and geographic spread.
- Do not forward-fill gaps longer than 3 consecutive reporting days.
- Add an `is_imputed` flag if short gaps are filled later.