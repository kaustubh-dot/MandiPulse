# MandiPulse India API Spec

## API Overview

The FastAPI service exposes forecasts, mandi recommendations, regime status, and monitoring metrics. The API is the contract between the ML system and the Streamlit dashboard.

All prices are expressed as INR per quintal unless otherwise noted.

## Endpoint List

| Method | Endpoint | Responsibility | Priority |
|---|---|---|---:|
| GET | `/health` | Check API, model artifact, and data availability | P0 |
| POST | `/forecast` | Return forecast, interval, regime, and drivers | P0 |
| POST | `/recommend` | Rank mandis by risk-adjusted net expected price | P0 |
| GET | `/regime` | Return current regime/anomaly state for crop/mandi | P0 |
| GET | `/metrics` | Return monitoring and model metrics | P0 |

Only the P0 endpoints above are in MVP API scope.

## Deferred Non-MVP Capabilities

These are ideas only, not API routes for Phase 1 or the MVP:

| Capability | Status | Rule |
|---|---|---|
| Detailed data-quality endpoint | P2 future | Do not add `/data-quality` until all P0 endpoints are working and tested |
| Arbitrage opportunity detection | P2 future | Do not add `/arbitrage` during MVP |
| Similar historical market days | P2 future | Do not add `/similar-days` during MVP |

Deferred capabilities must not appear in the FastAPI router or Streamlit navigation until explicitly promoted in the docs.

## Pydantic Model Names

| Model | Purpose |
|---|---|
| `HealthResponse` | Health check response |
| `ForecastRequest` | Forecast request body |
| `ForecastResponse` | Forecast response body |
| `RecommendationRequest` | Recommendation request body |
| `FarmerLocation` | Latitude/longitude object |
| `MandiRecommendation` | One ranked mandi result |
| `RecommendationResponse` | Recommendation response body |
| `RegimeResponse` | Regime/anomaly response |
| `AnomalyEvent` | One anomaly event |
| `MetricsResponse` | Monitoring metrics response |
| `ErrorResponse` | Standard error response |

## Common Rules

- Supported horizons: `7`, `14`, `30`.
- Supported MVP crops: `onion`, `tomato`.
- Supported MVP states: `maharashtra`, `karnataka`, `uttar_pradesh`.
- Requests must be validated with Pydantic.
- Responses must include enough metadata for dashboard display.
- Forecasts must include uncertainty bounds.
- Recommendations must include transport cost and risk level.
- Causal claims must not be returned by the API.
- Request bodies may use mandi display names, but the API must resolve them to internal `mandi_id` values through `mandi_metadata` and alias maps.
- If a mandi display name cannot be resolved unambiguously, return `MANDI_NOT_FOUND` instead of silently choosing a mandi.

## Standard Error Format

```json
{
  "error": {
    "code": "UNSUPPORTED_HORIZON",
    "message": "Supported horizons are 7, 14, and 30 days.",
    "details": {
      "received_horizon_days": 21
    }
  }
}
```

## Common Error Codes

| Code | HTTP Status | Meaning |
|---|---:|---|
| `VALIDATION_ERROR` | 422 | Request schema or value validation failed |
| `UNSUPPORTED_CROP` | 400 | Crop is outside MVP scope |
| `UNSUPPORTED_STATE` | 400 | State is outside MVP scope |
| `UNSUPPORTED_HORIZON` | 400 | Horizon is not 7, 14, or 30 |
| `MANDI_NOT_FOUND` | 404 | Mandi not found in metadata |
| `INSUFFICIENT_HISTORY` | 409 | Not enough data to forecast selected mandi |
| `MODEL_NOT_AVAILABLE` | 503 | Model artifact is missing or cannot be loaded |
| `DATA_NOT_AVAILABLE` | 503 | Required processed data is missing |
| `INTERNAL_ERROR` | 500 | Unexpected server failure |

## GET `/health`

### Responsibility

Return system readiness for demo/API use.

### Response Example

```json
{
  "status": "ok",
  "api_version": "0.1.0",
  "model_status": "loaded",
  "model_version": "mlflow-run-123",
  "data_status": "available",
  "latest_data_date": "2026-06-10",
  "supported_crops": ["onion", "tomato"],
  "supported_horizons": [7, 14, 30]
}
```

## POST `/forecast`

### Responsibility

Return a price forecast for one crop-state-mandi-horizon combination, with uncertainty interval, market regime, and top drivers.

### Request Model

`ForecastRequest`

```json
{
  "crop": "onion",
  "state": "maharashtra",
  "mandi": "lasalgaon",
  "horizon_days": 14
}
```

### Response Model

`ForecastResponse`

```json
{
  "crop": "onion",
  "state": "maharashtra",
  "mandi": "lasalgaon",
  "horizon_days": 14,
  "as_of_date": "2026-06-10",
  "forecast_price": 2100.5,
  "lower_bound": 1940.2,
  "upper_bound": 2285.8,
  "confidence_level": 0.9,
  "market_regime": "volatile",
  "risk_level": "medium",
  "model_version": "mlflow-run-123",
  "top_drivers": [
    "7-day price momentum",
    "arrival quantity drop",
    "seasonal pattern"
  ]
}
```

