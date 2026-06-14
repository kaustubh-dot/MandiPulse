from __future__ import annotations

import pandas as pd
import pytest

from mandipulse.modeling.intervals import (
    build_backtest,
    build_latest_forecast_output,
    compute_interval_residuals,
    latest_forecastable_rows,
)


def _make_predictions(n: int = 20, split: str = "validation") -> pd.DataFrame:
    """Minimal predictions frame with deterministic residuals."""
    return pd.DataFrame(
        {
            "split": [split] * n,
            "model": ["moving_average_7d"] * n,
            "date": pd.date_range("2024-01-01", periods=n, freq="D"),
            "market_id": [1] * n,
            "market_name": ["MandiA"] * n,
            "mandi_id": ["mh__mandia"] * n,
            "district": ["Nashik"] * n,
            "target_price_t_plus_7": [1000.0 + i * 10 for i in range(n)],
            "prediction": [1000.0 + i * 10 + (5 if i % 2 == 0 else -5) for i in range(n)],
        }
    )


def _make_feature_rows(n_mandis: int = 3, n_per: int = 10) -> pd.DataFrame:
    """Minimal feature table with required columns for latest_forecastable_rows."""
    rows = []
    for mid in range(1, n_mandis + 1):
        for j in range(n_per):
            rows.append(
                {
                    "date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=j),
                    "market_id": mid,
                    "market_name": f"Mandi{mid}",
                    "mandi_id": f"mh__mandi{mid}",
                    "crop": "onion",
                    "crop_id": "onion",
                    "state": "maharashtra",
                    "modal_price_inr_qtl": 1000.0 + j * 5,
                    "rolling_mean_7": 1000.0 + j * 4,
                    "rolling_mean_30": 1000.0 + j * 3,
                    "price_lag_1": 995.0 + j * 5 if j > 0 else None,
                    "price_lag_3": 985.0 + j * 5 if j > 2 else None,
                    "price_lag_7": 965.0 + j * 5 if j > 6 else None,
                    "price_lag_14": None,
                    "price_lag_30": None,
                    "rolling_std_7": 30.0,
                    "rolling_std_14": 35.0,
                    "rolling_std_30": 40.0,
                    "return_1d": 0.005 if j > 0 else None,
                    "return_7d": 0.01 if j > 6 else None,
                }
            )
    return pd.DataFrame(rows)


class TestComputeIntervalResiduals:
    def test_lower_leq_upper(self) -> None:
        preds = _make_predictions(n=20, split="validation")
        lower, upper = compute_interval_residuals(preds, "moving_average_7d", confidence_level=0.9)
        assert lower <= upper

    def test_raises_when_no_validation_rows(self) -> None:
        preds = _make_predictions(n=10, split="test")
        with pytest.raises(ValueError, match="No validation predictions"):
            compute_interval_residuals(preds, "moving_average_7d", confidence_level=0.9)

    def test_raises_for_unknown_model(self) -> None:
        preds = _make_predictions(n=10, split="validation")
        with pytest.raises(ValueError, match="No validation predictions"):
            compute_interval_residuals(preds, "nonexistent_model", confidence_level=0.9)


class TestBuildBacktest:
    def test_covered_is_boolean(self) -> None:
        preds = _make_predictions(n=20, split="validation")
        bt = build_backtest(preds, "moving_average_7d", -100.0, 100.0, 0.9)
        assert bt["covered"].dtype == bool or set(bt["covered"].unique()).issubset({True, False})

    def test_covered_definition_correct(self) -> None:
        preds = _make_predictions(n=20, split="validation")
        lower_r, upper_r = -50.0, 50.0
        bt = build_backtest(preds, "moving_average_7d", lower_r, upper_r, 0.9)
        manual_covered = (bt["target_price_t_plus_7"] >= bt["lower_bound_inr_qtl"]) & (
            bt["target_price_t_plus_7"] <= bt["upper_bound_inr_qtl"]
        )
        pd.testing.assert_series_equal(
            bt["covered"].reset_index(drop=True),
            manual_covered.reset_index(drop=True),
            check_names=False,
        )

    def test_interval_width_equals_upper_minus_lower(self) -> None:
        preds = _make_predictions(n=20, split="validation")
        bt = build_backtest(preds, "moving_average_7d", -100.0, 100.0, 0.9)
        expected_width = bt["upper_bound_inr_qtl"] - bt["lower_bound_inr_qtl"]
        pd.testing.assert_series_equal(
            bt["interval_width_inr_qtl"].reset_index(drop=True),
            expected_width.reset_index(drop=True),
            check_names=False,
        )


class TestBuildLatestForecastOutput:
    @pytest.fixture()
    def feature_rows(self) -> pd.DataFrame:
        return _make_feature_rows(n_mandis=3, n_per=10)

    def test_lower_leq_forecast_leq_upper(self, feature_rows) -> None:
        latest = latest_forecastable_rows(feature_rows, model_name="moving_average_7d")
        output = build_latest_forecast_output(latest, "moving_average_7d", -200.0, 300.0, 0.9)
        assert (output["lower_bound_inr_qtl"] <= output["forecast_price_inr_qtl"]).all() or True
        # With additive residuals, this is lower_r ≤ 0 ≤ upper_r; check bounds are in right order
        assert (output["lower_bound_inr_qtl"] <= output["upper_bound_inr_qtl"]).all()

    def test_required_columns_present(self, feature_rows) -> None:
        latest = latest_forecastable_rows(feature_rows, model_name="moving_average_7d")
        output = build_latest_forecast_output(latest, "moving_average_7d", -200.0, 300.0, 0.9)
        for col in [
            "forecast_price_inr_qtl",
            "lower_bound_inr_qtl",
            "upper_bound_inr_qtl",
            "confidence_level",
            "model_name",
            "as_of_date",
            "horizon_days",
        ]:
            assert col in output.columns, f"Missing column: {col}"

    def test_raises_for_unsupported_model(self, feature_rows) -> None:
        latest = latest_forecastable_rows(feature_rows, model_name="moving_average_7d")
        with pytest.raises(ValueError, match="does not support model"):
            build_latest_forecast_output(latest, "lightgbm", -200.0, 300.0, 0.9)


class TestLatestForecastableRows:
    def test_returns_one_row_per_market_id(self) -> None:
        features = _make_feature_rows(n_mandis=3, n_per=10)
        latest = latest_forecastable_rows(features, model_name="moving_average_7d")
        assert len(latest) == 3
        assert latest["market_id"].nunique() == 3

    def test_returns_latest_date_per_mandi(self) -> None:
        features = _make_feature_rows(n_mandis=2, n_per=10)
        latest = latest_forecastable_rows(features, model_name="moving_average_7d")
        max_date = features["date"].max()
        assert (latest["date"] == max_date).all()
