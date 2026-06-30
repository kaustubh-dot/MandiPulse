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
`UNSUPPORTED_HORIZON`, `MANDI_NOT_FOUND`, `DATA_NOT_AVAILABLE`, and `INTERNAL_ERROR`.

## GET `/health`

Response fields:

| Field | Type | Notes |
|---|---|---|
| `status` | string | `ok` when API loaders are ready |
| `api_version` | string | API package version |
| `data_status` | string | Demo/full artifact availability |
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
  "quantity_quintal": 100
}
```

Response includes:

- `recommended_mandi`, headline net price, risk level, and reason.
- `alternatives`, including rank 1, with forecast, interval, transport cost, expected net price,
  uncertainty penalty, risk-adjusted score, and risk level.
- `model_version`.

## Compatibility Rules

- Keep field names aligned with `api/schemas.py`.
- Keep ranking behavior aligned with `src/mandipulse/recommend/engine.py`.
- Do not add deferred endpoints until `docs/RULES.md`, `docs/TRACKER.md`, and this spec are updated.
- Never fabricate regime labels, SHAP drivers, unsupported horizons, or additional states.
