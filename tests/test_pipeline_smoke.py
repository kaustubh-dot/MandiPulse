from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

# Scripts are not a package; add scripts/ to path so we can import build functions.
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from build_feature_table import build_features  # noqa: E402
from mandipulse.modeling.baselines import predict_baselines  # noqa: E402
from mandipulse.modeling.splits import SplitConfig, make_temporal_splits  # noqa: E402
from mandipulse.recommend.engine import score_recommendations  # noqa: E402

_MANDIS_PATH = Path(__file__).parent.parent / "data" / "external" / "mvp_mandis.csv"

_SPLIT_CONFIG = SplitConfig(validation_days=90, test_days=90, horizon_days=7)

# Recommendation params from configs/recommendation.yaml
_REC_KWARGS: dict = dict(
    farmer_latitude=19.99750,
    farmer_longitude=73.78981,
    cost_per_km_per_quintal=4.0,
    road_distance_factor=1.3,
    uncertainty_penalty_weight=0.3,
    low_max_interval_pct=0.10,
    high_min_interval_pct=0.25,
    candidate_state="maharashtra",
)

# RULES-required columns at each terminal artifact
_FORECAST_RULES_COLS = {"lower_bound_inr_qtl", "upper_bound_inr_qtl", "forecast_price_inr_qtl"}
_REC_RULES_COLS = {
    "estimated_transport_cost_inr_qtl",
    "rank",
    "risk_level",
    "reason",
    "lower_bound_inr_qtl",
    "upper_bound_inr_qtl",
}


class TestPipelineSmoke:
    def test_clean_panel_to_features(self, golden_clean_panel: pd.DataFrame) -> None:
        """Stage 1→2: build_features wires clean panel into a trainable feature table."""
        features = build_features(golden_clean_panel, horizon_days=7)
        assert len(features) > 0

        # Columns that predict_baselines and make_temporal_splits consume
        downstream_required = {
            "market_id",
            "date",
            "rolling_mean_7",
            "target_price_t_plus_7",
            "feature_row_valid",
            "is_observed",
            "target_observed_t_plus_7",
        }
        missing = downstream_required - set(features.columns)
        assert not missing, f"Feature table missing downstream-required columns: {missing}"

        trainable = features[features["feature_row_valid"].astype(bool)]
        assert len(trainable) > 0, "No trainable rows produced from clean panel"

    def test_features_to_predictions(self, golden_feature_table: pd.DataFrame) -> None:
        """Stage 2→3: predict_baselines wires feature table into a predictions frame.

        Uses golden_feature_table (pre-computed) to avoid re-running build_features;
        this test guards wiring, not numeric output.
        """
        trainable = (
            golden_feature_table[golden_feature_table["feature_row_valid"].astype(bool)]
            .dropna(subset=["target_price_t_plus_7", "modal_price_inr_qtl"])
            .sort_values(["date", "market_id"])
            .reset_index(drop=True)
        )
        train, validation, test, _ = make_temporal_splits(trainable, _SPLIT_CONFIG)
        preds = predict_baselines(train, validation, test, ridge_alpha=1.0)

        assert len(preds) > 0
        for col in ("date", "market_id", "model", "split", "prediction", "target_price_t_plus_7"):
            assert col in preds.columns, f"Prediction frame missing column: {col}"

        # Both validation and test splits must be present
        assert set(preds["split"].unique()) >= {"validation", "test"}

    def test_forecasts_have_rules_columns(self, golden_forecasts: pd.DataFrame) -> None:
        """Forecast artifact carries RULES-required uncertainty columns."""
        missing = _FORECAST_RULES_COLS - set(golden_forecasts.columns)
        assert not missing, f"Forecast artifact missing RULES-required columns: {missing}"
        assert len(golden_forecasts) > 0

    @pytest.mark.skipif(
        not _MANDIS_PATH.exists(),
        reason="data/external/mvp_mandis.csv not present (local artifact)",
    )
    def test_forecasts_to_recommendations(self, golden_forecasts: pd.DataFrame) -> None:
        """Stage 6: score_recommendations wires forecast + mandi metadata into ranked recs.

        Asserts RULES-required columns: transport cost, alternatives (rank),
        risk_level + reason, and uncertainty bounds.
        """
        mandis = pd.read_csv(_MANDIS_PATH)
        recs = score_recommendations(golden_forecasts, mandis, **_REC_KWARGS)

        assert len(recs) > 0
        missing = _REC_RULES_COLS - set(recs.columns)
        assert not missing, f"Recommendations missing RULES-required columns: {missing}"

        assert recs["risk_level"].isin({"low", "medium", "high"}).all()
        assert (recs["rank"] >= 1).all()
        assert recs["reason"].str.len().gt(0).all()
        assert (recs["estimated_transport_cost_inr_qtl"] >= 0).all()

        # Alternatives exist (more than one ranked option)
        assert len(recs) > 1, "Recommendation should surface multiple alternatives"
