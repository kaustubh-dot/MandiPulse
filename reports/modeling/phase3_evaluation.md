# Phase 3 - Defensible ML Engineering Evidence

## Scope and population policy

- Frozen scope: Onion/Maharashtra, 15 mandis, 7-day horizon, snapshot through 2025-10-30.
- Primary metric population: rows whose as-of value and t+7 target are observed.
- Imputed targets are counted and excluded from primary metrics; unavailable targets are reported separately.
- Rolling origins are evaluated before an untouched final holdout. The final holdout is evaluated last.
- This is an internal evaluation evidence export; the public web/API v1 schemas remain unchanged.

## Provenance

- Evidence provenance id: 1465d5ede864fdd562770dcabb5e27225184ab429b9064bcdfef21d80140c95d
- Source snapshot: data/processed/onion_maharashtra/clean_mandi_prices.csv (6c4396e3487ff01028b07b3569e37eb80421d6e5d5385458af6a161b9ee36a4f)
- Feature snapshot: data/processed/onion_maharashtra/feature_table_7d.csv (f1c20950335ea17aaf439b6e6f0cc6eb831c5ddb9c77beb00ee7b78ee3ccc1a8)
- Coordinate source: data/external/mvp_mandis.csv (effd28c137a42fa26c7934f07e28baa040ecc7f97bb05e3176d1f6140fe4a279)
- Transport config: {'road_distance_factor': 1.3, 'base_cost_per_km_per_quintal': 4.0, 'scenario_multipliers': [0.8, 1.0, 1.2]}

## Rolling origins

| origin_id | origin_date | train_start | train_end | validation_start | validation_end | test_start | test_end | train | validation | test | metrics | interval | provenance_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rolling_1 | 2025-07-11 | 2020-01-31 | 2025-05-22 | 2025-05-29 | 2025-06-27 | 2025-07-05 | 2025-07-11 | {'rows': 17840, 'observed_target_rows': 12968, 'imputed_target_rows': 3554, 'unavailable_target_rows': 1318} | {'rows': 450, 'observed_target_rows': 352, 'imputed_target_rows': 80, 'unavailable_target_rows': 18} | {'rows': 105, 'observed_target_rows': 88, 'imputed_target_rows': 14, 'unavailable_target_rows': 3} | [{'model': 'moving_average_7d', 'split': 'test', 'rows': 88, 'mae': 207.05, 'rmse': 1053.94, 'smape_pct': 9.85, 'mase': None, 'population': 'observed_targets', 'observed_target_rows': 88, 'imputed_target_rows_excluded': 14, 'unavailable_target_rows': 3, 'provenance_id': '1465d5ede864fdd562770dcabb5e27225184ab429b9064bcdfef21d80140c95d'}] | {'origin_id': 'rolling_1', 'method': 'split_conformal', 'lower_residual': -264.28571428571445, 'upper_residual': 264.28571428571445, 'calibration_rows': 352, 'provenance_id': '1465d5ede864fdd562770dcabb5e27225184ab429b9064bcdfef21d80140c95d'} | 1465d5ede864fdd562770dcabb5e27225184ab429b9064bcdfef21d80140c95d |
| rolling_2 | 2025-07-18 | 2020-01-31 | 2025-05-29 | 2025-06-05 | 2025-07-04 | 2025-07-12 | 2025-07-18 | {'rows': 17945, 'observed_target_rows': 13051, 'imputed_target_rows': 3572, 'unavailable_target_rows': 1322} | {'rows': 450, 'observed_target_rows': 348, 'imputed_target_rows': 74, 'unavailable_target_rows': 28} | {'rows': 105, 'observed_target_rows': 86, 'imputed_target_rows': 17, 'unavailable_target_rows': 2} | [{'model': 'moving_average_7d', 'split': 'test', 'rows': 86, 'mae': 164.2, 'rmse': 342.47, 'smape_pct': 12.26, 'mase': None, 'population': 'observed_targets', 'observed_target_rows': 86, 'imputed_target_rows_excluded': 17, 'unavailable_target_rows': 2, 'provenance_id': '1465d5ede864fdd562770dcabb5e27225184ab429b9064bcdfef21d80140c95d'}] | {'origin_id': 'rolling_2', 'method': 'split_conformal', 'lower_residual': -257.1428571428571, 'upper_residual': 257.1428571428571, 'calibration_rows': 348, 'provenance_id': '1465d5ede864fdd562770dcabb5e27225184ab429b9064bcdfef21d80140c95d'} | 1465d5ede864fdd562770dcabb5e27225184ab429b9064bcdfef21d80140c95d |
| rolling_3 | 2025-07-25 | 2020-01-31 | 2025-06-05 | 2025-06-12 | 2025-07-11 | 2025-07-19 | 2025-07-25 | {'rows': 18050, 'observed_target_rows': 13131, 'imputed_target_rows': 3593, 'unavailable_target_rows': 1326} | {'rows': 450, 'observed_target_rows': 354, 'imputed_target_rows': 73, 'unavailable_target_rows': 23} | {'rows': 105, 'observed_target_rows': 72, 'imputed_target_rows': 29, 'unavailable_target_rows': 4} | [{'model': 'moving_average_7d', 'split': 'test', 'rows': 72, 'mae': 83.12, 'rmse': 190.13, 'smape_pct': 6.55, 'mase': None, 'population': 'observed_targets', 'observed_target_rows': 72, 'imputed_target_rows_excluded': 29, 'unavailable_target_rows': 4, 'provenance_id': '1465d5ede864fdd562770dcabb5e27225184ab429b9064bcdfef21d80140c95d'}] | {'origin_id': 'rolling_3', 'method': 'split_conformal', 'lower_residual': -200.0, 'upper_residual': 200.0, 'calibration_rows': 354, 'provenance_id': '1465d5ede864fdd562770dcabb5e27225184ab429b9064bcdfef21d80140c95d'} | 1465d5ede864fdd562770dcabb5e27225184ab429b9064bcdfef21d80140c95d |

