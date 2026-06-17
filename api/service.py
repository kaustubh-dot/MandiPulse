from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mandipulse.config import load_yaml_config  # noqa: E402
from mandipulse.data.loaders import (  # noqa: E402
    read_forecasts,
    read_mandi_metadata,
)
from mandipulse.recommend.engine import risk_level as _risk_level  # noqa: E402
from mandipulse.recommend.engine import score_recommendations  # noqa: E402
from mandipulse.utils.text import slugify  # noqa: E402

from api.config import SUPPORTED_CROPS, SUPPORTED_HORIZONS, SUPPORTED_STATES  # noqa: E402
from api.errors import ApiError  # noqa: E402
from api.schemas import (  # noqa: E402
    ForecastResponse,
    MandiRecommendation,
    RecommendationResponse,
)

_REC_CFG = load_yaml_config("configs/recommendation.yaml")
_TC = _REC_CFG.get("transport_cost", {})
_RK = _REC_CFG.get("ranking", {})
_RT = _REC_CFG.get("risk_thresholds", {})

DEFAULT_COST_PER_KM: float = float(_TC.get("cost_per_km_per_quintal", 4.0))
DEFAULT_ROAD_FACTOR: float = float(_TC.get("road_distance_factor", 1.3))
DEFAULT_PENALTY: float = float(_RK.get("uncertainty_penalty_weight", 0.3))
LOW_MAX_PCT: float = float(_RT.get("low_max_interval_pct", 10)) / 100
HIGH_MIN_PCT: float = float(_RT.get("high_min_interval_pct", 25)) / 100


def _validate_scope(crop: str, state: str, horizon_days: int) -> None:
    if crop.lower() not in SUPPORTED_CROPS:
        raise ApiError(
            "UNSUPPORTED_CROP",
            f"Supported crops: {sorted(SUPPORTED_CROPS)}.",
            400,
            {"received_crop": crop},
        )
    if state.lower() not in SUPPORTED_STATES:
        raise ApiError(
            "UNSUPPORTED_STATE",
            f"Supported states: {sorted(SUPPORTED_STATES)}.",
            400,
            {"received_state": state},
        )
    if horizon_days not in SUPPORTED_HORIZONS:
        raise ApiError(
            "UNSUPPORTED_HORIZON",
            f"Supported horizons: {sorted(SUPPORTED_HORIZONS)} days.",
            400,
            {"received_horizon_days": horizon_days},
        )


def _resolve_mandi(forecasts: pd.DataFrame, mandi_input: str) -> pd.Series:
    """Resolve display name or slug to a forecast row.

    Compares slugify(mandi_input) against the 'mandi' column.
    Raises MANDI_NOT_FOUND if no match.
    """
    slug = slugify(mandi_input)
    matches = forecasts[forecasts["mandi"].apply(slugify) == slug]
    if matches.empty:
        raise ApiError(
            "MANDI_NOT_FOUND",
            f"Mandi '{mandi_input}' not found in forecast data.",
            404,
            {
                "received_mandi": mandi_input,
                "available_mandis": sorted(forecasts["mandi"].tolist()),
            },
        )
    return matches.iloc[0]


def get_health() -> dict:
    try:
        forecasts = read_forecasts()
        data_status = "available"
        latest_date = str(pd.to_datetime(forecasts["as_of_date"]).max().date())
        model_version = str(forecasts["model_version"].iloc[0]) if len(forecasts) > 0 else None
    except Exception:
        data_status = "unavailable"
        latest_date = None
        model_version = None

    from api.config import API_VERSION, SUPPORTED_CROPS, SUPPORTED_HORIZONS

    return {
        "status": "ok",
        "api_version": API_VERSION,
        "data_status": data_status,
        "latest_data_date": latest_date,
        "model_version": model_version,
        "supported_crops": sorted(SUPPORTED_CROPS),
        "supported_horizons": sorted(SUPPORTED_HORIZONS),
    }


