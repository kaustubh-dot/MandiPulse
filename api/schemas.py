from __future__ import annotations

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class ForecastRequest(BaseModel):
    crop: str
    state: str
    mandi: str
    horizon_days: int = 7


class FarmerLocation(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)


class RecommendationRequest(BaseModel):
    crop: str
    farmer_location: FarmerLocation
    candidate_states: list[str]
    horizon_days: int = 7
    quantity_quintal: float = Field(default=100.0, gt=0)


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class HealthResponse(BaseModel):
    status: str
    api_version: str
    data_status: str
    latest_data_date: str | None
    model_version: str | None
    supported_crops: list[str]
    supported_horizons: list[int]


class ForecastResponse(BaseModel):
    crop: str
    state: str
    mandi: str
    mandi_id: str
    market_id: int
    horizon_days: int
    as_of_date: str
    forecast_price_inr_qtl: float
    lower_bound_inr_qtl: float
    upper_bound_inr_qtl: float
    confidence_level: float
    risk_level: str
    market_regime: str | None = None
    top_drivers: list[str] = []
    model_version: str


class MandiRecommendation(BaseModel):
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
    estimated_transport_cost_inr_qtl: float
    expected_net_price_inr_qtl: float
    uncertainty_penalty_inr_qtl: float
    risk_adjusted_score: float
    risk_level: str
    market_regime: str | None = None
    reason: str


class RecommendationResponse(BaseModel):
    crop: str
    horizon_days: int
    quantity_quintal: float
    recommended_mandi: str
    expected_net_price_inr_qtl: float
    risk_level: str
    reason: str
    alternatives: list[MandiRecommendation]
    model_version: str


class ErrorResponse(BaseModel):
    error: dict
