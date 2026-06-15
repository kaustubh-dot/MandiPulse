from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

SAMPLE_DIR = Path(__file__).parent.parent / "data" / "sample"


@pytest.fixture(autouse=True)
def _reload_data_access():
    """Re-import data_access before each test so module-level state is fresh."""
    import mandipulse.app.data_access as da

    da.RUNNING_ON_SAMPLE = False
    yield
    da.RUNNING_ON_SAMPLE = False


class TestResolveOrSample:
    def test_full_path_returned_when_exists(self) -> None:
        import mandipulse.app.data_access as da

        with tempfile.TemporaryDirectory() as tmpdir:
            full = Path(tmpdir) / "full.csv"
            full.write_text("a,b\n1,2\n")
            result = da._resolve_or_sample(full, "full.csv")
        assert result == full

    def test_falls_back_to_sample_when_full_absent(self) -> None:
        import mandipulse.app.data_access as da

        with tempfile.TemporaryDirectory() as tmpdir:
            missing_full = Path(tmpdir) / "nonexistent.csv"
            # Point the sample dir at a temp dir that has the file
            sample_tmp = Path(tmpdir) / "sample"
            sample_tmp.mkdir()
            (sample_tmp / "forecast_outputs_7d.csv").write_text("a,b\n1,2\n")

            with patch.object(da, "_SAMPLE_DIR", sample_tmp):
                result = da._resolve_or_sample(missing_full, "forecast_outputs_7d.csv")

        assert result == sample_tmp / "forecast_outputs_7d.csv"

    def test_sets_running_on_sample_flag_when_fallback_used(self) -> None:
        import mandipulse.app.data_access as da

        assert not da.RUNNING_ON_SAMPLE
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_full = Path(tmpdir) / "nonexistent.csv"
            sample_tmp = Path(tmpdir) / "sample"
            sample_tmp.mkdir()
            (sample_tmp / "forecast_outputs_7d.csv").write_text("a,b\n1,2\n")

            with patch.object(da, "_SAMPLE_DIR", sample_tmp):
                da._resolve_or_sample(missing_full, "forecast_outputs_7d.csv")

        assert da.RUNNING_ON_SAMPLE

    def test_returns_full_path_when_neither_exists(self) -> None:
        import mandipulse.app.data_access as da

        with tempfile.TemporaryDirectory() as tmpdir:
            missing_full = Path(tmpdir) / "nonexistent.csv"
            empty_sample_dir = Path(tmpdir) / "empty_sample"
            empty_sample_dir.mkdir()

            with patch.object(da, "_SAMPLE_DIR", empty_sample_dir):
                result = da._resolve_or_sample(missing_full, "nonexistent.csv")

        assert result == missing_full


@pytest.mark.skipif(
    not (SAMPLE_DIR / "forecast_outputs_7d.csv").exists(),
    reason="data/sample/ not present",
)
class TestDemoBundleIntegrity:
    def test_forecast_sample_loadable(self) -> None:
        df = pd.read_csv(SAMPLE_DIR / "forecast_outputs_7d.csv")
        assert len(df) > 0
        for col in (
            "market_id",
            "forecast_price_inr_qtl",
            "lower_bound_inr_qtl",
            "upper_bound_inr_qtl",
        ):
            assert col in df.columns, f"Missing column in forecast sample: {col}"

    def test_panel_sample_loadable(self) -> None:
        df = pd.read_csv(SAMPLE_DIR / "clean_mandi_prices.csv")
        assert len(df) > 0
        for col in (
            "date",
            "market_id",
            "market_name",
            "modal_price_inr_qtl",
            "is_observed",
            "is_imputed",
        ):
            assert col in df.columns, f"Missing column in panel sample: {col}"

    def test_feature_sample_loadable(self) -> None:
        df = pd.read_csv(SAMPLE_DIR / "feature_table_7d.csv")
        assert len(df) > 0
        for col in ("date", "market_id", "market_name", "feature_row_valid"):
            assert col in df.columns, f"Missing column in feature sample: {col}"

    def test_backtest_sample_loadable(self) -> None:
        bt_path = SAMPLE_DIR / "recommendation_backtest_7d.csv"
        if not bt_path.exists():
            pytest.skip("backtest sample not present")
        df = pd.read_csv(bt_path)
        assert len(df) > 0
