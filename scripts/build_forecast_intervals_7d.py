from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mandipulse.modeling.baselines import predict_baselines  # noqa: E402
from mandipulse.modeling.columns import (  # noqa: E402
    DATE_COLUMN,
    MARKET_ID_COLUMN,
)
from mandipulse.modeling.intervals import (  # noqa: E402
    build_backtest,
    build_latest_forecast_output,
    compute_interval_residuals,
    latest_forecastable_rows,
    summarize_backtest,
)
from mandipulse.modeling.splits import (  # noqa: E402
    SplitConfig,
    apply_row_filter,
    load_trainable_features,
    make_temporal_splits,
)
from mandipulse.utils.formatting import dataframe_to_markdown  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build residual uncertainty intervals and latest forecast outputs for the 7-day MVP."
    )
    parser.add_argument(
        "--features",
        default="data/processed/onion_maharashtra/feature_table_7d.csv",
    )
    parser.add_argument(
        "--report",
        default="reports/modeling/forecast_intervals_7d.md",
    )
    parser.add_argument(
        "--forecast-output",
        default="artifacts/forecasts/forecast_outputs_7d.csv",
    )
    parser.add_argument(
        "--backtest-output",
        default="artifacts/metrics/forecast_interval_backtest_7d.csv",
    )
    parser.add_argument(
        "--interval-metadata-output",
        default="artifacts/metrics/forecast_interval_metadata_7d.csv",
    )
    parser.add_argument("--validation-days", type=int, default=90)
    parser.add_argument("--test-days", type=int, default=90)
    parser.add_argument("--horizon-days", type=int, default=7)
    parser.add_argument("--ridge-alpha", type=float, default=1.0)
    parser.add_argument(
        "--row-filter",
        choices=["all", "observed_only"],
        default="all",
    )
    parser.add_argument(
        "--model-name",
        choices=["seasonal_naive_7d", "moving_average_7d", "moving_average_30d"],
        default="moving_average_7d",
        help="Baseline model for interval calibration (ridge not supported for latest forecast output).",
    )
    parser.add_argument("--confidence-level", type=float, default=0.90)
    return parser.parse_args()


def load_full_feature_table(path: Path) -> pd.DataFrame:
    features = pd.read_csv(path)
    features[DATE_COLUMN] = pd.to_datetime(features[DATE_COLUMN])
    return features.sort_values([DATE_COLUMN, MARKET_ID_COLUMN]).reset_index(drop=True)


def write_report(
    report_path: Path,
    feature_path: Path,
    model_name: str,
    row_filter: str,
    confidence_level: float,
    lower_residual: float,
    upper_residual: float,
    interval_summary: pd.DataFrame,
    latest_forecasts: pd.DataFrame,
) -> None:
    latest_preview = latest_forecasts[
        [
            "mandi",
            "as_of_date",
            "forecast_price_inr_qtl",
            "lower_bound_inr_qtl",
            "upper_bound_inr_qtl",
        ]
    ].sort_values("mandi")

    lines = [
        "# Onion/Maharashtra 7-Day Forecast Intervals",
        "",
        "## Summary",
        "",
        f"- Feature table: `{feature_path}`",
        f"- Production forecast model for MVP intervals: `{model_name}`",
        f"- Row filter used for calibration/evaluation: `{row_filter}`",
        f"- Confidence level: {confidence_level:.2f}",
        f"- Validation residual lower adjustment: {round(lower_residual, 2)} INR/quintal",
        f"- Validation residual upper adjustment: {round(upper_residual, 2)} INR/quintal",
        "",
        "## Empirical Interval Performance",
        "",
        dataframe_to_markdown(interval_summary),
        "",
        "## Latest Forecast Output Preview",
        "",
        dataframe_to_markdown(latest_preview),
        "",
        "## Notes",
        "",
        "- Intervals are empirical residual intervals calibrated on the validation split and evaluated on the held-out test split.",
        "- This keeps the uncertainty story aligned with the current MVP decision to ship the strongest honest baseline first.",
        "- Bounds are not guarantees; the dashboard should present them as uncertainty estimates with measured coverage.",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    feature_path = Path(args.features)
    report_path = Path(args.report)
    forecast_output_path = Path(args.forecast_output)
    backtest_output_path = Path(args.backtest_output)
    interval_metadata_output_path = Path(args.interval_metadata_output)

    trainable = load_trainable_features(feature_path)
    filtered = apply_row_filter(trainable, args.row_filter)
    train, validation, test, _ = make_temporal_splits(
        filtered,
        SplitConfig(
            validation_days=args.validation_days,
            test_days=args.test_days,
            horizon_days=args.horizon_days,
        ),
    )
    predictions = predict_baselines(train, validation, test, ridge_alpha=args.ridge_alpha)
    lower_residual, upper_residual = compute_interval_residuals(
        predictions=predictions,
        model_name=args.model_name,
        confidence_level=args.confidence_level,
    )
    backtest = build_backtest(
        predictions=predictions,
        model_name=args.model_name,
        lower_residual=lower_residual,
        upper_residual=upper_residual,
        confidence_level=args.confidence_level,
    )
    interval_summary = summarize_backtest(backtest)

    full_features = load_full_feature_table(feature_path)
    latest_rows = latest_forecastable_rows(full_features, model_name=args.model_name)
    latest_forecasts = build_latest_forecast_output(
        latest_rows=latest_rows,
        model_name=args.model_name,
        lower_residual=lower_residual,
        upper_residual=upper_residual,
        confidence_level=args.confidence_level,
    )

    interval_metadata = pd.DataFrame(
        [
            {
                "model_name": args.model_name,
                "row_filter": args.row_filter,
                "confidence_level": args.confidence_level,
                "lower_residual": round(lower_residual, 6),
                "upper_residual": round(upper_residual, 6),
                "validation_rows": len(backtest[backtest["split"] == "validation"]),
                "test_rows": len(backtest[backtest["split"] == "test"]),
            }
        ]
    )

    forecast_output_path.parent.mkdir(parents=True, exist_ok=True)
    backtest_output_path.parent.mkdir(parents=True, exist_ok=True)
    interval_metadata_output_path.parent.mkdir(parents=True, exist_ok=True)
    latest_forecasts.to_csv(forecast_output_path, index=False)
    backtest.to_csv(backtest_output_path, index=False)
    interval_metadata.to_csv(interval_metadata_output_path, index=False)
    write_report(
        report_path=report_path,
        feature_path=feature_path,
        model_name=args.model_name,
        row_filter=args.row_filter,
        confidence_level=args.confidence_level,
        lower_residual=lower_residual,
        upper_residual=upper_residual,
        interval_summary=interval_summary,
        latest_forecasts=latest_forecasts,
    )

    print(f"Wrote forecast outputs: {forecast_output_path}")
    print(f"Wrote backtest outputs: {backtest_output_path}")
    print(f"Wrote interval metadata: {interval_metadata_output_path}")
    print(f"Wrote report: {report_path}")
    print(interval_summary.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
