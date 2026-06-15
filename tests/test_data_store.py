from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from mandipulse.data.store import read_csv_via_duckdb

GOLDEN_DIR = Path(__file__).parent / "golden"


class TestReadCsvViaDuckdb:
    def test_parity_with_read_csv_shape_and_columns(self) -> None:
        """read_csv_via_duckdb returns same shape and column names as pd.read_csv."""
        path = GOLDEN_DIR / "clean_mandi_prices.csv"
        expected = pd.read_csv(path)
        got = read_csv_via_duckdb(path)
        assert got.shape == expected.shape
        assert list(got.columns) == list(expected.columns)

    def test_parity_numeric_columns(self) -> None:
        """Numeric columns match pd.read_csv exactly (DuckDB infers floats/ints the same)."""
        path = GOLDEN_DIR / "clean_mandi_prices.csv"
        expected = pd.read_csv(path)
        got = read_csv_via_duckdb(path)
        numeric_cols = expected.select_dtypes(include="number").columns.tolist()
        # Sort by market_id + modal_price for stable row alignment
        sort_cols = [c for c in ("market_id", "modal_price_inr_qtl") if c in expected.columns]
        if sort_cols:
            expected = expected.sort_values(sort_cols).reset_index(drop=True)
            got = got.sort_values(sort_cols).reset_index(drop=True)
        pd.testing.assert_frame_equal(
            got[numeric_cols],
            expected[numeric_cols],
            check_dtype=False,
        )

    def test_date_column_parsed_as_datetime(self) -> None:
        """parse_dates=['date'] yields a datetime column.

        DuckDB returns datetime64[us]; pd.to_datetime returns datetime64[ns].
        Both are valid — compare string representations to avoid resolution mismatch.
        """
        path = GOLDEN_DIR / "clean_mandi_prices.csv"
        expected = pd.read_csv(path)
        expected["date"] = pd.to_datetime(expected["date"])

        got = read_csv_via_duckdb(path, parse_dates=["date"])

        assert pd.api.types.is_datetime64_any_dtype(got["date"]), "date not parsed as datetime"
        # Compare date values as strings (YYYY-MM-DD) ignoring ns vs us resolution
        got_dates = got["date"].dt.strftime("%Y-%m-%d").sort_values().reset_index(drop=True)
        exp_dates = expected["date"].dt.strftime("%Y-%m-%d").sort_values().reset_index(drop=True)
        pd.testing.assert_series_equal(got_dates, exp_dates, check_names=False)

    def test_missing_file_raises_file_not_found(self) -> None:
        """read_csv_via_duckdb raises FileNotFoundError for absent CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            missing = Path(tmpdir) / "nonexistent.csv"
            with pytest.raises(FileNotFoundError):
                read_csv_via_duckdb(missing)

    def test_roundtrip_numeric_only_csv(self) -> None:
        """Write a numeric CSV and read it back via DuckDB — values match exactly."""
        df = pd.DataFrame({"market_id": [1, 2], "price": [1200.0, 1350.5]})
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.csv"
            df.to_csv(path, index=False)
            got = read_csv_via_duckdb(path)
        pd.testing.assert_frame_equal(got, df, check_dtype=False)

    def test_returns_dataframe(self) -> None:
        path = GOLDEN_DIR / "forecast_outputs_7d.csv"
        result = read_csv_via_duckdb(path)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    def test_no_parse_dates_required_columns_present(self) -> None:
        """Without parse_dates, the call still succeeds and returns all columns."""
        path = GOLDEN_DIR / "clean_mandi_prices.csv"
        got = read_csv_via_duckdb(path)
        assert "date" in got.columns
        assert len(got) > 0