## Untouched final holdout

- Definition: last 90 days of trainable as-of rows, evaluated after rolling origins
- Dates: 2025-07-26 to 2025-10-23
- Test population counts: {'rows': 1204, 'observed_target_rows': 792, 'imputed_target_rows': 285, 'unavailable_target_rows': 127}

| model | split | rows | mae | rmse | smape_pct | mase | population | observed_target_rows | imputed_target_rows_excluded | unavailable_target_rows | provenance_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| moving_average_7d | test | 792 | 133.61 | 246.89 | 11.73 | None | observed_targets | 792 | 285 | 127 | 1465d5ede864fdd562770dcabb5e27225184ab429b9064bcdfef21d80140c95d |

## Conditional versus split-conformal intervals

| method | description | nominal_coverage | calibration_rows | evaluation_rows | excluded_imputed_rows | excluded_unavailable_rows | empirical_coverage | coverage_error | coverage_shortfall | failure_mode | excluded_imputed_rate | excluded_unavailable_rate | avg_interval_width_inr_qtl | median_interval_width_inr_qtl | lower_residual | upper_residual | provenance_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| conditional_residual | asymmetric residual quantiles from observed validation targets | 0.9 | 959 | 792 | 285 | 127 | 0.8686868686868687 | -0.03131313131313129 | 0.03131313131313129 | undercoverage_on_observed_holdout | 0.2367109634551495 | 0.10548172757475083 | 493.92857142857105 | 493.9285714285711 | -200.71428571428578 | 293.2142857142854 | 1465d5ede864fdd562770dcabb5e27225184ab429b9064bcdfef21d80140c95d |
| split_conformal | symmetric finite-sample absolute-residual quantile from observed validation targets | 0.9 | 959 | 792 | 285 | 127 | 0.9090909090909091 | 0.009090909090909038 | 0.0 | nominal_or_overcoverage_with_width_tradeoff | 0.2367109634551495 | 0.10548172757475083 | 528.5714285714284 | 528.5714285714284 | -264.2857142857142 | 264.2857142857142 | 1465d5ede864fdd562770dcabb5e27225184ab429b9064bcdfef21d80140c95d |

- Failure-mode comparison is explicit: undercoverage, coverage shortfall, excluded imputed/unavailable rows, and width tradeoffs are recorded for each candidate.

- Adopted method: split_conformal
- Adoption rule: pre-declared rule: smallest absolute coverage error to nominal, then narrowest mean interval

## Rolling-origin interval calibration

Each rolling origin calibrates its interval bounds on that origin's observed validation targets. The adopted method is fixed by the final comparison; holdout-derived bounds are not reused backward.

