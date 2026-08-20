from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mandipulse.modeling.phase3 import (
    adopt_interval_method,
    canonical_hash,
    compare_interval_methods,
    impute_short_internal_gaps,
    observed_target_mask,
    target_population_counts,
)
from mandipulse.modeling.splits import SplitConfig, make_rolling_origin_splits
from mandipulse.recommend.evaluation import backtest_recommendations, realized_net_price


def test_short_gap_fill_never_uses_future_value() -> None:
    frame = pd.DataFrame(
        {
            "market_id": [1, 1, 1, 1, 1],
            "date": pd.date_range("2025-01-01", periods=5),
            "price": [100.0, np.nan, 900.0, np.nan, np.nan],
        }
    )
    result = impute_short_internal_gaps(
        frame,
        value_columns=["price"],
        max_gap_days=1,
    )
    assert result.loc[1, "price"] == 100.0
    assert result.loc[1, "is_imputed"]
    assert pd.isna(result.loc[3, "price"])
    assert pd.isna(result.loc[4, "price"])


def test_observed_target_population_counts_are_explicit() -> None:
    frame = pd.DataFrame(
        {
            "is_observed": [True, True, False, True],
            "target_observed_t_plus_7": [True, False, False, True],
            "target_imputed_t_plus_7": [False, True, True, False],
        }
    )
    assert observed_target_mask(frame).tolist() == [True, False, False, True]
    assert target_population_counts(frame) == {
        "rows": 4,
        "observed_target_rows": 2,
        "imputed_target_rows": 2,
        "unavailable_target_rows": 0,
    }


def test_rolling_origins_are_purged_and_before_final_holdout(synthetic_features) -> None:
    trainable = synthetic_features[synthetic_features["feature_row_valid"].astype(bool)].copy()
    config = SplitConfig(validation_days=7, test_days=7, horizon_days=7)
    origins = make_rolling_origin_splits(
        trainable,
        config,
        n_origins=2,
        final_holdout_days=7,
    )
    assert len(origins) == 2
    for origin in origins:
        assert origin.dates.train_end < origin.dates.validation_start
        assert origin.dates.validation_end < origin.dates.test_start
        assert origin.dates.test_end < trainable["date"].max() - pd.Timedelta(days=6)


def test_interval_comparison_has_observed_denominator_and_finite_values() -> None:
    dates = pd.date_range("2025-01-01", periods=8)
    predictions = pd.DataFrame(
        {
            "split": ["validation"] * 4 + ["test"] * 4,
            "model": ["moving_average_7d"] * 8,
            "date": dates,
            "market_id": [1] * 8,
            "target_price_t_plus_7": [100, 110, 120, 130, 105, 115, 125, 135],
            "prediction": [98, 112, 118, 132, 104, 114, 129, 133],
            "is_observed": [True, True, True, True, True, False, True, True],
            "target_observed_t_plus_7": [True, True, True, True, True, False, True, True],
            "target_imputed_t_plus_7": [False, False, False, False, False, True, False, False],
        }
    )
    comparison = compare_interval_methods(
        predictions,
        model_name="moving_average_7d",
        confidence_level=0.9,
        observed_only=True,
    )
    assert set(comparison["method"]) == {"conditional_residual", "split_conformal"}
    assert (comparison["evaluation_rows"] == 3).all()
    assert (comparison["excluded_imputed_rows"] == 1).all()
    assert np.isfinite(comparison["empirical_coverage"]).all()
    assert set(comparison["failure_mode"]).issubset(
        {
            "undercoverage_on_observed_holdout",
            "nominal_or_overcoverage_with_width_tradeoff",
        }
    )
    assert "undercoverage_on_observed_holdout" in set(comparison["failure_mode"])
    assert (comparison["coverage_shortfall"] >= 0).all()
    adopted, reason = adopt_interval_method(comparison)
    assert adopted in {"conditional_residual", "split_conformal"}
    assert "pre-declared rule" in reason


def test_canonical_hash_is_order_independent() -> None:
    assert canonical_hash({"b": 2, "a": 1}) == canonical_hash({"a": 1, "b": 2})


