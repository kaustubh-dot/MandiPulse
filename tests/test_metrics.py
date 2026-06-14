from __future__ import annotations

import math

import pandas as pd
import pytest

from mandipulse.modeling.metrics import (
    metric_row,
    smape,
    summarize_predictions,
)


class TestSmape:
    def test_identical_series_is_zero(self) -> None:
        y = pd.Series([100.0, 200.0, 300.0])
        assert smape(y, y) == pytest.approx(0.0, abs=1e-9)

    def test_symmetric(self) -> None:
        y_true = pd.Series([100.0, 200.0])
        y_pred = pd.Series([120.0, 180.0])
        assert smape(y_true, y_pred) == pytest.approx(smape(y_pred, y_true), rel=1e-9)

    def test_known_value(self) -> None:
        # |100-150| / ((100+150)/2) = 50/125 = 0.4  → 40%
        assert smape([100.0], [150.0]) == pytest.approx(40.0, rel=1e-6)

    def test_all_zero_denominator_returns_nan(self) -> None:
        result = smape([0.0, 0.0], [0.0, 0.0])
        assert math.isnan(result)


class TestMetricRow:
    def test_mae_matches_hand_computed(self) -> None:
        y_true = pd.Series([100.0, 200.0, 300.0])
        y_pred = pd.Series([110.0, 190.0, 310.0])
        row = metric_row("test_model", "validation", y_true, y_pred, scale=100.0)
        expected_mae = (10 + 10 + 10) / 3
        assert row["mae"] == pytest.approx(expected_mae, abs=0.01)

    def test_rmse_matches_hand_computed(self) -> None:
        y_true = pd.Series([100.0, 200.0])
        y_pred = pd.Series([110.0, 210.0])
        row = metric_row("m", "v", y_true, y_pred, scale=10.0)
        expected_rmse = 10.0
        assert row["rmse"] == pytest.approx(expected_rmse, abs=0.01)

    def test_mase_equals_mae_over_scale(self) -> None:
        y_true = pd.Series([100.0, 200.0, 300.0])
        y_pred = pd.Series([110.0, 190.0, 310.0])
        scale = 50.0
        row = metric_row("m", "v", y_true, y_pred, scale=scale)
        expected_mase = round(row["mae"] / scale, 3)
        assert row["mase"] == pytest.approx(expected_mase, rel=1e-6)

    def test_row_contains_required_keys(self) -> None:
        y = pd.Series([1000.0, 1100.0])
        row = metric_row("m", "v", y, y, scale=100.0)
        for key in ("model", "split", "rows", "mae", "rmse", "smape_pct", "mase"):
            assert key in row


class TestSummarizePredictions:
    @pytest.fixture()
    def multi_model_predictions(self) -> pd.DataFrame:
        rows = []
        for model in ["model_a", "model_b"]:
            for split in ["validation", "test"]:
                for i in range(10):
                    rows.append(
                        {
                            "model": model,
                            "split": split,
                            "date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=i),
                            "market_id": 1,
                            "market_name": "MandiA",
                            "target_price_t_plus_7": 1000.0 + i * 5,
                            "prediction": 1000.0 + i * 5 + (10 if model == "model_a" else 20),
                        }
                    )
        return pd.DataFrame(rows)

    def test_one_row_per_model_split(self, multi_model_predictions, synthetic_features) -> None:
        from mandipulse.modeling.splits import SplitConfig, make_temporal_splits

        trainable = synthetic_features[synthetic_features["feature_row_valid"].astype(bool)].copy()
        cfg = SplitConfig(validation_days=14, test_days=14, horizon_days=7)
        train, _, _, _ = make_temporal_splits(trainable, cfg)

        summary = summarize_predictions(multi_model_predictions, train)
        assert len(summary) == 4  # 2 models × 2 splits

    def test_sorted_by_split_then_mae(self, multi_model_predictions, synthetic_features) -> None:
        from mandipulse.modeling.splits import SplitConfig, make_temporal_splits

        trainable = synthetic_features[synthetic_features["feature_row_valid"].astype(bool)].copy()
        cfg = SplitConfig(validation_days=14, test_days=14, horizon_days=7)
        train, _, _, _ = make_temporal_splits(trainable, cfg)

        summary = summarize_predictions(multi_model_predictions, train)
        # validation rows should come before test rows
        splits = summary["split"].tolist()
        val_indices = [i for i, s in enumerate(splits) if s == "validation"]
        test_indices = [i for i, s in enumerate(splits) if s == "test"]
        if val_indices and test_indices:
            assert max(val_indices) < min(test_indices)
