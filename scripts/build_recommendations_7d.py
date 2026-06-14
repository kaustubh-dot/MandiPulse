from __future__ import annotations

import argparse
import math
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mandipulse.utils.formatting import dataframe_to_markdown  # noqa: E402
from mandipulse.utils.text import make_mandi_id, slugify  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build transport-aware 7-day mandi recommendations from latest forecast outputs."
    )
    parser.add_argument(
        "--forecasts",
        default="artifacts/forecasts/forecast_outputs_7d.csv",
    )
    parser.add_argument(
        "--mandis",
        default="data/external/mvp_mandis.csv",
    )
    parser.add_argument(
        "--report",
        default="reports/modeling/recommendation_report_7d.md",
    )
    parser.add_argument(
        "--output",
        default="artifacts/recommendations/recommendation_outputs_7d.csv",
    )
    parser.add_argument("--farmer-latitude", type=float, default=19.99750)
    parser.add_argument("--farmer-longitude", type=float, default=73.78981)
    parser.add_argument("--quantity-quintal", type=float, default=100.0)
    parser.add_argument(
        "--candidate-state",
        default="maharashtra",
    )
    parser.add_argument(
        "--road-factor",
        type=float,
        default=1.25,
        help="Approximate road-vs-airline distance multiplier.",
    )
    parser.add_argument(
        "--transport-cost-inr-per-km",
        type=float,
        default=18.0,
        help="Assumed total transport cost per km before dividing by quantity.",
    )
    parser.add_argument(
        "--uncertainty-penalty-fraction",
        type=float,
        default=0.25,
        help="Fraction of interval width converted into a per-quintal risk penalty.",
    )
    return parser.parse_args()


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


def load_forecasts(path: Path, candidate_state: str) -> pd.DataFrame:
    forecasts = pd.read_csv(path)
    required = {
        "forecast_id",
        "generated_at",
        "as_of_date",
        "crop",
        "crop_id",
        "state",
        "mandi",
        "mandi_id",
        "horizon_days",
        "forecast_price_inr_qtl",
        "lower_bound_inr_qtl",
        "upper_bound_inr_qtl",
        "confidence_level",
        "model_name",
        "model_version",
    }
    missing = sorted(required - set(forecasts.columns))
    if missing:
        raise ValueError(f"Forecast output missing required columns: {missing}")
    filtered = forecasts[forecasts["state"].str.lower() == candidate_state.lower()].copy()
    if filtered.empty:
        raise ValueError(f"No forecasts found for candidate state '{candidate_state}'.")
    return filtered


def load_mandi_metadata(path: Path) -> pd.DataFrame:
    mandis = pd.read_csv(path)
    mandis["state"] = "maharashtra"
    mandis["mandi"] = mandis["market_name"].fillna("").map(slugify)
    mandis["mandi_id"] = mandis["market_name"].fillna("").map(make_mandi_id)
    required = {"mandi_id", "market_name", "latitude", "longitude", "district_name"}
    missing = sorted(required - set(mandis.columns))
    if missing:
        raise ValueError(f"Mandi metadata missing required columns: {missing}")
    return mandis


def risk_level(relative_interval_width: float) -> str:
    if relative_interval_width <= 0.2:
        return "low"
    if relative_interval_width <= 0.4:
        return "medium"
    return "high"


