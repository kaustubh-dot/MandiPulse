from __future__ import annotations

import pandas as pd
import pytest

from mandipulse.recommend.evaluation import (
    backtest_recommendations,
    nearest_mandi_regret,
    realized_net_price,
    regret_at_k,
    summarize_backtest,
)


@pytest.fixture()
def minimal_panel() -> pd.DataFrame:
    """Three mandis, observed rows on 2025-10-22 (target_date = 2025-10-15 + 7)."""
    return pd.DataFrame(
        {
            "market_id": [1, 2, 3],
            "date": ["2025-10-22", "2025-10-22", "2025-10-22"],
            "modal_price_inr_qtl": [1500.0, 1300.0, 1100.0],
            "is_observed": [True, True, True],
        }
    )


@pytest.fixture()
def minimal_mandis_with_coords() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "market_id": [1, 2, 3],
            "market_name": ["MandiA", "MandiB", "MandiC"],
            "latitude": [20.0, 18.5, 17.7],
            "longitude": [73.8, 73.9, 75.9],
        }
    )


class TestRealizedNetPrice:
    def test_returns_net_price_for_exact_date(self, minimal_panel) -> None:
        transport_cost = 100.0
        net = realized_net_price(
            minimal_panel,
            market_id=1,
            target_date=pd.Timestamp("2025-10-22"),
            transport_cost_inr_qtl=transport_cost,
        )
        assert net == pytest.approx(1500.0 - transport_cost)

    def test_returns_none_when_mandi_not_in_panel(self, minimal_panel) -> None:
        net = realized_net_price(
            minimal_panel,
            market_id=99,
            target_date=pd.Timestamp("2025-10-22"),
            transport_cost_inr_qtl=100.0,
        )
        assert net is None

    def test_returns_none_when_outside_tolerance(self, minimal_panel) -> None:
        # target 2025-10-10, panel on 2025-10-22 → 12 days gap, default tol=2
        net = realized_net_price(
            minimal_panel,
            market_id=1,
            target_date=pd.Timestamp("2025-10-10"),
            transport_cost_inr_qtl=100.0,
        )
        assert net is None

    def test_uses_closest_date_within_tolerance(self) -> None:
        panel = pd.DataFrame(
            {
                "market_id": [1, 1],
                "date": ["2025-10-21", "2025-10-23"],
                "modal_price_inr_qtl": [1400.0, 1600.0],
                "is_observed": [True, True],
            }
        )
        # target = 2025-10-22; both within tol=2; 2025-10-21 is 1 day closer
        # but 2025-10-23 is also 1 day away — check closest is selected (either is fine)
        net = realized_net_price(
            panel,
            market_id=1,
            target_date=pd.Timestamp("2025-10-22"),
            transport_cost_inr_qtl=0.0,
        )
        # Both rows are equidistant from target; either price is acceptable
        assert net is not None
        assert net == pytest.approx(1400.0, abs=1.0) or net == pytest.approx(1600.0, abs=1.0)

    def test_prefers_observed_over_imputed(self) -> None:
        panel = pd.DataFrame(
            {
                "market_id": [1, 1],
                "date": ["2025-10-22", "2025-10-22"],
                "modal_price_inr_qtl": [999.0, 1500.0],
                "is_observed": [False, True],
            }
        )
        net = realized_net_price(
            panel,
            market_id=1,
            target_date=pd.Timestamp("2025-10-22"),
            transport_cost_inr_qtl=0.0,
        )
        assert net == pytest.approx(1500.0)

    def test_falls_back_to_imputed_when_no_observed(self) -> None:
        panel = pd.DataFrame(
            {
                "market_id": [1],
                "date": ["2025-10-22"],
                "modal_price_inr_qtl": [800.0],
                "is_observed": [False],
            }
        )
        net = realized_net_price(
            panel,
            market_id=1,
            target_date=pd.Timestamp("2025-10-22"),
            transport_cost_inr_qtl=50.0,
        )
        assert net == pytest.approx(750.0)

    def test_accepts_string_date_column(self) -> None:
        panel = pd.DataFrame(
            {
                "market_id": [1],
                "date": ["2025-10-22"],  # string, not datetime
                "modal_price_inr_qtl": [1200.0],
                "is_observed": [True],
            }
        )
        net = realized_net_price(
            panel,
            market_id=1,
            target_date=pd.Timestamp("2025-10-22"),
            transport_cost_inr_qtl=0.0,
        )
        assert net == pytest.approx(1200.0)


