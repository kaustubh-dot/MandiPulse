# MandiPulse API Spec

## Status

FastAPI is active as a post-MVP additive surface. It serves precomputed 7-day Onion/Maharashtra
forecasts and transport-adjusted recommendations over the same committed demo bundle used by the
Streamlit dashboard.

Implemented endpoints:

| Method | Path | Responsibility |
|---|---|---|
| GET | `/health` | API and data readiness |
| POST | `/forecast` | One mandi forecast with uncertainty interval |
| POST | `/recommend` | Ranked mandis by risk-adjusted net expected price |

Deferred endpoints: `/regime`, `/metrics`, `/data-quality`, `/arbitrage`, and `/similar-days`.

## Scope

| Dimension | Supported |
|---|---|
| Crop | `onion` |
| State | `maharashtra` |
| Horizon | `7` days |
| Model runtime | Precomputed artifacts; no model training or LightGBM inference at request time |
| Regime | `null` because regime detection is deferred |
| Drivers | `[]` because the shipped forecaster is moving-average |

Out-of-scope requests return typed errors instead of silent fallback.

## Standard Error Format

```json
{
  "error": {
    "code": "UNSUPPORTED_HORIZON",
    "message": "Supported MVP horizon is 7 days.",
    "details": {
      "received_horizon_days": 21
    }
  }
}
```

Common codes: `VALIDATION_ERROR`, `UNSUPPORTED_CROP`, `UNSUPPORTED_STATE`,
`UNSUPPORTED_HORIZON`, `MANDI_NOT_FOUND`, `NO_CANDIDATES_AVAILABLE`,
`DATA_NOT_AVAILABLE`, and `INTERNAL_ERROR`. Pydantic request failures use the same
`{"error":{"code":"VALIDATION_ERROR",...}}` envelope.

## GET `/health`

Response fields:

| Field | Type | Notes |
|---|---|---|
| `status` | string | `ready` when snapshot loaders are ready; otherwise `not_ready` |
| `api_version` | string | API package version |
| `data_status` | string | `available`, `empty`, or `unavailable` |
| `latest_data_date` | string or null | Latest date in loaded artifacts |
| `model_version` | string or null | Artifact model label |
| `supported_crops` | list[string] | Currently `["onion"]` |
| `supported_horizons` | list[int] | Currently `[7]` |

## POST `/forecast`

Request:

```json
{
  "crop": "onion",
  "state": "maharashtra",
  "mandi": "lasalgaon",
  "horizon_days": 7
}
```

Response includes:

- Crop, state, mandi, `mandi_id`, and `market_id`.
- `forecast_price_inr_qtl`, `lower_bound_inr_qtl`, `upper_bound_inr_qtl`.
- `as_of_date`, `canonical_as_of_date`, `target_date`, and `staleness_days`; the target is
  `as_of_date + horizon_days` and `canonical_as_of_date` is the bundle-wide policy date.
- `confidence_level`, `risk_level`, `market_regime`, `top_drivers`, and `model_version`.

## POST `/recommend`

Request:

```json
{
  "crop": "onion",
  "farmer_location": {
    "latitude": 19.9975,
    "longitude": 73.7898
  },
  "candidate_states": ["maharashtra"],
  "horizon_days": 7,
  "quantity_quintal": 100,
  "max_transport_radius_km": 500,
  "max_alternatives": 10
}
```

`max_transport_radius_km` and `max_alternatives` default to the configured values above and are
bounded by the same configured maxima (currently 500 km and 10 rows). Unknown fields, non-finite
numbers, empty candidate-state lists, and values outside these bounds are rejected with HTTP 422.
The current frozen scope accepts one candidate state (`maharashtra`) per request.

Response includes:

- `recommended_mandi`, headline net price, risk level, and reason.
- `alternatives`, including rank 1, with forecast, interval, transport cost, expected net price,
  uncertainty penalty, risk-adjusted score, and risk level.
- `as_of_date` and `as_of_policy` (`as_of_equals_bundle_max`), plus the applied radius and
  alternative limits.
- `model_version`.

The current public v1 interval uses one global residual width. As a result, the uncertainty penalty
is equal across candidates in one snapshot and does not affect their relative rank; it remains
visible for risk communication. Transport inputs are configurable scenarios, not live route or
carrier quotes.

## Compatibility Rules

- Keep field names aligned with `api/schemas.py`.
- Keep ranking behavior aligned with `src/mandipulse/recommend/engine.py`.
- Do not add deferred endpoints until `docs/RULES.md`, `docs/TRACKER.md`, and this spec are updated.
- Never fabricate regime labels, SHAP drivers, unsupported horizons, or additional states.