def build_recommendations(
    forecasts: pd.DataFrame,
    mandis: pd.DataFrame,
    farmer_latitude: float,
    farmer_longitude: float,
    quantity_quintal: float,
    road_factor: float,
    transport_cost_inr_per_km: float,
    uncertainty_penalty_fraction: float,
    candidate_state: str,
) -> pd.DataFrame:
    merged = forecasts.merge(
        mandis[["mandi_id", "market_name", "district_name", "latitude", "longitude"]],
        on="mandi_id",
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
    merged["road_distance_km"] = merged["air_distance_km"] * road_factor
    merged["estimated_transport_cost_inr_qtl"] = (
        merged["road_distance_km"] * transport_cost_inr_per_km / quantity_quintal
    )
    merged["expected_net_price_inr_qtl"] = (
        merged["forecast_price_inr_qtl"] - merged["estimated_transport_cost_inr_qtl"]
    )
    merged["interval_width_inr_qtl"] = merged["upper_bound_inr_qtl"] - merged["lower_bound_inr_qtl"]
    merged["uncertainty_penalty_inr_qtl"] = (
        merged["interval_width_inr_qtl"] * uncertainty_penalty_fraction
    )
    merged["risk_adjusted_score"] = (
        merged["expected_net_price_inr_qtl"] - merged["uncertainty_penalty_inr_qtl"]
    )
    merged["relative_interval_width"] = merged["interval_width_inr_qtl"] / merged[
        "forecast_price_inr_qtl"
    ].clip(lower=1.0)
    merged["risk_level"] = merged["relative_interval_width"].map(risk_level)
    merged = merged.sort_values(
        ["risk_adjusted_score", "expected_net_price_inr_qtl"],
        ascending=[False, False],
    ).reset_index(drop=True)
    merged["rank"] = range(1, len(merged) + 1)
    merged["recommendation_id"] = [str(uuid.uuid4()) for _ in range(len(merged))]
    merged["generated_at"] = datetime.now(UTC).replace(microsecond=0).isoformat()
    merged["quantity_quintal"] = quantity_quintal
    merged["farmer_latitude"] = farmer_latitude
    merged["farmer_longitude"] = farmer_longitude
    merged["candidate_states"] = candidate_state
    merged["reason"] = merged.apply(
        lambda row: (
            f"{row['market_name']} ranks #{row['rank']} with forecast "
            f"{row['forecast_price_inr_qtl']:.2f}, transport cost "
            f"{row['estimated_transport_cost_inr_qtl']:.2f}, and risk-adjusted score "
            f"{row['risk_adjusted_score']:.2f} INR/quintal."
        ),
        axis=1,
    )
    merged["state"] = candidate_state
    merged["mandi"] = merged["market_name"]
    output_columns = [
        "recommendation_id",
        "generated_at",
        "crop",
        "model_name",
        "horizon_days",
        "quantity_quintal",
        "farmer_latitude",
        "farmer_longitude",
        "candidate_states",
        "rank",
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


def write_report(
    report_path: Path,
    recommendations: pd.DataFrame,
    args: argparse.Namespace,
) -> None:
    top3 = recommendations.head(3).copy()
    top3["forecast_price_inr_qtl"] = top3["forecast_price_inr_qtl"].round(2)
    top3["lower_bound_inr_qtl"] = top3["lower_bound_inr_qtl"].round(2)
    top3["upper_bound_inr_qtl"] = top3["upper_bound_inr_qtl"].round(2)
    top3["estimated_transport_cost_inr_qtl"] = top3["estimated_transport_cost_inr_qtl"].round(2)
    top3["expected_net_price_inr_qtl"] = top3["expected_net_price_inr_qtl"].round(2)
    top3["uncertainty_penalty_inr_qtl"] = top3["uncertainty_penalty_inr_qtl"].round(2)
    top3["risk_adjusted_score"] = top3["risk_adjusted_score"].round(2)
    top3["road_distance_km"] = top3["road_distance_km"].round(2)

    lines = [
        "# Onion/Maharashtra 7-Day Recommendation Report",
        "",
        "## Summary",
        "",
        f"- Farmer latitude: {args.farmer_latitude}",
        f"- Farmer longitude: {args.farmer_longitude}",
        f"- Quantity: {args.quantity_quintal} quintals",
        f"- Candidate state: `{args.candidate_state}`",
        f"- Road factor: {args.road_factor}",
        f"- Transport cost assumption: {args.transport_cost_inr_per_km} INR/km total, divided by quantity",
        f"- Uncertainty penalty fraction: {args.uncertainty_penalty_fraction} of interval width",
        f"- Production forecast model: `{recommendations['model_name'].iloc[0]}` via latest `forecast_outputs_7d.csv` artifact",
        "",
        "## Top 3 Ranked Mandis",
        "",
        dataframe_to_markdown(
            top3[
                [
                    "rank",
                    "mandi",
                    "district_name",
                    "forecast_price_inr_qtl",
                    "estimated_transport_cost_inr_qtl",
                    "expected_net_price_inr_qtl",
                    "uncertainty_penalty_inr_qtl",
                    "risk_adjusted_score",
                    "risk_level",
                    "road_distance_km",
                ]
            ]
        ),
        "",
        "## Notes",
        "",
        "- Distance is haversine distance multiplied by a simple road-factor approximation.",
        "- Transport cost is intentionally transparent and easy to tune for demo sensitivity checks.",
        "- This is decision support, not a guaranteed-profit recommendation.",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    forecasts = load_forecasts(Path(args.forecasts), candidate_state=args.candidate_state)
    mandis = load_mandi_metadata(Path(args.mandis))
    recommendations = build_recommendations(
        forecasts=forecasts,
        mandis=mandis,
        farmer_latitude=args.farmer_latitude,
        farmer_longitude=args.farmer_longitude,
        quantity_quintal=args.quantity_quintal,
        road_factor=args.road_factor,
        transport_cost_inr_per_km=args.transport_cost_inr_per_km,
        uncertainty_penalty_fraction=args.uncertainty_penalty_fraction,
        candidate_state=args.candidate_state,
    )
    output_path = Path(args.output)
    report_path = Path(args.report)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    recommendations.to_csv(output_path, index=False)
    write_report(report_path, recommendations, args)

    print(f"Wrote recommendations: {output_path}")
    print(f"Wrote report: {report_path}")
    print(
        recommendations[
            [
                "rank",
                "mandi",
                "forecast_price_inr_qtl",
                "estimated_transport_cost_inr_qtl",
                "expected_net_price_inr_qtl",
                "uncertainty_penalty_inr_qtl",
                "risk_adjusted_score",
                "risk_level",
            ]
        ]
        .head(10)
        .to_string(index=False)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
