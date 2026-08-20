from __future__ import annotations

import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mandipulse.data.loaders import (  # noqa: E402
    read_forecasts,
    read_mandi_metadata,
)
from mandipulse.policy import (  # noqa: E402
    FORECAST_AS_OF_POLICY,
    canonical_forecast_as_of,
    forecast_target_date,
    select_latest_forecast_for_market,
    select_recommendation_candidates,
)
from mandipulse.recommend.engine import haversine_km  # noqa: E402
from mandipulse.recommend.engine import risk_level as _risk_level  # noqa: E402
from mandipulse.recommend.engine import score_recommendations  # noqa: E402
from mandipulse.utils.text import slugify  # noqa: E402

from api.config import (  # noqa: E402
    API_VERSION,
    DEFAULT_COST_PER_KM,
    DEFAULT_ROAD_FACTOR,
    DEFAULT_UNCERTAINTY_PENALTY,
    HIGH_MIN_INTERVAL_PCT,
    LOW_MAX_INTERVAL_PCT,
    SUPPORTED_CROPS,
    SUPPORTED_HORIZONS,
    SUPPORTED_STATES,
)
from api.errors import ApiError  # noqa: E402
from api.schemas import (  # noqa: E402
    ForecastResponse,
    MandiRecommendation,
    RecommendationResponse,
)


_REQUIRED_FORECAST_COLUMNS = {
    "market_id",
    "mandi_id",
    "as_of_date",
    "horizon_days",
    "forecast_price_inr_qtl",
    "lower_bound_inr_qtl",
    "upper_bound_inr_qtl",
    "confidence_level",
    "model_version",
    "crop",
    "model_name",
}


def _validate_forecasts(forecasts: pd.DataFrame) -> pd.DataFrame:
    """Validate the minimum finite snapshot contract shared by API endpoints."""

    canonical_forecast_as_of(forecasts)
    missing = sorted(_REQUIRED_FORECAST_COLUMNS.difference(forecasts.columns))
    if missing:
        raise ValueError(f"Missing forecast columns: {missing}")
    for column in (
        "market_id",
        "horizon_days",
        "forecast_price_inr_qtl",
        "lower_bound_inr_qtl",
        "upper_bound_inr_qtl",
        "confidence_level",
    ):
        values = pd.to_numeric(forecasts[column], errors="coerce")
        if values.isna().any() or not values.map(math.isfinite).all():
            raise ValueError(f"Forecast column {column} contains non-finite values.")
    if (
        forecasts["model_version"].isna().any()
        or forecasts["model_version"].astype(str).str.strip().eq("").any()
    ):
        raise ValueError("Forecast model_version is missing.")
    if forecasts.duplicated(["market_id", "as_of_date"]).any():
        raise ValueError("Forecast snapshot contains duplicate market/as-of rows.")
    return forecasts


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


def _load_forecasts() -> pd.DataFrame:
    try:
        forecasts = read_forecasts()
        _validate_forecasts(forecasts)
    except Exception as exc:
        raise ApiError(
            "DATA_NOT_AVAILABLE",
            "Forecast snapshot data is unavailable or invalid.",
            503,
            {"resource": "forecasts"},
        ) from exc
    return forecasts


def _validate_mandi_metadata(mandis: pd.DataFrame) -> pd.DataFrame:
    """Validate the metadata required to resolve and rank markets."""

    required = {"market_id", "market_name", "district_name", "latitude", "longitude"}
    if mandis.empty or not required.issubset(mandis.columns):
        raise ValueError("Mandi metadata is empty or missing required columns.")
    for column in ("market_id", "latitude", "longitude"):
        values = pd.to_numeric(mandis[column], errors="coerce")
        if values.isna().any() or not values.map(math.isfinite).all():
            raise ValueError(f"Mandi metadata column {column} contains non-finite values.")
    if (
        mandis["market_name"].isna().any()
        or mandis["market_name"].astype(str).str.strip().eq("").any()
        or mandis["market_id"].duplicated().any()
        or (~pd.to_numeric(mandis["latitude"], errors="coerce").between(-90, 90)).any()
        or (~pd.to_numeric(mandis["longitude"], errors="coerce").between(-180, 180)).any()
    ):
        raise ValueError("Mandi metadata contains invalid names, IDs, or coordinates.")
    return mandis


