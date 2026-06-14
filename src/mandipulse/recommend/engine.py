from __future__ import annotations

import math
import uuid
from datetime import UTC, datetime

import pandas as pd


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return 2 * radius_km * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def compute_transport_cost_inr_qtl(
    road_distance_km: float,
    cost_per_km_per_quintal: float,
) -> float:
    """Return transport cost in INR/quintal.

    cost_per_km_per_quintal is already a per-quintal rate so the result is
    independent of load size, consistent with configs/recommendation.yaml.
    """
    return road_distance_km * cost_per_km_per_quintal


def risk_level(
    relative_interval_width: float,
    low_max_pct: float,
    high_min_pct: float,
) -> str:
    if relative_interval_width <= low_max_pct:
        return "low"
    if relative_interval_width < high_min_pct:
        return "medium"
    return "high"


def score_recommendations(
    forecasts: pd.DataFrame,
    mandis: pd.DataFrame,
    farmer_latitude: float,
    farmer_longitude: float,
    cost_per_km_per_quintal: float,
    road_distance_factor: float,
    uncertainty_penalty_weight: float,
    low_max_interval_pct: float,
    high_min_interval_pct: float,
    candidate_state: str,
) -> pd.DataFrame:
    merged = forecasts.merge(
        mandis[["market_id", "market_name", "district_name", "latitude", "longitude"]],
        on="market_id",
        how="left",
        validate="one_to_one",
    )
    missing_coords = merged[merged["latitude"].isna() | merged["longitude"].isna()]
    if not missing_coords.empty:
        raise ValueError("Some candidate mandis are still missing coordinates.")

    merged["air_distance_km"] = merged.apply(
        lambda row: haversine_km(
            farmer_latitude,
            farmer_longitude,
            float(row["latitude"]),
            float(row["longitude"]),
        ),
        axis=1,
    )
    merged["road_distance_km"] = merged["air_distance_km"] * road_distance_factor
    merged["estimated_transport_cost_inr_qtl"] = merged["road_distance_km"].map(
        lambda d: compute_transport_cost_inr_qtl(d, cost_per_km_per_quintal)
    )
    merged["expected_net_price_inr_qtl"] = (
        merged["forecast_price_inr_qtl"] - merged["estimated_transport_cost_inr_qtl"]
    )
    merged["interval_width_inr_qtl"] = merged["upper_bound_inr_qtl"] - merged["lower_bound_inr_qtl"]
    merged["uncertainty_penalty_inr_qtl"] = (
        merged["interval_width_inr_qtl"] * uncertainty_penalty_weight
    )
    merged["risk_adjusted_score"] = (
        merged["expected_net_price_inr_qtl"] - merged["uncertainty_penalty_inr_qtl"]
    )
    merged["relative_interval_width"] = merged["interval_width_inr_qtl"] / merged[
        "forecast_price_inr_qtl"
    ].clip(lower=1.0)
    merged["risk_level"] = merged["relative_interval_width"].map(
        lambda w: risk_level(w, low_max_interval_pct, high_min_interval_pct)
    )
    merged = merged.sort_values(
        ["risk_adjusted_score", "expected_net_price_inr_qtl"],
        ascending=[False, False],
    ).reset_index(drop=True)
    merged["rank"] = range(1, len(merged) + 1)
    merged["recommendation_id"] = [str(uuid.uuid4()) for _ in range(len(merged))]
    merged["generated_at"] = datetime.now(UTC).replace(microsecond=0).isoformat()
    merged["candidate_states"] = candidate_state
    merged["state"] = candidate_state
    merged["mandi"] = merged["market_name"]
    merged["reason"] = merged.apply(
        lambda row: (
            f"{row['market_name']} ranks #{row['rank']} with forecast "
            f"{row['forecast_price_inr_qtl']:.2f}, transport cost "
            f"{row['estimated_transport_cost_inr_qtl']:.2f}, and risk-adjusted score "
            f"{row['risk_adjusted_score']:.2f} INR/quintal."
        ),
        axis=1,
    )
    output_columns = [
        "recommendation_id",
        "generated_at",
        "crop",
        "model_name",
        "horizon_days",
        "candidate_states",
        "rank",
        "market_id",
        "mandi_id",
        "mandi",
        "state",
        "forecast_price_inr_qtl",
        "lower_bound_inr_qtl",
        "upper_bound_inr_qtl",
        "estimated_transport_cost_inr_qtl",
        "expected_net_price_inr_qtl",
        "uncertainty_penalty_inr_qtl",
        "risk_adjusted_score",
        "risk_level",
        "reason",
        "air_distance_km",
        "road_distance_km",
        "district_name",
    ]
    return merged[output_columns]
