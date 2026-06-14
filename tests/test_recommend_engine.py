from __future__ import annotations


import pandas as pd
import pytest

from mandipulse.recommend.engine import (
    compute_transport_cost_inr_qtl,
    haversine_km,
    risk_level,
    score_recommendations,
)


class TestHaversineKm:
    def test_identical_points_is_zero(self) -> None:
        assert haversine_km(19.0, 73.0, 19.0, 73.0) == pytest.approx(0.0, abs=1e-6)

    def test_known_distance_mumbai_to_pune(self) -> None:
        # Mumbai (18.975°N, 72.825°E) to Pune (18.520°N, 73.857°E) ≈ 119 km airline
        dist = haversine_km(18.975, 72.825, 18.520, 73.857)
        assert 110 < dist < 130

    def test_symmetry(self) -> None:
        a = haversine_km(19.0, 73.0, 20.0, 74.0)
        b = haversine_km(20.0, 74.0, 19.0, 73.0)
        assert a == pytest.approx(b, rel=1e-9)


class TestTransportCost:
    def test_linear_in_distance(self) -> None:
        c1 = compute_transport_cost_inr_qtl(100.0, 4.0)
        c2 = compute_transport_cost_inr_qtl(200.0, 4.0)
        assert c2 == pytest.approx(2 * c1)

    def test_zero_distance_is_zero_cost(self) -> None:
        assert compute_transport_cost_inr_qtl(0.0, 4.0) == pytest.approx(0.0)

    def test_per_quintal_rate(self) -> None:
        # Result is per-quintal — independent of load
        assert compute_transport_cost_inr_qtl(50.0, 4.0) == pytest.approx(200.0)


class TestRiskLevel:
    def test_at_low_boundary_is_low(self) -> None:
        assert risk_level(0.10, low_max_pct=0.10, high_min_pct=0.25) == "low"

    def test_below_low_boundary_is_low(self) -> None:
        assert risk_level(0.05, low_max_pct=0.10, high_min_pct=0.25) == "low"

    def test_between_boundaries_is_medium(self) -> None:
        assert risk_level(0.15, low_max_pct=0.10, high_min_pct=0.25) == "medium"

    def test_at_high_boundary_is_high(self) -> None:
        assert risk_level(0.25, low_max_pct=0.10, high_min_pct=0.25) == "high"

    def test_above_high_boundary_is_high(self) -> None:
        assert risk_level(0.50, low_max_pct=0.10, high_min_pct=0.25) == "high"