def _load_mandi_metadata() -> pd.DataFrame:
    try:
        return _validate_mandi_metadata(read_mandi_metadata())
    except Exception as exc:
        raise ApiError(
            "DATA_NOT_AVAILABLE",
            "Mandi metadata is unavailable or invalid.",
            503,
            {"resource": "mandi_metadata"},
        ) from exc


def _resolve_mandi_metadata(mandis: pd.DataFrame, mandi_input: str) -> pd.Series:
    """Resolve a display name or slug through the canonical metadata table."""

    slug = slugify(mandi_input)
    matches = mandis.loc[mandis["market_name"].fillna("").map(slugify) == slug]
    if matches.empty:
        raise ApiError(
            "MANDI_NOT_FOUND",
            f"Mandi '{mandi_input}' was not found in mandi metadata.",
            404,
            {
                "received_mandi": mandi_input,
                "available_mandis": sorted(mandis["market_name"].dropna().astype(str).tolist()),
            },
        )
    return matches.iloc[0]


def get_health() -> dict:
    try:
        forecasts = read_forecasts()
        mandis = read_mandi_metadata()
    except Exception:
        forecasts = None
        mandis = None

    if forecasts is None:
        status = "not_ready"
        data_status = "unavailable"
        latest_date = None
        model_version = None
    elif forecasts.empty or mandis is None or mandis.empty:
        status = "not_ready"
        data_status = "empty"
        latest_date = None
        model_version = None
    else:
        try:
            _validate_forecasts(forecasts)
            _validate_mandi_metadata(mandis)
            latest_date = canonical_forecast_as_of(forecasts).isoformat()
            versions = forecasts["model_version"].dropna().astype(str)
            if versions.empty:
                raise ValueError("Missing model version values.")
            model_version = versions.iloc[0]
            status = "ready"
            data_status = "available"
        except Exception:
            status = "not_ready"
            data_status = "unavailable"
            latest_date = None
            model_version = None

    return {
        "status": status,
        "api_version": API_VERSION,
        "data_status": data_status,
        "latest_data_date": latest_date,
        "model_version": model_version,
        "supported_crops": sorted(SUPPORTED_CROPS),
        "supported_horizons": sorted(SUPPORTED_HORIZONS),
    }


