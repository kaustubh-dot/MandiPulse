from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

SAMPLE_DIR = Path(__file__).parent.parent / "data" / "sample"


@pytest.fixture(autouse=True)
def _reset_loaders_state():
    """Reset loaders module state before/after each test."""
    import mandipulse.data.loaders as loaders

    loaders._running_on_sample = False
    yield
    loaders._running_on_sample = False


class TestResolveOrSample:
    def test_full_path_returned_when_exists(self) -> None:
        import mandipulse.data.loaders as loaders

        with tempfile.TemporaryDirectory() as tmpdir:
            full = Path(tmpdir) / "full.csv"
            full.write_text("a,b\n1,2\n")
            result, used_sample = loaders.resolve_or_sample(full, "full.csv")
        assert result == full
        assert not used_sample

    def test_falls_back_to_sample_when_full_absent(self) -> None:
        import mandipulse.data.loaders as loaders

        with tempfile.TemporaryDirectory() as tmpdir:
            missing_full = Path(tmpdir) / "nonexistent.csv"
            sample_tmp = Path(tmpdir) / "sample"
            sample_tmp.mkdir()
            (sample_tmp / "forecast_outputs_7d.csv").write_text("a,b\n1,2\n")

            with patch.object(loaders, "SAMPLE_DIR", sample_tmp):
                result, used_sample = loaders.resolve_or_sample(
                    missing_full, "forecast_outputs_7d.csv"
                )

        assert result == sample_tmp / "forecast_outputs_7d.csv"
        assert used_sample

    def test_sets_running_on_sample_flag_when_fallback_used(self) -> None:
        import mandipulse.data.loaders as loaders

        assert not loaders.running_on_sample()
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_full = Path(tmpdir) / "nonexistent.csv"
            sample_tmp = Path(tmpdir) / "sample"
            sample_tmp.mkdir()
            (sample_tmp / "forecast_outputs_7d.csv").write_text("a,b\n1,2\n")

            with patch.object(loaders, "SAMPLE_DIR", sample_tmp):
                loaders.resolve_or_sample(missing_full, "forecast_outputs_7d.csv")

        assert loaders.running_on_sample()

    def test_returns_full_path_when_neither_exists(self) -> None:
        import mandipulse.data.loaders as loaders

        with tempfile.TemporaryDirectory() as tmpdir:
            missing_full = Path(tmpdir) / "nonexistent.csv"
            empty_sample_dir = Path(tmpdir) / "empty_sample"
            empty_sample_dir.mkdir()

            with patch.object(loaders, "SAMPLE_DIR", empty_sample_dir):
                result, used_sample = loaders.resolve_or_sample(missing_full, "nonexistent.csv")

        assert result == missing_full
        assert not used_sample


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