| origin_id | method | description | nominal_coverage | calibration_rows | evaluation_rows | excluded_imputed_rows | excluded_unavailable_rows | empirical_coverage | coverage_error | coverage_shortfall | failure_mode | excluded_imputed_rate | excluded_unavailable_rate | avg_interval_width_inr_qtl | median_interval_width_inr_qtl | lower_residual | upper_residual | provenance_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rolling_1 | conditional_residual | asymmetric residual quantiles from observed validation targets | 0.9 | 352 | 88 | 14 | 3 | 0.9090909090909091 | 0.009090909090909038 | 0.0 | nominal_or_overcoverage_with_width_tradeoff | 0.13333333333333333 | 0.02857142857142857 | 456.4285714285715 | 456.42857142857133 | -163.57142857142844 | 292.8571428571429 | 1465d5ede864fdd562770dcabb5e27225184ab429b9064bcdfef21d80140c95d |
| rolling_1 | split_conformal | symmetric finite-sample absolute-residual quantile from observed validation targets | 0.9 | 352 | 88 | 14 | 3 | 0.9431818181818182 | 0.04318181818181821 | 0.0 | nominal_or_overcoverage_with_width_tradeoff | 0.13333333333333333 | 0.02857142857142857 | 528.571428571429 | 528.5714285714289 | -264.28571428571445 | 264.28571428571445 | 1465d5ede864fdd562770dcabb5e27225184ab429b9064bcdfef21d80140c95d |
| rolling_2 | conditional_residual | asymmetric residual quantiles from observed validation targets | 0.9 | 348 | 86 | 17 | 2 | 0.7209302325581395 | -0.17906976744186054 | 0.17906976744186054 | undercoverage_on_observed_holdout | 0.1619047619047619 | 0.01904761904761905 | 450.0 | 450.0 | -157.1428571428571 | 292.8571428571429 | 1465d5ede864fdd562770dcabb5e27225184ab429b9064bcdfef21d80140c95d |
| rolling_2 | split_conformal | symmetric finite-sample absolute-residual quantile from observed validation targets | 0.9 | 348 | 86 | 17 | 2 | 0.9069767441860465 | 0.006976744186046435 | 0.0 | nominal_or_overcoverage_with_width_tradeoff | 0.1619047619047619 | 0.01904761904761905 | 514.2857142857143 | 514.2857142857142 | -257.1428571428571 | 257.1428571428571 | 1465d5ede864fdd562770dcabb5e27225184ab429b9064bcdfef21d80140c95d |
| rolling_3 | conditional_residual | asymmetric residual quantiles from observed validation targets | 0.9 | 354 | 72 | 29 | 4 | 0.9444444444444444 | 0.0444444444444444 | 0.0 | nominal_or_overcoverage_with_width_tradeoff | 0.2761904761904762 | 0.0380952380952381 | 373.9285714285709 | 373.9285714285709 | -171.4285714285711 | 202.49999999999974 | 1465d5ede864fdd562770dcabb5e27225184ab429b9064bcdfef21d80140c95d |
| rolling_3 | split_conformal | symmetric finite-sample absolute-residual quantile from observed validation targets | 0.9 | 354 | 72 | 29 | 4 | 0.9583333333333334 | 0.05833333333333335 | 0.0 | nominal_or_overcoverage_with_width_tradeoff | 0.2761904761904762 | 0.0380952380952381 | 400.0 | 400.0 | -200.0 | 200.0 | 1465d5ede864fdd562770dcabb5e27225184ab429b9064bcdfef21d80140c95d |

## Multi-origin transport backtest

Each scenario first applies the observed-target mask. Target-ineligible rows, coordinate exclusions, and realized-target drops are counted per as-of date; the realized lookup uses the declared matching tolerance only after eligibility is established.