def get_forecast(crop: str, state: str, mandi: str, horizon_days: int) -> ForecastResponse:
    _validate_scope(crop, state, horizon_days)

    forecasts = read_forecasts()
    row = _resolve_mandi(forecasts, mandi)

    forecast_price = float(row["forecast_price_inr_qtl"])
    lower = float(row["lower_bound_inr_qtl"])
    upper = float(row["upper_bound_inr_qtl"])
    interval_width = upper - lower
    relative_width = interval_width / max(forecast_price, 1.0)
    rl = _risk_level(relative_width, LOW_MAX_PCT, HIGH_MIN_PCT)

    return ForecastResponse(
        crop=crop.lower(),
        state=state.lower(),
        mandi=str(row["mandi"]),
        mandi_id=str(row["mandi_id"]),
        market_id=int(row["market_id"]),
        horizon_days=int(row["horizon_days"]),
        as_of_date=str(pd.to_datetime(row["as_of_date"]).date()),
        forecast_price_inr_qtl=round(forecast_price, 2),
        lower_bound_inr_qtl=round(lower, 2),
        upper_bound_inr_qtl=round(upper, 2),
        confidence_level=float(row["confidence_level"]),
        risk_level=rl,
        market_regime=None,
        top_drivers=[],
        model_version=str(row["model_version"]),
    )


def get_recommendations(
    crop: str,
    candidate_states: list[str],
    horizon_days: int,
    farmer_latitude: float,
    farmer_longitude: float,
    quantity_quintal: float,
) -> RecommendationResponse:
    for state in candidate_states:
        _validate_scope(crop, state, horizon_days)

    forecasts = read_forecasts()
    mandis = read_mandi_metadata()

    mandis_with_coords = mandis.dropna(subset=["latitude", "longitude"])

    recs = score_recommendations(
        forecasts=forecasts,
        mandis=mandis_with_coords,
        farmer_latitude=farmer_latitude,
        farmer_longitude=farmer_longitude,
        cost_per_km_per_quintal=DEFAULT_COST_PER_KM,
        road_distance_factor=DEFAULT_ROAD_FACTOR,
        uncertainty_penalty_weight=DEFAULT_PENALTY,
        low_max_interval_pct=LOW_MAX_PCT,
        high_min_interval_pct=HIGH_MIN_PCT,
        candidate_state=candidate_states[0],
    )

    # Merge as_of_date back (engine output_columns doesn't include it)
    recs = recs.merge(
        forecasts[["market_id", "as_of_date", "model_version"]],
        on="market_id",
        how="left",
    )

    top = recs.iloc[0]

    alternatives = [
        MandiRecommendation(
            rank=int(row["rank"]),
            mandi=str(row["mandi"]),
            mandi_id=str(row["mandi_id"]),
            market_id=int(row["market_id"]),
            state=str(row["state"]),
            district_name=str(row["district_name"]) if pd.notna(row.get("district_name")) else None,
            as_of_date=str(pd.to_datetime(row["as_of_date"]).date()),
            forecast_price_inr_qtl=round(float(row["forecast_price_inr_qtl"]), 2),
            lower_bound_inr_qtl=round(float(row["lower_bound_inr_qtl"]), 2),
            upper_bound_inr_qtl=round(float(row["upper_bound_inr_qtl"]), 2),
            estimated_transport_cost_inr_qtl=round(
                float(row["estimated_transport_cost_inr_qtl"]), 2
            ),
            expected_net_price_inr_qtl=round(float(row["expected_net_price_inr_qtl"]), 2),
            uncertainty_penalty_inr_qtl=round(float(row["uncertainty_penalty_inr_qtl"]), 2),
            risk_adjusted_score=round(float(row["risk_adjusted_score"]), 2),
            risk_level=str(row["risk_level"]),
            market_regime=None,
            reason=str(row["reason"]),
        )
        for _, row in recs.iterrows()
    ]

    return RecommendationResponse(
        crop=crop.lower(),
        horizon_days=horizon_days,
        quantity_quintal=quantity_quintal,
        recommended_mandi=str(top["mandi"]),
        expected_net_price_inr_qtl=round(float(top["expected_net_price_inr_qtl"]), 2),
        risk_level=str(top["risk_level"]),
        reason=str(top["reason"]),
        alternatives=alternatives,
        model_version=str(top["model_version"]),
    )