class TestRegretAtK:
    def _ranked(self) -> pd.DataFrame:
        return pd.DataFrame({"market_id": [1, 2, 3], "rank": [1, 2, 3]})

    def test_regret_at_1_is_best_minus_top1(self) -> None:
        realized = {1: 900.0, 2: 1000.0, 3: 800.0}
        # top-1 is market_id=1 (rank=1), realized=900; best=1000 → regret=100
        r = regret_at_k(self._ranked(), realized, k=1)
        assert r == pytest.approx(100.0)

    def test_zero_regret_when_top1_is_best(self) -> None:
        realized = {1: 1000.0, 2: 900.0, 3: 800.0}
        r = regret_at_k(self._ranked(), realized, k=1)
        assert r == pytest.approx(0.0)

    def test_regret_at_k3_picks_max_of_top3(self) -> None:
        realized = {1: 900.0, 2: 950.0, 3: 800.0}
        # top-3 includes all mandis; max(top3)=950; best=950 → regret=0
        r = regret_at_k(self._ranked(), realized, k=3)
        assert r == pytest.approx(0.0)

    def test_returns_none_when_realized_empty(self) -> None:
        r = regret_at_k(self._ranked(), {}, k=1)
        assert r is None

    def test_returns_none_when_top_k_have_no_realized(self) -> None:
        # market_id=1 (rank=1) has no realized price
        realized = {2: 900.0, 3: 800.0}
        r = regret_at_k(self._ranked(), realized, k=1)
        assert r is None

    def test_regret_is_non_negative(self) -> None:
        realized = {1: 800.0, 2: 900.0, 3: 700.0}
        r = regret_at_k(self._ranked(), realized, k=1)
        assert r is not None
        assert r >= 0.0


class TestNearestMandiRegret:
    def test_returns_zero_when_nearest_has_best_realized(self, minimal_mandis_with_coords) -> None:
        # MandiA is at (20.0, 73.8) — closest to farmer at ~(20.0, 73.8)
        realized = {1: 1500.0, 2: 1300.0, 3: 1100.0}
        r = nearest_mandi_regret(
            realized, farmer_lat=20.0, farmer_lon=73.8, mandis=minimal_mandis_with_coords
        )
        assert r == pytest.approx(0.0)

    def test_returns_positive_when_nearest_not_best(self, minimal_mandis_with_coords) -> None:
        # MandiA (market_id=1) is nearest to (20.0, 73.8); give MandiB the best realized
        realized = {1: 1000.0, 2: 1500.0, 3: 1100.0}
        r = nearest_mandi_regret(
            realized, farmer_lat=20.0, farmer_lon=73.8, mandis=minimal_mandis_with_coords
        )
        assert r is not None
        assert r == pytest.approx(500.0)

    def test_returns_none_when_realized_empty(self, minimal_mandis_with_coords) -> None:
        r = nearest_mandi_regret(
            {}, farmer_lat=20.0, farmer_lon=73.8, mandis=minimal_mandis_with_coords
        )
        assert r is None

    def test_ignores_mandis_without_coords(self) -> None:
        mandis = pd.DataFrame(
            {
                "market_id": [1, 2],
                "latitude": [float("nan"), 18.5],
                "longitude": [float("nan"), 73.9],
            }
        )
        # Only mandi 2 has coords; it should be chosen as nearest
        realized = {1: 1500.0, 2: 1200.0}
        r = nearest_mandi_regret(realized, farmer_lat=20.0, farmer_lon=73.8, mandis=mandis)
        # best=1500; nearest_with_coords=mandi2=1200 → regret=300
        assert r == pytest.approx(300.0)

    def test_regret_is_non_negative(self, minimal_mandis_with_coords) -> None:
        realized = {1: 900.0, 2: 1000.0, 3: 800.0}
        r = nearest_mandi_regret(
            realized, farmer_lat=20.0, farmer_lon=73.8, mandis=minimal_mandis_with_coords
        )
        assert r is not None
        assert r >= 0.0