def test_observed_only_realized_price_excludes_imputed_row() -> None:
    panel = pd.DataFrame(
        {
            "market_id": [1],
            "date": ["2025-01-08"],
            "modal_price_inr_qtl": [900.0],
            "is_observed": [False],
        }
    )
    assert (
        realized_net_price(
            panel,
            market_id=1,
            target_date=pd.Timestamp("2025-01-08"),
            transport_cost_inr_qtl=0.0,
            observed_only=True,
        )
        is None
    )


def test_observed_only_backtest_matches_target_population_and_keeps_empty_dates() -> None:
    panel = pd.DataFrame(
        {
            "market_id": [1, 2],
            "date": ["2025-01-08", "2025-01-08"],
            "modal_price_inr_qtl": [1500.0, 2200.0],
            "is_observed": [True, False],
        }
    )
    mandis = pd.DataFrame(
        {
            "market_id": [1, 2],
            "market_name": ["MandiA", "MandiB"],
            "district_name": ["Nashik", "Pune"],
            "latitude": [20.0, 18.5],
            "longitude": [73.8, 73.9],
        }
    )
    predictions = pd.DataFrame(
        {
            "date": ["2025-01-01", "2025-01-01"],
            "market_id": [1, 2],
            "market_name": ["MandiA", "MandiB"],
            "district": ["Nashik", "Pune"],
            "mandi_id": ["a", "b"],
            "target_price_t_plus_7": [1500.0, 2200.0],
            "split": ["test", "test"],
            "model": ["moving_average_7d", "moving_average_7d"],
            "prediction": [1490.0, 2190.0],
            "is_observed": [True, True],
            "target_observed_t_plus_7": [True, False],
            "target_imputed_t_plus_7": [False, True],
        }
    )
    kwargs = {
        "panel": panel,
        "mandis": mandis,
        "predictions": predictions,
        "k_values": [1],
        "farmer_lat": 19.9975,
        "farmer_lon": 73.78981,
        "cost_per_km_per_quintal": 4.0,
        "road_distance_factor": 1.3,
        "uncertainty_penalty_weight": 0.3,
        "low_max_interval_pct": 0.10,
        "high_min_interval_pct": 0.25,
        "lower_residual": -100.0,
        "upper_residual": 100.0,
        "observed_target_only": True,
    }
    result = backtest_recommendations(**kwargs)
    row = result.iloc[0]
    assert len(result) == 1
    assert row["n_prediction_candidates"] == 1
    assert row["n_target_ineligible"] == 1
    assert row["n_candidate_mandis"] == 1
    assert row["n_observed_realized"] == 1
    assert row["n_eligible_realized"] == 1
    assert row["n_dropped"] == 0
    assert row["regret_at_1"] == 0.0

    no_coordinates = mandis.assign(latitude=np.nan, longitude=np.nan)
    empty_candidate = backtest_recommendations(**{**kwargs, "mandis": no_coordinates})
    empty_row = empty_candidate.iloc[0]
    assert len(empty_candidate) == 1
    assert empty_row["n_candidate_mandis"] == 0
    assert empty_row["n_coordinate_excluded"] == 1
    assert pd.isna(empty_row["regret_at_1"])


def test_phase3_report_provenance_binds_interval_and_result_rows() -> None:
    payload = json.loads(
        Path("reports/modeling/phase3_evaluation.json").read_text(encoding="utf-8")
    )
    provenance_id = payload["provenance_id"]
    assert provenance_id == canonical_hash(payload["provenance"])
    interval = payload["provenance"]["interval"]
    assert interval["adopted_method"] == payload["interval_adoption"]["method"]
    assert interval["adoption_rule"] == payload["interval_adoption"]["rule"]
    assert "lower_residual" in interval and "upper_residual" in interval
    assert interval["adopted_method"] == "split_conformal"
    assert payload["interval_adoption"]["provenance_id"] == provenance_id
    for origin in payload["rolling_origins"]:
        assert origin["provenance_id"] == provenance_id
        assert origin["interval"]["provenance_id"] == provenance_id
        assert origin["metrics"][0]["provenance_id"] == provenance_id
    for row in payload["rolling_interval_comparison"]:
        assert row["provenance_id"] == provenance_id
    for row in payload["recommendation_backtest"]["rows"]:
        assert row["provenance_id"] == provenance_id