def get_forecast(crop: str, state: str, mandi: str, horizon_days: int) -> ForecastResponse:
    _validate_scope(crop, state, horizon_days)

    mandis = _load_mandi_metadata()
    mandi_metadata = _resolve_mandi_metadata(mandis, mandi)
    forecasts = _load_forecasts()
    try:
        row = select_latest_forecast_for_market(forecasts, mandi_metadata["market_id"])
    except ValueError as exc:
        raise ApiError(
            "DATA_NOT_AVAILABLE",
            f"No forecast is available for mandi '{mandi_metadata['market_name']}'.",
            503,
            {"market_id": int(mandi_metadata["market_id"])},
        ) from exc

    forecast_price = float(row["forecast_price_inr_qtl"])
    lower = float(row["lower_bound_inr_qtl"])
    upper = float(row["upper_bound_inr_qtl"])
    interval_width = upper - lower
    relative_width = interval_width / max(forecast_price, 1.0)
    risk = _risk_level(relative_width, LOW_MAX_INTERVAL_PCT, HIGH_MIN_INTERVAL_PCT)
    canonical_as_of = canonical_forecast_as_of(forecasts)
    row_as_of = pd.to_datetime(row["as_of_date"]).date()

    return ForecastResponse(
        crop=crop.lower(),
        state=state.lower(),
        mandi=str(mandi_metadata["market_name"]),
        mandi_id=str(row["mandi_id"]),
        market_id=int(row["market_id"]),
        horizon_days=int(row["horizon_days"]),
        as_of_date=row_as_of.isoformat(),
        canonical_as_of_date=canonical_as_of.isoformat(),
        target_date=forecast_target_date(row_as_of, int(row["horizon_days"])).isoformat(),
        staleness_days=(canonical_as_of - row_as_of).days,
        forecast_price_inr_qtl=round(forecast_price, 2),
        lower_bound_inr_qtl=round(lower, 2),
        upper_bound_inr_qtl=round(upper, 2),
        confidence_level=float(row["confidence_level"]),
        risk_level=risk,
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
    max_transport_radius_km: float,
    max_alternatives: int,
) -> RecommendationResponse:
    if not candidate_states:
        raise ApiError(
            "VALIDATION_ERROR",
            "At least one candidate state is required.",
            422,
            {"field": "candidate_states"},
        )
    for state in candidate_states:
        _validate_scope(crop, state, horizon_days)

    forecasts = _load_forecasts()
    mandis = _load_mandi_metadata()
    try:
        eligible_forecasts = select_recommendation_candidates(forecasts)
        canonical_as_of = canonical_forecast_as_of(forecasts)
    except ValueError as exc:
        raise ApiError(
            "DATA_NOT_AVAILABLE",
            "No forecasts satisfy the configured as-of policy.",
            503,
            {"as_of_policy": FORECAST_AS_OF_POLICY},
        ) from exc

    mandis_with_coords = mandis.dropna(subset=["latitude", "longitude"]).copy()
    mandis_with_coords["_road_distance_km"] = mandis_with_coords.apply(
        lambda row: haversine_km(
            farmer_latitude,
            farmer_longitude,
            float(row["latitude"]),
            float(row["longitude"]),
        )
        * DEFAULT_ROAD_FACTOR,
        axis=1,
    )
    mandis_in_radius = mandis_with_coords.loc[
        mandis_with_coords["_road_distance_km"] <= max_transport_radius_km
    ].drop(columns=["_road_distance_km"])
    eligible_forecasts = eligible_forecasts.loc[
        eligible_forecasts["market_id"].isin(mandis_in_radius["market_id"])
    ].copy()

    if eligible_forecasts.empty:
        raise ApiError(
            "NO_CANDIDATES_AVAILABLE",
            "No canonical-as-of mandi forecast is available within the requested radius.",
            404,
            {
                "as_of_date": canonical_as_of.isoformat(),
                "as_of_policy": FORECAST_AS_OF_POLICY,
                "max_transport_radius_km": max_transport_radius_km,
            },
        )

    recs = score_recommendations(
        forecasts=eligible_forecasts,
        mandis=mandis_in_radius,
        farmer_latitude=farmer_latitude,
        farmer_longitude=farmer_longitude,
        cost_per_km_per_quintal=DEFAULT_COST_PER_KM,
        road_distance_factor=DEFAULT_ROAD_FACTOR,
        uncertainty_penalty_weight=DEFAULT_UNCERTAINTY_PENALTY,
        low_max_interval_pct=LOW_MAX_INTERVAL_PCT,
        high_min_interval_pct=HIGH_MIN_INTERVAL_PCT,
        candidate_state=candidate_states[0].lower(),
    ).head(max_alternatives)

    recs = recs.merge(
        eligible_forecasts[["market_id", "as_of_date", "model_version"]],
        on="market_id",
        how="left",
        validate="one_to_one",
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
            road_distance_km=round(float(row["road_distance_km"]), 2),
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
        as_of_date=canonical_as_of.isoformat(),
        as_of_policy=FORECAST_AS_OF_POLICY,
        max_transport_radius_km=max_transport_radius_km,
        max_alternatives=max_alternatives,
        recommended_mandi=str(top["mandi"]),
        expected_net_price_inr_qtl=round(float(top["expected_net_price_inr_qtl"]), 2),
        risk_level=str(top["risk_level"]),
        reason=str(top["reason"]),
        alternatives=alternatives,
        model_version=str(top["model_version"]),
    )