class TestSummarizeBacktest:
    def _make_backtest(self) -> pd.DataFrame:
        # 3 dates: regret@1 = [0, 100, 200], nearest_mandi_regret = [50, 50, 50]
        return pd.DataFrame(
            {
                "as_of_date": ["2025-10-01", "2025-10-02", "2025-10-03"],
                "regret_at_1": [0.0, 100.0, 200.0],
                "regret_at_3": [0.0, 0.0, 100.0],
                "nearest_mandi_regret": [50.0, 50.0, 50.0],
                "n_dropped": [1, 0, 2],
            }
        )

    def test_empty_frame_returns_empty_dict(self) -> None:
        result = summarize_backtest(pd.DataFrame(), k_values=[1, 3])
        assert result == {}

    def test_mean_regret_correct(self) -> None:
        df = self._make_backtest()
        result = summarize_backtest(df, k_values=[1])
        assert result["regret_at_1_mean"] == pytest.approx(100.0)

    def test_median_regret_correct(self) -> None:
        df = self._make_backtest()
        result = summarize_backtest(df, k_values=[1])
        assert result["regret_at_1_median"] == pytest.approx(100.0)

    def test_optimal_rate_fraction_regret_le_zero(self) -> None:
        df = self._make_backtest()
        result = summarize_backtest(df, k_values=[1])
        # only row 0 has regret=0 -> 1/3
        assert result["optimal_rate_1"] == pytest.approx(1 / 3)

    def test_beats_nearest_fraction(self) -> None:
        df = self._make_backtest()
        result = summarize_backtest(df, k_values=[1])
        # regret@1 < nearest(50) only for row 0 (0 < 50) -> 1/3
        assert result["beats_nearest_1"] == pytest.approx(1 / 3)

    def test_nearest_mandi_mean_and_median(self) -> None:
        df = self._make_backtest()
        result = summarize_backtest(df, k_values=[1])
        assert result["nearest_mandi_regret_mean"] == pytest.approx(50.0)
        assert result["nearest_mandi_regret_median"] == pytest.approx(50.0)

    def test_keys_present_for_each_k(self) -> None:
        df = self._make_backtest()
        result = summarize_backtest(df, k_values=[1, 3])
        for k in [1, 3]:
            assert f"regret_at_{k}_mean" in result
            assert f"regret_at_{k}_median" in result
            assert f"optimal_rate_{k}" in result
            assert f"beats_nearest_{k}" in result
        assert "nearest_mandi_regret_mean" in result
        assert "nearest_mandi_regret_median" in result
        assert "n_dates" in result
        assert "date_min" in result
        assert "date_max" in result
        assert "n_dropped" in result

    def test_n_dropped_sum(self) -> None:
        df = self._make_backtest()
        result = summarize_backtest(df, k_values=[1])
        assert result["n_dropped"] == 3

    def test_n_dates(self) -> None:
        df = self._make_backtest()
        result = summarize_backtest(df, k_values=[1])
        assert result["n_dates"] == 3

    def test_rates_are_fractions_not_percentages(self) -> None:
        df = self._make_backtest()
        result = summarize_backtest(df, k_values=[1])
        assert 0.0 <= result["optimal_rate_1"] <= 1.0
        assert 0.0 <= result["beats_nearest_1"] <= 1.0


class TestBacktestRecommendations:
    """Integration tests for the full backtest loop.

    Regression guard: predictions carry a ``market_name`` column that collides
    with the one score_recommendations pulls from the mandis frame. The loop must
    drop it before scoring, otherwise every date fails silently and the backtest
    returns zero rows (the Milestone G review bug).
    """

    @pytest.fixture()
    def mandis(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "market_id": [1, 2],
                "market_name": ["MandiA", "MandiB"],
                "district_name": ["Nashik", "Pune"],
                "latitude": [20.0, 18.5],
                "longitude": [73.8, 73.9],
            }
        )

    @pytest.fixture()
    def predictions(self) -> pd.DataFrame:
        # One as-of date (2025-10-15); target_date = 2025-10-22. market_name present
        # on purpose to exercise the merge-collision guard.
        return pd.DataFrame(
            {
                "date": ["2025-10-15", "2025-10-15"],
                "market_id": [1, 2],
                "market_name": ["MandiA", "MandiB"],
                "mandi_id": ["mh__a", "mh__b"],
                "district": ["Nashik", "Pune"],
                "target_price_t_plus_7": [1500.0, 1300.0],
                "split": ["test", "test"],
                "model": ["moving_average_7d", "moving_average_7d"],
                "prediction": [1450.0, 1280.0],
            }
        )

    @pytest.fixture()
    def panel(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "market_id": [1, 2],
                "date": ["2025-10-22", "2025-10-22"],
                "modal_price_inr_qtl": [1500.0, 1300.0],
                "is_observed": [True, True],
            }
        )

    def _run(self, panel, mandis, predictions, k_values=(1, 3)):
        return backtest_recommendations(
            panel=panel,
            mandis=mandis,
            predictions=predictions,
            k_values=list(k_values),
            farmer_lat=19.9975,
            farmer_lon=73.78981,
            cost_per_km_per_quintal=4.0,
            road_distance_factor=1.3,
            uncertainty_penalty_weight=0.3,
            low_max_interval_pct=0.10,
            high_min_interval_pct=0.25,
            lower_residual=-210.0,
            upper_residual=292.0,
        )

    def test_produces_one_row_per_as_of_date(self, panel, mandis, predictions) -> None:
        result = self._run(panel, mandis, predictions)
        assert len(result) == 1
        assert result["as_of_date"].iloc[0] == "2025-10-15"
        assert result["target_date"].iloc[0] == "2025-10-22"

    def test_does_not_silently_return_empty_on_market_name_collision(
        self, panel, mandis, predictions
    ) -> None:
        # The regression: predictions has market_name; must still produce rows.
        result = self._run(panel, mandis, predictions)
        assert not result.empty
        assert "regret_at_1" in result.columns
        assert "nearest_mandi_regret" in result.columns

    def test_raises_when_scoring_fails(self, panel, predictions) -> None:
        # mandis missing district_name -> score_recommendations raises on every date;
        # the loop must surface it, not swallow it into an empty frame.
        broken_mandis = pd.DataFrame(
            {
                "market_id": [1, 2],
                "market_name": ["MandiA", "MandiB"],
                # district_name intentionally absent
                "latitude": [20.0, 18.5],
                "longitude": [73.8, 73.9],
            }
        )
        with pytest.raises(RuntimeError, match="score_recommendations failed"):
            self._run(panel, broken_mandis, predictions)