| origin | transport_cost_multiplier | cost_per_km_per_quintal | realized_target_population | provenance_id | regret_at_1_mean | regret_at_1_median | optimal_rate_1 | beats_nearest_1 | regret_at_3_mean | regret_at_3_median | optimal_rate_3 | beats_nearest_3 | nearest_mandi_regret_mean | nearest_mandi_regret_median | n_dates | date_min | date_max | n_dropped | n_candidate_mandis_sum | n_prediction_candidates_sum | n_target_ineligible_sum | n_coordinate_excluded_sum | n_observed_realized_sum | n_imputed_realized_sum | n_eligible_realized_sum | interval_method | lower_residual | upper_residual | target_matching_tolerance_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rolling_1 | 0.8 | 3.2 | observed_only | 1465d5ede864fdd562770dcabb5e27225184ab429b9064bcdfef21d80140c95d | 1287.3542882408494 | 0.0 | 0.7142857142857143 | 0.8571428571428571 | 1283.771670527586 | 0.0 | 0.8571428571428571 | 0.8571428571428571 | 1521.637801536008 | 310.065146707238 | 7 | 2025-07-05 | 2025-07-11 | 0 | 88 | 88 | 17 | 0 | 88 | 0 | 88 | split_conformal | -264.28571428571445 | 264.28571428571445 | 2 |
| rolling_1 | 1.0 | 4.0 | observed_only | 1465d5ede864fdd562770dcabb5e27225184ab429b9064bcdfef21d80140c95d | 1261.6928603010617 | 0.0 | 0.7142857142857143 | 0.8571428571428571 | 1260.7860167309111 | 0.0 | 0.8571428571428571 | 0.8571428571428571 | 1487.7615376342958 | 300.0814333840474 | 7 | 2025-07-05 | 2025-07-11 | 0 | 88 | 88 | 17 | 0 | 88 | 0 | 88 | split_conformal | -264.28571428571445 | 264.28571428571445 | 2 |
| rolling_1 | 1.2 | 4.8 | observed_only | 1465d5ede864fdd562770dcabb5e27225184ab429b9064bcdfef21d80140c95d | 1237.8003629342363 | 0.0 | 0.8571428571428571 | 0.8571428571428571 | 1237.8003629342363 | 0.0 | 0.8571428571428571 | 0.8571428571428571 | 1455.6542043055451 | 290.0977200608568 | 7 | 2025-07-05 | 2025-07-11 | 0 | 88 | 88 | 17 | 0 | 88 | 0 | 88 | split_conformal | -264.28571428571445 | 264.28571428571445 | 2 |
| rolling_2 | 0.8 | 3.2 | observed_only | 1465d5ede864fdd562770dcabb5e27225184ab429b9064bcdfef21d80140c95d | 504.9245070314907 | 843.5983063068977 | 0.2857142857142857 | 0.42857142857142855 | 0.0 | 0.0 | 1.0 | 0.8571428571428571 | 287.3058915788282 | 310.065146707238 | 7 | 2025-07-12 | 2025-07-18 | 0 | 86 | 86 | 19 | 0 | 86 | 0 | 86 | split_conformal | -257.1428571428571 | 257.1428571428571 | 2 |
| rolling_2 | 1.0 | 4.0 | observed_only | 1465d5ede864fdd562770dcabb5e27225184ab429b9064bcdfef21d80140c95d | 594.1913480750776 | 1004.497882883622 | 0.2857142857142857 | 0.42857142857142855 | 0.0 | 0.0 | 1.0 | 0.8571428571428571 | 273.73950733067807 | 300.0814333840474 | 7 | 2025-07-12 | 2025-07-18 | 0 | 86 | 86 | 19 | 0 | 86 | 0 | 86 | split_conformal | -257.1428571428571 | 257.1428571428571 | 2 |
| rolling_2 | 1.2 | 4.8 | observed_only | 1465d5ede864fdd562770dcabb5e27225184ab429b9064bcdfef21d80140c95d | 685.3699768344835 | 1165.3974594603462 | 0.42857142857142855 | 0.42857142857142855 | 0.0 | 0.0 | 1.0 | 0.8571428571428571 | 262.084910798347 | 290.0977200608568 | 7 | 2025-07-12 | 2025-07-18 | 0 | 86 | 86 | 19 | 0 | 86 | 0 | 86 | split_conformal | -257.1428571428571 | 257.1428571428571 | 2 |
| rolling_3 | 0.8 | 3.2 | observed_only | 1465d5ede864fdd562770dcabb5e27225184ab429b9064bcdfef21d80140c95d | 31.414257188499473 | 0.0 | 0.8571428571428571 | 0.5714285714285714 | 0.0 | 0.0 | 1.0 | 0.7142857142857143 | 255.24921782355338 | 360.065146707238 | 7 | 2025-07-19 | 2025-07-25 | 0 | 72 | 72 | 33 | 0 | 72 | 0 | 72 | split_conformal | -200.0 | 200.0 | 2 |
| rolling_3 | 1.0 | 4.0 | observed_only | 1465d5ede864fdd562770dcabb5e27225184ab429b9064bcdfef21d80140c95d | 32.12496434276721 | 0.0 | 0.8571428571428571 | 0.5714285714285714 | 0.0 | 0.0 | 1.0 | 0.7142857142857143 | 242.2758079937274 | 331.42933837510304 | 7 | 2025-07-19 | 2025-07-25 | 0 | 72 | 72 | 33 | 0 | 72 | 0 | 72 | split_conformal | -200.0 | 200.0 | 2 |
| rolling_3 | 1.2 | 4.8 | observed_only | 1465d5ede864fdd562770dcabb5e27225184ab429b9064bcdfef21d80140c95d | 32.83567149703494 | 0.0 | 0.8571428571428571 | 0.5714285714285714 | 2.1432350900673294 | 0.0 | 0.8571428571428571 | 0.7142857142857143 | 229.30239816390144 | 302.7152060501237 | 7 | 2025-07-19 | 2025-07-25 | 0 | 72 | 72 | 33 | 0 | 72 | 0 | 72 | split_conformal | -200.0 | 200.0 | 2 |

## Reproduction

    python scripts/run_phase3_evaluation.py

The JSON companion is strict JSON (no NaN/Infinity) and contains the complete split, denominator, interval, scenario, and provenance records.
