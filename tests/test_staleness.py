from __future__ import annotations

import pandas as pd

from mandipulse.app.data_access import add_staleness_days


def _make_forecasts(as_of_dates: list[str]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "market_id": list(range(1, len(as_of_dates) + 1)),
            "mandi": [f"Mandi{i}" for i in range(1, len(as_of_dates) + 1)],
            "as_of_date": as_of_dates,
            "forecast_price_inr_qtl": [1000.0] * len(as_of_dates),
        }
    )


class TestAddStaleness:
    def test_freshest_mandi_has_zero_staleness(self) -> None:
        df = _make_forecasts(["2025-10-28", "2025-10-30", "2025-10-29"])
        result = add_staleness_days(df)
        freshest_idx = result["as_of_date"] == "2025-10-30"
        assert int(result.loc[freshest_idx, "staleness_days"].iloc[0]) == 0

    def test_older_mandi_has_correct_staleness(self) -> None:
        df = _make_forecasts(["2025-10-17", "2025-10-30"])
        result = add_staleness_days(df)
        older_idx = result["as_of_date"] == "2025-10-17"
        assert int(result.loc[older_idx, "staleness_days"].iloc[0]) == 13

    def test_all_same_date_gives_all_zeros(self) -> None:
        df = _make_forecasts(["2025-10-30", "2025-10-30", "2025-10-30"])
        result = add_staleness_days(df)
        assert (result["staleness_days"] == 0).all()

    def test_returns_copy_original_unmutated(self) -> None:
        df = _make_forecasts(["2025-10-28", "2025-10-30"])
        original_cols = set(df.columns)
        result = add_staleness_days(df)
        assert "staleness_days" not in original_cols
        assert "staleness_days" not in df.columns
        assert "staleness_days" in result.columns

    def test_staleness_days_are_non_negative(self) -> None:
        df = _make_forecasts(["2025-10-15", "2025-10-22", "2025-10-30"])
        result = add_staleness_days(df)
        assert (result["staleness_days"] >= 0).all()

    def test_accepts_datetime_as_of_date(self) -> None:
        df = pd.DataFrame(
            {
                "market_id": [1, 2],
                "mandi": ["A", "B"],
                "as_of_date": pd.to_datetime(["2025-10-28", "2025-10-30"]),
                "forecast_price_inr_qtl": [1000.0, 1100.0],
            }
        )
        result = add_staleness_days(df)
        assert int(result.loc[result["mandi"] == "A", "staleness_days"].iloc[0]) == 2
