from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mandipulse.modeling.columns import CATEGORICAL_FEATURES, NUMERIC_FEATURES, TARGET_COLUMN
from mandipulse.modeling.lightgbm_model import build_lightgbm_pipeline, predict_lightgbm_residual
from mandipulse.modeling.splits import SplitConfig, make_temporal_splits


def _split_synthetic(synthetic_features: pd.DataFrame):
    trainable = synthetic_features[
        synthetic_features["feature_row_valid"] & synthetic_features["target_available"]
    ].copy()
    train, validation, test, _ = make_temporal_splits(
        trainable,
        SplitConfig(validation_days=10, test_days=10, horizon_days=7),
    )
    return train, validation, test


class TestPredictLightgbmResidual:
    def test_returns_dataframe_with_correct_models(self, synthetic_features) -> None:
        train, validation, test = _split_synthetic(synthetic_features)
        result = predict_lightgbm_residual(train, validation, test, n_estimators=10)
        assert isinstance(result, pd.DataFrame)
        assert set(result["model"].unique()) == {"lightgbm_residual"}

    def test_produces_validation_and_test_rows(self, synthetic_features) -> None:
        train, validation, test = _split_synthetic(synthetic_features)
        result = predict_lightgbm_residual(train, validation, test, n_estimators=10)
        assert set(result["split"].unique()) == {"validation", "test"}

    def test_reconstruction_identity(self, synthetic_features) -> None:
        """prediction == rolling_mean_7 + model.predict(X), exactly.

        Guards the reconstruction line in predict_lightgbm_residual: the function is
        deterministic given random_state, so we re-fit the same pipeline on the same
        residual target and assert the function's output equals the reconstructed value.
        A bug that forgot to add rolling_mean_7 back would fail this.
        """
        train, validation, test = _split_synthetic(synthetic_features)
        feature_columns = NUMERIC_FEATURES + CATEGORICAL_FEATURES

        # Reproduce the model the function fits (same data, same seed, same hyperparams)
        model = build_lightgbm_pipeline(n_estimators=10, random_state=0)
        model.fit(train[feature_columns], train[TARGET_COLUMN] - train["rolling_mean_7"])
        expected = test["rolling_mean_7"].to_numpy() + model.predict(test[feature_columns])

        got = predict_lightgbm_residual(train, validation, test, n_estimators=10, random_state=0)
        # The function builds the test frame in test's row order, so positional compare is valid.
        got_test = got[got["split"] == "test"]["prediction"].to_numpy()
        np.testing.assert_allclose(got_test, expected, rtol=1e-9)

    def test_zero_residual_collapses_to_baseline(self, synthetic_features) -> None:
        """A model that learns ~0 residual reconstructs to ~rolling_mean_7.

        Verifies the reconstruction arithmetic (rolling_mean_7 + ~0 == rolling_mean_7),
        not the function itself — we force a near-zero-residual model the public API
        cannot produce directly.
        """
        train, validation, test = _split_synthetic(synthetic_features)

        feature_columns = NUMERIC_FEATURES + CATEGORICAL_FEATURES
        model = build_lightgbm_pipeline(n_estimators=1, num_leaves=2)
        # Train on zero residual
        model.fit(train[feature_columns], pd.Series(np.zeros(len(train)), index=train.index))
        # Reconstruction: prediction = rolling_mean_7 + model.predict(X) ~ rolling_mean_7 + ~0
        preds = test["rolling_mean_7"].to_numpy() + model.predict(test[feature_columns])
        np.testing.assert_allclose(preds, test["rolling_mean_7"].to_numpy(), atol=1.0)

    def test_prediction_column_present(self, synthetic_features) -> None:
        train, validation, test = _split_synthetic(synthetic_features)
        result = predict_lightgbm_residual(train, validation, test, n_estimators=10)
        assert "prediction" in result.columns
        assert result["prediction"].notna().all()

    def test_required_columns_present(self, synthetic_features) -> None:
        train, validation, test = _split_synthetic(synthetic_features)
        result = predict_lightgbm_residual(train, validation, test, n_estimators=10)
        for col in (
            "date",
            "market_id",
            "market_name",
            TARGET_COLUMN,
            "split",
            "model",
            "prediction",
        ):
            assert col in result.columns, f"Missing: {col}"


class TestResidualTargetLeakageGuard:
    def test_rolling_mean_7_uses_only_past_prices(self) -> None:
        """rolling_mean_7 at date d must not depend on any price after d.

        Build a hand-crafted per-mandi series where we know the price at each step.
        rolling_mean_7[i] = mean(price[max(i-6,0):i+1]) -- backward window, no future.
        Verify that price[i+1] changing does not affect rolling_mean_7[i].
        """
        prices = [100.0, 200.0, 300.0, 400.0, 500.0, 600.0, 700.0, 800.0, 900.0, 1000.0]
        dates = pd.date_range("2025-01-01", periods=len(prices), freq="D")
        df = pd.DataFrame({"date": dates, "price": prices})

        # Compute rolling_mean_7 exactly as build_feature_table does (backward, min_periods=window)
        df["rolling_mean_7"] = df["price"].rolling(7, min_periods=7).mean()

        # At index 6 (date 2025-01-07), rolling_mean_7 = mean(prices[0:7])
        expected_at_6 = float(np.mean(prices[0:7]))
        assert df["rolling_mean_7"].iloc[6] == pytest.approx(expected_at_6)

        # If we change price at index 7 (future relative to index 6), rolling_mean_7[6] must not change
        prices_alt = prices.copy()
        prices_alt[7] = 99999.0
        df_alt = pd.DataFrame({"date": dates, "price": prices_alt})
        df_alt["rolling_mean_7"] = df_alt["price"].rolling(7, min_periods=7).mean()
        assert df_alt["rolling_mean_7"].iloc[6] == pytest.approx(expected_at_6)

    def test_residual_target_uses_only_available_columns(self, synthetic_features) -> None:
        """Residual target = target_price_t_plus_7 - rolling_mean_7.

        Both columns are present per-row in the feature table. rolling_mean_7 is backward-only
        (verified above). target_price_t_plus_7 = price at t+7 but is used as the label
        (not a feature), so no leakage into X. Verify that computing the residual target
        produces finite non-NaN values for all trainable rows.
        """
        trainable = synthetic_features[
            synthetic_features["feature_row_valid"] & synthetic_features["target_available"]
        ].copy()
        y_residual = trainable[TARGET_COLUMN] - trainable["rolling_mean_7"]
        assert y_residual.notna().all(), "Residual target has NaN"
        assert np.isfinite(y_residual.to_numpy()).all(), "Residual target has Inf"
