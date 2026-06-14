from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mandipulse.config import load_yaml_config  # noqa: E402
from mandipulse.recommend.engine import score_recommendations  # noqa: E402
from mandipulse.utils.formatting import dataframe_to_markdown  # noqa: E402
from mandipulse.utils.text import make_mandi_id, slugify  # noqa: E402

_CONFIG_PATH = "configs/recommendation.yaml"


def _load_recommend_config() -> dict:
    return load_yaml_config(_CONFIG_PATH)


def parse_args(cfg: dict) -> argparse.Namespace:
    tc = cfg.get("transport_cost", {})
    rk = cfg.get("ranking", {})
    rt = cfg.get("risk_thresholds", {})

    parser = argparse.ArgumentParser(
        description="Build transport-aware 7-day mandi recommendations from latest forecast outputs."
    )
    parser.add_argument("--forecasts", default="artifacts/forecasts/forecast_outputs_7d.csv")
    parser.add_argument("--mandis", default="data/external/mvp_mandis.csv")
    parser.add_argument("--report", default="reports/modeling/recommendation_report_7d.md")
    parser.add_argument(
        "--output", default="artifacts/recommendations/recommendation_outputs_7d.csv"
    )
    parser.add_argument("--farmer-latitude", type=float, default=19.99750)
    parser.add_argument("--farmer-longitude", type=float, default=73.78981)
    parser.add_argument("--quantity-quintal", type=float, default=100.0)
    parser.add_argument("--candidate-state", default="maharashtra")
    parser.add_argument(
        "--road-factor",
        type=float,
        default=tc.get("road_distance_factor", 1.3),
        help="Approximate road-vs-airline distance multiplier (from configs/recommendation.yaml).",
    )
    parser.add_argument(
        "--cost-per-km-per-quintal",
        type=float,
        default=tc.get("cost_per_km_per_quintal", 4.0),
        help="Transport cost in INR per km per quintal (from configs/recommendation.yaml).",
    )
    parser.add_argument(
        "--uncertainty-penalty-weight",
        type=float,
        default=rk.get("uncertainty_penalty_weight", 0.3),
        help="Fraction of interval width converted into a per-quintal risk penalty.",
    )
    parser.add_argument(
        "--low-max-interval-pct",
        type=float,
        default=rt.get("low_max_interval_pct", 10) / 100,
        help="Relative interval width at or below which risk is 'low'.",
    )
    parser.add_argument(
        "--high-min-interval-pct",
        type=float,
        default=rt.get("high_min_interval_pct", 25) / 100,
        help="Relative interval width at or above which risk is 'high'.",
    )
    return parser.parse_args()


def load_forecasts(path: Path, candidate_state: str) -> pd.DataFrame:
    forecasts = pd.read_csv(path)
    required = {
        "forecast_id",
        "generated_at",
        "as_of_date",
        "crop",
        "state",
        "mandi",
        "mandi_id",
        "market_id",
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
    required = {"market_id", "mandi_id", "market_name", "latitude", "longitude", "district_name"}
    missing = sorted(required - set(mandis.columns))
    if missing:
        raise ValueError(f"Mandi metadata missing required columns: {missing}")
    return mandis


def write_report(
    report_path: Path,
    recommendations: pd.DataFrame,
    args: argparse.Namespace,
) -> None:
    top3 = recommendations.head(3).copy()
    for col in [
        "forecast_price_inr_qtl",
        "lower_bound_inr_qtl",
        "upper_bound_inr_qtl",
        "estimated_transport_cost_inr_qtl",
        "expected_net_price_inr_qtl",
        "uncertainty_penalty_inr_qtl",
        "risk_adjusted_score",
        "road_distance_km",
    ]:
        top3[col] = top3[col].round(2)

    lines = [
        "# Onion/Maharashtra 7-Day Recommendation Report",
        "",
        "## Summary",
        "",
        f"- Farmer latitude: {args.farmer_latitude}",
        f"- Farmer longitude: {args.farmer_longitude}",
        f"- Quantity: {args.quantity_quintal} quintals",
        f"- Candidate state: `{args.candidate_state}`",
        f"- Road distance factor: {args.road_factor} (from configs/recommendation.yaml)",
        f"- Transport cost: {args.cost_per_km_per_quintal} INR/km/quintal (from configs/recommendation.yaml)",
        f"- Uncertainty penalty weight: {args.uncertainty_penalty_weight} (from configs/recommendation.yaml)",
        f"- Risk thresholds: low ≤ {args.low_max_interval_pct:.0%}, high ≥ {args.high_min_interval_pct:.0%} (from configs/recommendation.yaml)",
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
        "- Distance is haversine distance multiplied by road_distance_factor from configs/recommendation.yaml.",
        "- Transport cost is INR per km per quintal (load-size-independent), consistent with the config unit.",
        "- This is decision support, not a guaranteed-profit recommendation.",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    cfg = _load_recommend_config()
    args = parse_args(cfg)

    forecasts = load_forecasts(Path(args.forecasts), candidate_state=args.candidate_state)
    mandis = load_mandi_metadata(Path(args.mandis))
    recommendations = score_recommendations(
        forecasts=forecasts,
        mandis=mandis,
        farmer_latitude=args.farmer_latitude,
        farmer_longitude=args.farmer_longitude,
        cost_per_km_per_quintal=args.cost_per_km_per_quintal,
        road_distance_factor=args.road_factor,
        uncertainty_penalty_weight=args.uncertainty_penalty_weight,
        low_max_interval_pct=args.low_max_interval_pct,
        high_min_interval_pct=args.high_min_interval_pct,
        candidate_state=args.candidate_state,
    )
    # Attach request-context metadata for traceability
    recommendations.insert(4, "farmer_latitude", args.farmer_latitude)
    recommendations.insert(5, "farmer_longitude", args.farmer_longitude)
    recommendations.insert(6, "quantity_quintal", args.quantity_quintal)

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
