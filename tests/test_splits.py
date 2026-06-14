from __future__ import annotations

import pandas as pd
import pytest

from mandipulse.modeling.splits import (
    SplitConfig,
    apply_row_filter,
    make_temporal_splits,
)


class TestMakeTemporalSplits:
    def test_no_date_overlap_between_splits(self, synthetic_features) -> None:
        trainable = synthetic_features[synthetic_features["feature_row_valid"].astype(bool)].copy()
        cfg = SplitConfig(validation_days=14, test_days=14, horizon_days=7)
        train, val, test, _ = make_temporal_splits(trainable, cfg)

        train_dates = set(train["date"].dt.date)
        val_dates = set(val["date"].dt.date)
        test_dates = set(test["date"].dt.date)

        assert train_dates.isdisjoint(val_dates), "train and validation dates overlap"
        assert train_dates.isdisjoint(test_dates), "train and test dates overlap"
        assert val_dates.isdisjoint(test_dates), "validation and test dates overlap"

    def test_train_end_before_validation_start(self, synthetic_features) -> None:
        trainable = synthetic_features[synthetic_features["feature_row_valid"].astype(bool)].copy()
        cfg = SplitConfig(validation_days=14, test_days=14, horizon_days=7)
        train, val, test, dates = make_temporal_splits(trainable, cfg)

        assert dates.train_end < dates.validation_start

    def test_validation_end_before_test_start(self, synthetic_features) -> None:
        trainable = synthetic_features[synthetic_features["feature_row_valid"].astype(bool)].copy()
        cfg = SplitConfig(validation_days=14, test_days=14, horizon_days=7)
        train, val, test, dates = make_temporal_splits(trainable, cfg)

        assert dates.validation_end < dates.test_start

    def test_purge_gap_at_least_horizon_days(self, synthetic_features) -> None:
        """Gap between train_end and validation_start must be ≥ horizon_days."""
        trainable = synthetic_features[synthetic_features["feature_row_valid"].astype(bool)].copy()
        horizon = 7
        cfg = SplitConfig(validation_days=14, test_days=14, horizon_days=horizon)
        train, val, test, dates = make_temporal_splits(trainable, cfg)

        gap_days = (dates.validation_start - dates.train_end).days
        assert gap_days >= horizon, f"Purge gap {gap_days} < horizon {horizon}"

    def test_raises_on_too_little_data(self) -> None:
        tiny = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=5, freq="D"),
                "market_id": [1] * 5,
                "modal_price_inr_qtl": [1000.0] * 5,
                "target_price_t_plus_7": [1010.0] * 5,
            }
        )
        cfg = SplitConfig(validation_days=30, test_days=30, horizon_days=7)
        with pytest.raises(ValueError, match="empty partition"):
            make_temporal_splits(tiny, cfg)


class TestApplyRowFilter:
    def test_all_filter_returns_all_rows(self, synthetic_features) -> None:
        result = apply_row_filter(synthetic_features, "all")
        assert len(result) == len(synthetic_features)

    def test_observed_only_keeps_only_observed(self, synthetic_features) -> None:
        result = apply_row_filter(synthetic_features, "observed_only")
        assert result["is_observed"].astype(bool).all()
        assert result["target_observed_t_plus_7"].astype(bool).all()

    def test_unknown_filter_raises(self, synthetic_features) -> None:
        with pytest.raises(ValueError, match="Unsupported row filter"):
            apply_row_filter(synthetic_features, "bogus_filter")


class TestLoadTrainableFeatures:
    def test_loads_golden_feature_table(self, golden_feature_table) -> None:
        """Golden fixture should have feature_row_valid and required columns."""
        assert "feature_row_valid" in golden_feature_table.columns
        assert "modal_price_inr_qtl" in golden_feature_table.columns
        assert "target_price_t_plus_7" in golden_feature_table.columns
        assert "date" in golden_feature_table.columns

    def test_golden_has_trainable_rows(self, golden_feature_table) -> None:
        trainable = golden_feature_table[golden_feature_table["feature_row_valid"].astype(bool)]
        assert len(trainable) > 0

    def test_golden_dates_are_datetime(self, golden_feature_table) -> None:
        assert pd.api.types.is_datetime64_any_dtype(golden_feature_table["date"])
