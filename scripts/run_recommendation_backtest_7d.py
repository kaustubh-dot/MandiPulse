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
from mandipulse.recommend.evaluation import backtest_recommendations  # noqa: E402
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
        "  (±2-day tolerance; observed rows preferred over imputed).",
        f"- Farmer location: ({args.farmer_latitude}, {args.farmer_longitude}) — Nashik region",
        f"- Road distance factor: {args.road_factor}",
        f"- Transport cost: {args.cost_per_km} INR/km/quintal",
        f"- Uncertainty penalty weight: {args.penalty_weight}",
        "",
        "## Summary Metrics",
        "",
    ]

    n_dates = len(backtest)
    if n_dates == 0:
        lines.append("*No backtest rows produced — check prediction and panel artifacts.*")
    else:
        date_range = f"{backtest['as_of_date'].min()} → {backtest['as_of_date'].max()}"
        summary_rows = []

        for k in k_values:
            col = f"regret_at_{k}"
            if col in backtest.columns:
                valid = backtest[col].dropna()
                # "Optimal rate" = how often the top-K captured the best mandi (zero regret).
                optimal_rate = float((valid <= 0).mean()) * 100 if not valid.empty else float("nan")
                # "Beats nearest" = how often top-K regret is strictly below the
                # nearest-mandi baseline regret (the comparison this milestone is about).
                both = backtest[[col, "nearest_mandi_regret"]].dropna()
                beats_rate = (
                    float((both[col] < both["nearest_mandi_regret"]).mean()) * 100
                    if not both.empty
                    else float("nan")
                )
                summary_rows.append(
                    {
                        "metric": f"Regret@{k} (mean)",
                        "value": f"{valid.mean():.1f} INR/qtl" if not valid.empty else "N/A",
                    }
                )
                summary_rows.append(
                    {
                        "metric": f"Regret@{k} (median)",
                        "value": f"{valid.median():.1f} INR/qtl" if not valid.empty else "N/A",
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

        nm_regret = backtest["nearest_mandi_regret"].dropna()
        summary_rows.append(
            {
                "metric": "Nearest-mandi baseline regret (mean)",
                "value": f"{nm_regret.mean():.1f} INR/qtl" if not nm_regret.empty else "N/A",
            }
        )
        summary_rows.append(
            {
                "metric": "Nearest-mandi baseline regret (median)",
                "value": f"{nm_regret.median():.1f} INR/qtl" if not nm_regret.empty else "N/A",
            }
        )
        summary_rows.append({"metric": "As-of dates evaluated", "value": str(n_dates)})
        summary_rows.append({"metric": "Date range", "value": date_range})
        total_dropped = int(backtest["n_dropped"].sum())
        summary_rows.append(
            {"metric": "Mandi-dates dropped (no realized price)", "value": str(total_dropped)}
        )

        lines.append(dataframe_to_markdown(pd.DataFrame(summary_rows)))
        lines.append("")

        # Verdict
        lines.append("## Verdict")
        lines.append("")
        if "regret_at_1" in backtest.columns:
            mean_r1 = backtest["regret_at_1"].dropna().mean()
            mean_nm = nm_regret.mean() if not nm_regret.empty else float("nan")
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
        "- Realized-price tolerance: ±2 days. Observed rows preferred; imputed used as fallback.",
        "- Transport cost is haversine × road_factor × cost_per_km — same formula as the recommendation engine.",
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
