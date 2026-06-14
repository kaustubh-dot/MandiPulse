from __future__ import annotations

import pandas as pd
import pytest

from mandipulse.recommend.evaluation import (
    nearest_mandi_regret,
    realized_net_price,
    regret_at_k,
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