class TestScoreRecommendations:
    @pytest.fixture()
    def minimal_forecasts(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "market_id": [1, 2, 3],
                "mandi_id": ["mh__a", "mh__b", "mh__c"],
                "mandi": ["MandiA", "MandiB", "MandiC"],
                "crop": ["onion"] * 3,
                "model_name": ["moving_average_7d"] * 3,
                "horizon_days": [7] * 3,
                "forecast_price_inr_qtl": [1400.0, 1200.0, 1000.0],
                "lower_bound_inr_qtl": [1190.0, 990.0, 790.0],
                "upper_bound_inr_qtl": [1610.0, 1410.0, 1210.0],
                "confidence_level": [0.9] * 3,
            }
        )

    @pytest.fixture()
    def minimal_mandis(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "market_id": [1, 2, 3],
                "market_name": ["MandiA", "MandiB", "MandiC"],
                "district_name": ["Nashik", "Pune", "Solapur"],
                "latitude": [20.0, 18.5, 17.7],
                "longitude": [73.8, 73.9, 75.9],
            }
        )

    def test_rank_is_dense_one_to_n(self, minimal_forecasts, minimal_mandis) -> None:
        recs = score_recommendations(
            forecasts=minimal_forecasts,
            mandis=minimal_mandis,
            farmer_latitude=19.9975,
            farmer_longitude=73.7898,
            cost_per_km_per_quintal=4.0,
            road_distance_factor=1.3,
            uncertainty_penalty_weight=0.3,
            low_max_interval_pct=0.10,
            high_min_interval_pct=0.25,
            candidate_state="maharashtra",
        )
        assert list(recs["rank"]) == list(range(1, len(recs) + 1))

    def test_net_price_equals_forecast_minus_transport(
        self, minimal_forecasts, minimal_mandis
    ) -> None:
        recs = score_recommendations(
            forecasts=minimal_forecasts,
            mandis=minimal_mandis,
            farmer_latitude=19.9975,
            farmer_longitude=73.7898,
            cost_per_km_per_quintal=4.0,
            road_distance_factor=1.3,
            uncertainty_penalty_weight=0.3,
            low_max_interval_pct=0.10,
            high_min_interval_pct=0.25,
            candidate_state="maharashtra",
        )
        diff = (
            recs["forecast_price_inr_qtl"]
            - recs["estimated_transport_cost_inr_qtl"]
            - recs["expected_net_price_inr_qtl"]
        ).abs()
        assert diff.max() < 1e-6

    def test_score_equals_net_minus_penalty(self, minimal_forecasts, minimal_mandis) -> None:
        penalty_weight = 0.3
        recs = score_recommendations(
            forecasts=minimal_forecasts,
            mandis=minimal_mandis,
            farmer_latitude=19.9975,
            farmer_longitude=73.7898,
            cost_per_km_per_quintal=4.0,
            road_distance_factor=1.3,
            uncertainty_penalty_weight=penalty_weight,
            low_max_interval_pct=0.10,
            high_min_interval_pct=0.25,
            candidate_state="maharashtra",
        )
        expected_score = recs["expected_net_price_inr_qtl"] - recs["uncertainty_penalty_inr_qtl"]
        diff = (recs["risk_adjusted_score"] - expected_score).abs()
        assert diff.max() < 1e-6

    def test_sorted_by_score_descending(self, minimal_forecasts, minimal_mandis) -> None:
        recs = score_recommendations(
            forecasts=minimal_forecasts,
            mandis=minimal_mandis,
            farmer_latitude=19.9975,
            farmer_longitude=73.7898,
            cost_per_km_per_quintal=4.0,
            road_distance_factor=1.3,
            uncertainty_penalty_weight=0.3,
            low_max_interval_pct=0.10,
            high_min_interval_pct=0.25,
            candidate_state="maharashtra",
        )
        scores = recs["risk_adjusted_score"].tolist()
        assert scores == sorted(scores, reverse=True)

    def test_required_output_columns_present(self, minimal_forecasts, minimal_mandis) -> None:
        recs = score_recommendations(
            forecasts=minimal_forecasts,
            mandis=minimal_mandis,
            farmer_latitude=19.9975,
            farmer_longitude=73.7898,
            cost_per_km_per_quintal=4.0,
            road_distance_factor=1.3,
            uncertainty_penalty_weight=0.3,
            low_max_interval_pct=0.10,
            high_min_interval_pct=0.25,
            candidate_state="maharashtra",
        )
        required = {
            "mandi",
            "estimated_transport_cost_inr_qtl",
            "expected_net_price_inr_qtl",
            "risk_level",
            "reason",
            "rank",
        }
        assert required.issubset(set(recs.columns))

    def test_raises_when_mandi_missing_coords(self, minimal_forecasts, minimal_mandis) -> None:
        mandis_missing = minimal_mandis.copy()
        mandis_missing.loc[0, "latitude"] = float("nan")
        with pytest.raises(ValueError, match="missing coordinates"):
            score_recommendations(
                forecasts=minimal_forecasts,
                mandis=mandis_missing,
                farmer_latitude=19.9975,
                farmer_longitude=73.7898,
                cost_per_km_per_quintal=4.0,
                road_distance_factor=1.3,
                uncertainty_penalty_weight=0.3,
                low_max_interval_pct=0.10,
                high_min_interval_pct=0.25,
                candidate_state="maharashtra",
            )

    def test_golden_fixture_rank_1_is_pimpalgaon(self, golden_recommendations) -> None:
        top = golden_recommendations[golden_recommendations["rank"] == 1]
        assert len(top) == 1
        assert "Pimpalgaon" in top["mandi"].iloc[0]

    def test_raises_on_duplicate_market_id_in_forecasts(self, minimal_mandis) -> None:
        forecasts_with_dup = pd.DataFrame(
            {
                "market_id": [1, 1, 2],  # market_id=1 duplicated
                "mandi_id": ["mh__a", "mh__a2", "mh__b"],
                "mandi": ["MandiA", "MandiA2", "MandiB"],
                "crop": ["onion"] * 3,
                "model_name": ["moving_average_7d"] * 3,
                "horizon_days": [7] * 3,
                "forecast_price_inr_qtl": [1400.0, 1350.0, 1200.0],
                "lower_bound_inr_qtl": [1190.0, 1140.0, 990.0],
                "upper_bound_inr_qtl": [1610.0, 1560.0, 1410.0],
                "confidence_level": [0.9] * 3,
            }
        )
        with pytest.raises(Exception):
            score_recommendations(
                forecasts=forecasts_with_dup,
                mandis=minimal_mandis,
                farmer_latitude=19.9975,
                farmer_longitude=73.7898,
                cost_per_km_per_quintal=4.0,
                road_distance_factor=1.3,
                uncertainty_penalty_weight=0.3,
                low_max_interval_pct=0.10,
                high_min_interval_pct=0.25,
                candidate_state="maharashtra",
            )
