from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mandipulse.config import load_yaml_config  # noqa: E402
from mandipulse.paths import (  # noqa: E402
    baseline_predictions_path,
    clean_panel_path,
    metrics_dir,
    mvp_mandis_path,
    recommendation_backtest_path,
    recommendation_backtest_report_path,
)
from mandipulse.recommend.evaluation import (
    backtest_recommendations,
    summarize_backtest,
)  # noqa: E402
from mandipulse.utils.formatting import dataframe_to_markdown  # noqa: E402
from mandipulse.utils.text import make_mandi_id, slugify  # noqa: E402

_CONFIG_PATH = "configs/recommendation.yaml"


def parse_args(cfg: dict) -> argparse.Namespace:
    tc = cfg.get("transport_cost", {})
    rk = cfg.get("ranking", {})
    rt = cfg.get("risk_thresholds", {})

    parser = argparse.ArgumentParser(
        description=(
            "Evaluate recommendation quality via regret@K and nearest-mandi baseline "
            "over the leakage-safe baseline predictions (test split)."
        )
    )
    parser.add_argument("--predictions", default=str(baseline_predictions_path()))
    parser.add_argument("--panel", default=str(clean_panel_path()))
    parser.add_argument("--mandis", default=str(mvp_mandis_path()))
    parser.add_argument("--output", default=str(recommendation_backtest_path()))
    parser.add_argument("--report", default=str(recommendation_backtest_report_path()))
    parser.add_argument(
        "--split",
        default="test",
        choices=["test", "validation", "all"],
        help="Which split of baseline predictions to backtest over.",
    )
    parser.add_argument("--model", default="moving_average_7d")
    parser.add_argument(
        "--k-values",
        nargs="+",
        type=int,
        default=[1, 3],
        help="Values of K for regret@K (default: 1 3).",
    )
    parser.add_argument("--farmer-latitude", type=float, default=19.99750)
    parser.add_argument("--farmer-longitude", type=float, default=73.78981)
    parser.add_argument("--road-factor", type=float, default=tc.get("road_distance_factor", 1.3))
    parser.add_argument("--cost-per-km", type=float, default=tc.get("cost_per_km_per_quintal", 4.0))
    parser.add_argument(
        "--penalty-weight", type=float, default=rk.get("uncertainty_penalty_weight", 0.3)
    )
    parser.add_argument(
        "--low-max-pct",
        type=float,
        default=rt.get("low_max_interval_pct", 10) / 100,
    )
    parser.add_argument(
        "--high-min-pct",
        type=float,
        default=rt.get("high_min_interval_pct", 25) / 100,
    )
    return parser.parse_args()


def load_interval_residuals(model_name: str) -> tuple[float, float]:
    metadata_path = metrics_dir() / "forecast_interval_metadata_7d.csv"
    if not metadata_path.exists():
        raise FileNotFoundError(
            f"Interval metadata not found: {metadata_path}\n"
            "Run scripts/build_forecast_intervals_7d.py first."
        )
    meta = pd.read_csv(metadata_path)
    row = meta[meta["model_name"] == model_name]
    if row.empty:
        raise ValueError(f"No interval metadata found for model '{model_name}'.")
    return float(row["lower_residual"].iloc[0]), float(row["upper_residual"].iloc[0])


def load_mandi_metadata(path: Path) -> pd.DataFrame:
    mandis = pd.read_csv(path)
    mandis["state"] = "maharashtra"
    mandis["mandi"] = mandis["market_name"].fillna("").map(slugify)
    mandis["mandi_id"] = mandis["market_name"].fillna("").map(make_mandi_id)
    return mandis