### Notes

- `forecast_price`, `lower_bound`, and `upper_bound` are INR/quintal.
- The response must not omit uncertainty.
- If SHAP is unavailable, `top_drivers` can use a safe fallback based on feature movements.

## POST `/recommend`

### Responsibility

Rank candidate mandis by expected net price after transport cost and uncertainty penalty.

### Request Model

`RecommendationRequest`

```json
{
  "crop": "onion",
  "farmer_location": {
    "latitude": 19.9975,
    "longitude": 73.7898
  },
  "candidate_states": ["maharashtra"],
  "horizon_days": 14,
  "quantity_quintal": 20
}
```

### Response Model

`RecommendationResponse`

```json
{
  "crop": "onion",
  "horizon_days": 14,
  "quantity_quintal": 20,
  "recommended_mandi": "lasalgaon",
  "expected_net_price_per_quintal": 1980.4,
  "risk_level": "medium",
  "reason": "Lasalgaon has the highest risk-adjusted expected net price after transport cost.",
  "alternatives": [
    {
      "rank": 1,
      "mandi": "lasalgaon",
      "state": "maharashtra",
      "forecast_price_per_quintal": 2100.5,
      "transport_cost_per_quintal": 120.1,
      "expected_net_price_per_quintal": 1980.4,
      "lower_bound_per_quintal": 1940.2,
      "upper_bound_per_quintal": 2285.8,
      "risk_adjusted_score": 1902.0,
      "risk_level": "medium",
      "market_regime": "volatile"
    },
    {
      "rank": 2,
      "mandi": "pune",
      "state": "maharashtra",
      "forecast_price_per_quintal": 1980.2,
      "transport_cost_per_quintal": 60.0,
      "expected_net_price_per_quintal": 1920.2,
      "lower_bound_per_quintal": 1875.0,
      "upper_bound_per_quintal": 2060.5,
      "risk_adjusted_score": 1874.8,
      "risk_level": "low",
      "market_regime": "normal"
    }
  ],
  "model_version": "mlflow-run-123"
}
```

### Notes

- The `alternatives` list should include the recommended mandi as rank 1.
- Transport cost estimation assumptions must be documented in model/config docs.
- Ranking formula should be deterministic and tested.

## GET `/regime`

### Responsibility

Return the current regime and recent anomaly events for a crop/mandi pair.

### Query Parameters

| Name | Type | Required | Example |
|---|---|---:|---|
| `crop` | string | Yes | `onion` |
| `state` | string | Yes | `maharashtra` |
| `mandi` | string | Yes | `lasalgaon` |
| `lookback_days` | integer | No | `90` |

### Response Model

`RegimeResponse`

```json
{
  "crop": "onion",
  "state": "maharashtra",
  "mandi": "lasalgaon",
  "as_of_date": "2026-06-10",
  "current_regime": "volatile",
  "reason": "7-day volatility is 2.4x above the 90-day baseline.",
  "volatility_7d": 0.18,
  "volatility_30d": 0.09,
  "anomalies": [
    {
      "date": "2026-06-04",
      "price": 2180.0,
      "price_return_1d": 0.12,
      "anomaly_score": 2.8,
      "label": "positive_price_spike"
    }
  ]
}
```

## GET `/metrics`

### Responsibility

Return data quality, drift, model, and API monitoring metrics for the dashboard.

### Response Model

`MetricsResponse`

```json
{
  "generated_at": "2026-06-12T21:30:00+05:30",
  "latest_data_date": "2026-06-10",
  "data_freshness_days": 2,
  "missing_data_pct": 3.7,
  "duplicate_records_count": 12,
  "invalid_records_count": 4,
  "recent_forecast_mae": 145.2,
  "recent_forecast_smape": 8.6,
  "empirical_coverage_90": 0.88,
  "drift_status": "warning",
  "api_success_rate": 0.99,
  "p95_latency_ms": 240.5,
  "model_version": "mlflow-run-123"
}
```

## Endpoint Responsibility Matrix

| Endpoint | Loads Model | Reads Data | Computes Decision | Used By Dashboard |
|---|---:|---:|---:|---:|
| `/health` | No | Yes | No | Yes |
| `/forecast` | Yes | Yes | Forecast only | Yes |
| `/recommend` | Yes | Yes | Recommendation | Yes |
| `/regime` | No/optional | Yes | Regime label | Yes |
| `/metrics` | No | Yes | Monitoring summary | Yes |

## API Acceptance Checklist

- [ ] All Pydantic models are defined.
- [ ] All MVP endpoints return documented fields.
- [ ] Forecast response always includes lower and upper bounds.
- [ ] Recommendation response always includes transport cost and risk.
- [ ] Error responses follow standard format.
- [ ] Integration tests cover health, forecast, recommend, regime, and metrics.
- [ ] Unsupported horizons are rejected.
- [ ] Missing model/data states return service errors, not silent fallback.
