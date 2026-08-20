from __future__ import annotations

from fastapi import APIRouter, Response

from api.schemas import (
    ForecastRequest,
    ForecastResponse,
    ErrorResponse,
    HealthResponse,
    RecommendationRequest,
    RecommendationResponse,
)
from api.service import get_forecast, get_health, get_recommendations

router = APIRouter()

ERROR_RESPONSES = {
    400: {"model": ErrorResponse, "description": "Unsupported scope or invalid request policy"},
    404: {"model": ErrorResponse, "description": "Mandi or eligible candidates not found"},
    422: {"model": ErrorResponse, "description": "Request validation failed"},
    500: {"model": ErrorResponse, "description": "Unexpected internal error"},
    503: {"model": ErrorResponse, "description": "Required snapshot data is unavailable"},
}


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    responses={503: {"model": HealthResponse, "description": "Snapshot data is not ready"}},
)
def health(response: Response) -> HealthResponse:
    """Check API and data availability."""
    payload = get_health()
    response.status_code = 200 if payload["status"] == "ready" else 503
    return HealthResponse(**payload)


@router.post(
    "/forecast",
    response_model=ForecastResponse,
    tags=["Forecasting"],
    responses=ERROR_RESPONSES,
)
def forecast(req: ForecastRequest) -> ForecastResponse:
    """Return a 7-day price forecast with uncertainty interval for a given mandi.

    - Supported crop: `onion`
    - Supported state: `maharashtra`
    - Supported horizon: `7` days
    - `market_regime` is `null` (regime detection deferred)
    - `top_drivers` is `[]` (shipped model is moving-average; SHAP not applicable)
    """
    return get_forecast(req.crop, req.state, req.mandi, req.horizon_days)


@router.post(
    "/recommend",
    response_model=RecommendationResponse,
    tags=["Recommendation"],
    responses=ERROR_RESPONSES,
)
def recommend(req: RecommendationRequest) -> RecommendationResponse:
    """Rank mandis by net expected price after transport cost.

    Transport cost uses haversine distance × road factor + cost-per-km from config.
    Ranking formula: `score = net_price - penalty_weight × interval_width`
    All config defaults from `configs/recommendation.yaml`.
    """
    return get_recommendations(
        crop=req.crop,
        candidate_states=req.candidate_states,
        horizon_days=req.horizon_days,
        farmer_latitude=req.farmer_location.latitude,
        farmer_longitude=req.farmer_location.longitude,
        quantity_quintal=req.quantity_quintal,
        max_transport_radius_km=req.max_transport_radius_km,
        max_alternatives=req.max_alternatives,
    )
