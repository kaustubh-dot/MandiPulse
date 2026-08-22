from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from api.config import (
    DEFAULT_ALTERNATIVES,
    DEFAULT_TRANSPORT_RADIUS_KM,
    MAX_ALTERNATIVES,
    MAX_TRANSPORT_RADIUS_KM,
)

# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class RequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ResponseModel(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)


class ForecastRequest(RequestModel):
    crop: str = Field(min_length=1)
    state: str = Field(min_length=1)
    mandi: str = Field(min_length=1)
    horizon_days: int = Field(default=7, strict=True)


class FarmerLocation(RequestModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, allow_inf_nan=False)
    longitude: float = Field(..., ge=-180.0, le=180.0, allow_inf_nan=False)


class RecommendationRequest(RequestModel):
    crop: str = Field(min_length=1)
    farmer_location: FarmerLocation
    candidate_states: list[str] = Field(min_length=1, max_length=1)
    horizon_days: int = Field(default=7, strict=True)
    quantity_quintal: float = Field(default=100.0, gt=0, allow_inf_nan=False)
    max_transport_radius_km: float = Field(
        default=DEFAULT_TRANSPORT_RADIUS_KM,
        gt=0,
        le=MAX_TRANSPORT_RADIUS_KM,
        allow_inf_nan=False,
    )
    max_alternatives: int = Field(
        default=DEFAULT_ALTERNATIVES,
        ge=1,
        le=MAX_ALTERNATIVES,
        strict=True,
    )


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class HealthResponse(ResponseModel):
    status: Literal["ready", "not_ready"]
    api_version: str
    data_status: Literal["available", "unavailable", "empty"]
    latest_data_date: str | None
    model_version: str | None
    supported_crops: list[str]
    supported_horizons: list[int]


class ForecastResponse(ResponseModel):
    crop: str
    state: str
    mandi: str
    mandi_id: str
    market_id: int
    horizon_days: int
    as_of_date: str
    canonical_as_of_date: str
    target_date: str
    staleness_days: int
    forecast_price_inr_qtl: float
    lower_bound_inr_qtl: float
    upper_bound_inr_qtl: float
    confidence_level: float
    risk_level: str
    market_regime: str | None = None
    top_drivers: list[str] = Field(default_factory=list)
    model_version: str


class MandiRecommendation(ResponseModel):
    rank: int
    mandi: str
    mandi_id: str
    market_id: int
    state: str
    district_name: str | None
    as_of_date: str
    forecast_price_inr_qtl: float
    lower_bound_inr_qtl: float
    upper_bound_inr_qtl: float
    road_distance_km: float
    estimated_transport_cost_inr_qtl: float
    expected_net_price_inr_qtl: float
    uncertainty_penalty_inr_qtl: float = Field(
        description=(
            "Evidence only. The public interval width is global, so this value is "
            "identical across candidates and does not affect rank."
        )
    )
    transport_adjusted_net_price_inr_qtl: float = Field(
        description=(
            "Ranking value: expected net price after estimated transport cost, in "
            "INR per quintal. Candidates are ranked by this field descending."
        )
    )
    risk_level: str
    market_regime: str | None = None
    reason: str


class RecommendationResponse(ResponseModel):
    crop: str
    horizon_days: int
    quantity_quintal: float
    as_of_date: str
    as_of_policy: Literal["as_of_equals_bundle_max"]
    max_transport_radius_km: float
    max_alternatives: int
    recommended_mandi: str
    expected_net_price_inr_qtl: float
    risk_level: str
    reason: str
    alternatives: list[MandiRecommendation]
    model_version: str


class ErrorDetail(ResponseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(ResponseModel):
    error: ErrorDetail
