from __future__ import annotations

import os

from mandipulse.config import load_yaml_config

API_VERSION = "0.1.0"

# MVP scope guards — out-of-scope requests return typed 400/422 errors.
SUPPORTED_CROPS: frozenset[str] = frozenset({"onion"})
SUPPORTED_STATES: frozenset[str] = frozenset({"maharashtra"})
SUPPORTED_HORIZONS: frozenset[int] = frozenset({7})

_RECOMMENDATION_CONFIG = load_yaml_config("configs/recommendation.yaml")
_TRANSPORT_CONFIG = _RECOMMENDATION_CONFIG.get("transport_cost", {})
_RANKING_CONFIG = _RECOMMENDATION_CONFIG.get("ranking", {})
_RISK_CONFIG = _RECOMMENDATION_CONFIG.get("risk_thresholds", {})

DEFAULT_COST_PER_KM: float = float(_TRANSPORT_CONFIG.get("cost_per_km_per_quintal", 4.0))
DEFAULT_ROAD_FACTOR: float = float(_TRANSPORT_CONFIG.get("road_distance_factor", 1.3))
DEFAULT_TRANSPORT_RADIUS_KM: float = float(
    _TRANSPORT_CONFIG.get("default_transport_radius_km", 500.0)
)
MAX_TRANSPORT_RADIUS_KM: float = float(_TRANSPORT_CONFIG.get("max_transport_radius_km", 500.0))
DEFAULT_UNCERTAINTY_PENALTY: float = float(_RANKING_CONFIG.get("uncertainty_penalty_weight", 0.3))
DEFAULT_ALTERNATIVES: int = int(_RANKING_CONFIG.get("default_alternatives", 10))
MAX_ALTERNATIVES: int = int(_RANKING_CONFIG.get("max_alternatives", 10))
LOW_MAX_INTERVAL_PCT: float = float(_RISK_CONFIG.get("low_max_interval_pct", 10)) / 100
HIGH_MIN_INTERVAL_PCT: float = float(_RISK_CONFIG.get("high_min_interval_pct", 25)) / 100

if not 0 < DEFAULT_TRANSPORT_RADIUS_KM <= MAX_TRANSPORT_RADIUS_KM:
    raise ValueError("Configured default transport radius must be within the configured maximum.")
if not 0 < DEFAULT_ALTERNATIVES <= MAX_ALTERNATIVES:
    raise ValueError("Configured default alternatives must be within the configured maximum.")

# CORS origins. Default "*" is deliberate: the API is public, read-only, and carries no secrets.
# Set MANDIPULSE_ALLOWED_ORIGINS=https://your-frontend.vercel.app in production to tighten.
ALLOWED_ORIGINS: list[str] = [
    o.strip() for o in os.environ.get("MANDIPULSE_ALLOWED_ORIGINS", "*").split(",") if o.strip()
]
