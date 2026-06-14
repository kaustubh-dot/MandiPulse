from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pandas as pd

GOLDEN_DIR = Path(__file__).parent / "golden"

# ---------------------------------------------------------------------------
# Helper: point mandipulse.app.data_access path helpers at golden fixtures
# ---------------------------------------------------------------------------

_GOLDEN_PATHS = {
    "mandipulse.app.data_access.clean_panel_path": GOLDEN_DIR / "clean_mandi_prices.csv",
    "mandipulse.app.data_access.feature_table_path": GOLDEN_DIR / "feature_table_7d.csv",
    "mandipulse.app.data_access.forecast_outputs_path": GOLDEN_DIR / "forecast_outputs_7d.csv",
    "mandipulse.app.data_access.mvp_mandis_path": GOLDEN_DIR / "clean_mandi_prices.csv",
}


def _patch_paths():
    """Return a context manager that monkeypatches all path helpers."""
    patches = [patch(name, return_value=path) for name, path in _GOLDEN_PATHS.items()]
    return patches


class TestLoadCleanPanel:
    def test_returns_dataframe(self) -> None:
        from mandipulse.app import data_access

        with (
            patch.object(
                data_access, "clean_panel_path", return_value=GOLDEN_DIR / "clean_mandi_prices.csv"
            ),
        ):
            # Clear st.cache_data wrapper by calling the underlying function directly
            # via the __wrapped__ attribute if present, else call normally
            fn = getattr(data_access.load_clean_panel, "__wrapped__", data_access.load_clean_panel)
            df = fn()
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_date_column_is_datetime(self) -> None:
        from mandipulse.app import data_access

        with patch.object(
            data_access, "clean_panel_path", return_value=GOLDEN_DIR / "clean_mandi_prices.csv"
        ):
            fn = getattr(data_access.load_clean_panel, "__wrapped__", data_access.load_clean_panel)
            df = fn()
        assert pd.api.types.is_datetime64_any_dtype(df["date"])

    def test_required_columns_present(self) -> None:
        from mandipulse.app import data_access

        with patch.object(
            data_access, "clean_panel_path", return_value=GOLDEN_DIR / "clean_mandi_prices.csv"
        ):
            fn = getattr(data_access.load_clean_panel, "__wrapped__", data_access.load_clean_panel)
            df = fn()
        for col in ("date", "market_id", "market_name", "modal_price_inr_qtl", "is_observed"):
            assert col in df.columns, f"Missing column: {col}"


class TestLoadForecasts:
    def test_returns_dataframe_with_required_columns(self) -> None:
        from mandipulse.app import data_access

        with patch.object(
            data_access,
            "forecast_outputs_path",
            return_value=GOLDEN_DIR / "forecast_outputs_7d.csv",
        ):
            fn = getattr(data_access.load_forecasts, "__wrapped__", data_access.load_forecasts)
            df = fn()
        assert isinstance(df, pd.DataFrame)
        for col in (
            "mandi",
            "market_id",
            "forecast_price_inr_qtl",
            "lower_bound_inr_qtl",
            "upper_bound_inr_qtl",
            "confidence_level",
            "as_of_date",
            "model_name",
        ):
            assert col in df.columns, f"Missing column: {col}"


class TestLoadFeatureTable:
    def test_returns_dataframe(self) -> None:
        from mandipulse.app import data_access

        with patch.object(
            data_access, "feature_table_path", return_value=GOLDEN_DIR / "feature_table_7d.csv"
        ):
            fn = getattr(
                data_access.load_feature_table, "__wrapped__", data_access.load_feature_table
            )
            df = fn()
        assert isinstance(df, pd.DataFrame)
        assert pd.api.types.is_datetime64_any_dtype(df["date"])


class TestAvailableMandis:
    def test_returns_sorted_list(self, golden_forecasts) -> None:
        from mandipulse.app.data_access import available_mandis

        mandis = available_mandis(golden_forecasts)
        assert mandis == sorted(mandis)
        assert len(mandis) == golden_forecasts["mandi"].nunique()


class TestHistoryForMandi:
    def test_filters_by_market_id(self, golden_clean_panel) -> None:
        from mandipulse.app.data_access import history_for_mandi

        market_ids = golden_clean_panel["market_id"].unique()
        mid = int(market_ids[0])
        result = history_for_mandi(golden_clean_panel, mid)
        assert (result["market_id"] == mid).all()
        assert len(result) > 0

    def test_sorted_by_date(self, golden_clean_panel) -> None:
        from mandipulse.app.data_access import history_for_mandi

        mid = int(golden_clean_panel["market_id"].iloc[0])
        result = history_for_mandi(golden_clean_panel, mid)
        assert result["date"].is_monotonic_increasing