def write_report(
    report_path: Path,
    backtest: pd.DataFrame,
    args: argparse.Namespace,
    lower_residual: float,
    upper_residual: float,
) -> None:
    k_values = args.k_values

    lines = [
        "# Onion/Maharashtra 7-Day Recommendation Backtest",
        "",
        "## Method",
        "",
        f"- Forecast model: `{args.model}` (moving-average baseline, the shipped MVP forecaster)",
        f"- Backtest split: `{args.split}`",
        f"- Interval calibration: lower residual {lower_residual:.2f}, upper residual {upper_residual:.2f} INR/quintal",
        "- Leakage safeguard: predictions come from the leakage-safe baseline predictions artifact",
        "  (`baseline_predictions_7d.csv`), which uses only information up to each as-of date.",
        "- Realized price: modal price from the clean panel at as-of date + 7 days",
        "  (+-2-day tolerance; observed rows preferred over imputed).",
        f"- Farmer location: ({args.farmer_latitude}, {args.farmer_longitude}) -- Nashik region",
        f"- Road distance factor: {args.road_factor}",
        f"- Transport cost: {args.cost_per_km} INR/km/quintal",
        f"- Uncertainty penalty weight: {args.penalty_weight}",
        "",
        "## Summary Metrics",
        "",
    ]

    metrics = summarize_backtest(backtest, k_values)

    if not metrics:
        lines.append("*No backtest rows produced -- check prediction and panel artifacts.*")
    else:
        date_range = f"{metrics['date_min']} to {metrics['date_max']}"
        summary_rows = []

        for k in k_values:
            col = f"regret_at_{k}"
            if f"regret_at_{k}_mean" not in metrics:
                continue
            mean_val = metrics[f"regret_at_{k}_mean"]
            median_val = metrics[f"regret_at_{k}_median"]
            optimal_rate = metrics[f"optimal_rate_{k}"] * 100
            beats_rate = metrics[f"beats_nearest_{k}"] * 100
            summary_rows.append(
                {
                    "metric": f"Regret@{k} (mean)",
                    "value": f"{mean_val:.1f} INR/qtl" if not pd.isna(mean_val) else "N/A",
                }
            )
            summary_rows.append(
                {
                    "metric": f"Regret@{k} (median)",
                    "value": f"{median_val:.1f} INR/qtl" if not pd.isna(median_val) else "N/A",
                }
            )
            summary_rows.append(
                {
                    "metric": f"Optimal rate@{k} (top-{k} captured best mandi)",
                    "value": f"{optimal_rate:.1f}%",
                }
            )
            summary_rows.append(
                {
                    "metric": f"Beats nearest-mandi@{k}",
                    "value": f"{beats_rate:.1f}%",
                }
            )
            del col

        nm_mean = metrics["nearest_mandi_regret_mean"]
        nm_median = metrics["nearest_mandi_regret_median"]
        summary_rows.append(
            {
                "metric": "Nearest-mandi baseline regret (mean)",
                "value": f"{nm_mean:.1f} INR/qtl" if not pd.isna(nm_mean) else "N/A",
            }
        )
        summary_rows.append(
            {
                "metric": "Nearest-mandi baseline regret (median)",
                "value": f"{nm_median:.1f} INR/qtl" if not pd.isna(nm_median) else "N/A",
            }
        )
        summary_rows.append({"metric": "As-of dates evaluated", "value": str(metrics["n_dates"])})
        summary_rows.append({"metric": "Date range", "value": date_range})
        summary_rows.append(
            {
                "metric": "Mandi-dates dropped (no realized price)",
                "value": str(metrics["n_dropped"]),
            }
        )

        lines.append(dataframe_to_markdown(pd.DataFrame(summary_rows)))
        lines.append("")

        # Verdict
        lines.append("## Verdict")
        lines.append("")
        mean_r1 = metrics.get("regret_at_1_mean", float("nan"))
        if not pd.isna(mean_r1):
            mean_nm = nm_mean if not pd.isna(nm_mean) else float("nan")
            if mean_r1 <= mean_nm:
                verdict = (
                    f"The model's top-1 recommendation achieves **mean regret@1 of {mean_r1:.1f} INR/qtl**, "
                    f"which is better than the nearest-mandi baseline ({mean_nm:.1f} INR/qtl). "
                    "The ranking earns its place over the naive strategy."
                )
            else:
                verdict = (
                    f"The model's top-1 recommendation achieves **mean regret@1 of {mean_r1:.1f} INR/qtl**, "
                    f"which is **worse** than the nearest-mandi baseline ({mean_nm:.1f} INR/qtl). "
                    "The nearest-mandi policy outperforms the model on this backtest window. "
                    "See M3-04 in TRACKER.md for the open lever (reformulate target/features)."
                )
            lines.append(verdict)
        lines.append("")

    lines += [
        "## Assumptions and Caveats",
        "",
        "- Realized-price tolerance: +-2 days. Observed rows preferred; imputed used as fallback.",
        "- Transport cost is haversine x road_factor x cost_per_km -- same formula as the recommendation engine.",
        "- This is offline evaluation on historical data; past regret does not guarantee future performance.",
        "- This is decision support, not a guaranteed-profit recommendation.",
    ]

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    cfg = load_yaml_config(_CONFIG_PATH)
    args = parse_args(cfg)

    print("Loading artifacts...")
    predictions = pd.read_csv(args.predictions)
    panel = pd.read_csv(args.panel)
    mandis = load_mandi_metadata(Path(args.mandis))

    # Filter to requested split and model
    if args.split != "all":
        predictions = predictions[predictions["split"] == args.split]
    predictions = predictions[predictions["model"] == args.model]

    if predictions.empty:
        print(
            f"ERROR: No predictions found for model='{args.model}' split='{args.split}' "
            f"in {args.predictions}"
        )
        return 1

    n_dates = predictions["date"].nunique()
    print(
        f"Backtesting over {n_dates} as-of dates "
        f"({predictions['date'].min()} to {predictions['date'].max()})"
    )

    lower_residual, upper_residual = load_interval_residuals(args.model)
    print(f"Interval residuals: lower={lower_residual:.2f}, upper={upper_residual:.2f}")

    backtest = backtest_recommendations(
        panel=panel,
        mandis=mandis,
        predictions=predictions,
        k_values=args.k_values,
        farmer_lat=args.farmer_latitude,
        farmer_lon=args.farmer_longitude,
        cost_per_km_per_quintal=args.cost_per_km,
        road_distance_factor=args.road_factor,
        uncertainty_penalty_weight=args.penalty_weight,
        low_max_interval_pct=args.low_max_pct,
        high_min_interval_pct=args.high_min_pct,
        lower_residual=lower_residual,
        upper_residual=upper_residual,
    )

    if backtest.empty:
        print("WARNING: Backtest produced no rows. Check that panel and predictions overlap.")
        return 1

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    backtest.to_csv(output_path, index=False)
    print(f"Wrote backtest artifact: {output_path} ({len(backtest)} rows)")

    report_path = Path(args.report)
    write_report(report_path, backtest, args, lower_residual, upper_residual)
    print(f"Wrote report: {report_path}")

    # Print summary to console
    for k in args.k_values:
        col = f"regret_at_{k}"
        if col in backtest.columns:
            mean_r = backtest[col].dropna().mean()
            print(f"Mean regret@{k}: {mean_r:.1f} INR/qtl")
    nm = backtest["nearest_mandi_regret"].dropna().mean()
    print(f"Mean nearest-mandi baseline regret: {nm:.1f} INR/qtl")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
