from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mandipulse.modeling.baselines import predict_baselines  # noqa: E402
from mandipulse.modeling.columns import MARKET_ID_COLUMN, MARKET_NAME_COLUMN  # noqa: E402
from mandipulse.modeling.metrics import per_market_metrics, summarize_predictions  # noqa: E402
from mandipulse.modeling.splits import (  # noqa: E402
    SplitConfig,
    SplitDates,
    apply_row_filter,
    load_trainable_features,
    make_temporal_splits,
)
from mandipulse.modeling.tracking import (
    log_artifact,
    log_metrics,
    log_params,
    set_experiment,
    start_run,
)  # noqa: E402
from mandipulse.utils.formatting import dataframe_to_markdown  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train and evaluate 7-day Onion/Maharashtra baseline models."
    )
    parser.add_argument(
        "--features",
        default="data/processed/onion_maharashtra/feature_table_7d.csv",
        help="Path to the generated 7-day feature table.",
    )
    parser.add_argument(
        "--report",
        default="reports/modeling/baseline_metrics_7d.md",
        help="Markdown report output path.",
    )
    parser.add_argument(
        "--predictions",
        default="artifacts/predictions/baseline_predictions_7d.csv",
        help="Per-row validation/test prediction output path.",
    )
    parser.add_argument("--validation-days", type=int, default=90)
    parser.add_argument("--test-days", type=int, default=90)
    parser.add_argument("--horizon-days", type=int, default=7)
    parser.add_argument("--ridge-alpha", type=float, default=1.0)
    parser.add_argument(
        "--row-filter",
        choices=("all", "observed_only"),
        default="all",
        help="Training/evaluation row filter.",
    )
    return parser.parse_args()


def write_report(
    report_path: Path,
    feature_path: Path,
    prediction_path: Path,
    split_dates: SplitDates,
    row_filter: str,
    train: pd.DataFrame,
    validation: pd.DataFrame,
    test: pd.DataFrame,
    summary: pd.DataFrame,
    per_market: pd.DataFrame,
) -> None:
    best_test = summary[summary["split"] == "test"].sort_values("mae").iloc[0]
    ridge_test = summary[(summary["split"] == "test") & (summary["model"] == "ridge")].iloc[0]
    test_market_table = (
        per_market[(per_market["split"] == "test") & (per_market["model"] == best_test["model"])]
        .sort_values("mae")
        .loc[
            :,
            [MARKET_ID_COLUMN, MARKET_NAME_COLUMN, "rows", "mae", "rmse", "smape_pct", "mase"],
        ]
    )

    lines = [
        "# Onion/Maharashtra 7-Day Baseline Metrics",
        "",
        "## Summary",
        "",
        f"- Feature table: `{feature_path}`",
        f"- Prediction rows: `{prediction_path}`",
        f"- Train rows: {len(train):,}",
        f"- Validation rows: {len(validation):,}",
        f"- Test rows: {len(test):,}",
        f"- Markets: {train[MARKET_ID_COLUMN].nunique():,}",
        f"- Row filter: `{row_filter}`",
        f"- Observed targets in train: {int(train['target_observed_t_plus_7'].sum()):,}",
        f"- Observed targets in validation: {int(validation['target_observed_t_plus_7'].sum()):,}",
        f"- Observed targets in test: {int(test['target_observed_t_plus_7'].sum()):,}",
        f"- Train dates: {split_dates.train_start.date()} to {split_dates.train_end.date()}",
        f"- Validation dates: {split_dates.validation_start.date()} to {split_dates.validation_end.date()}",
        f"- Test dates: {split_dates.test_start.date()} to {split_dates.test_end.date()}",
        f"- Best test baseline by MAE: `{best_test['model']}` ({best_test['mae']} INR/quintal)",
        f"- Ridge test MAE: {ridge_test['mae']} INR/quintal",
        "- Next sanity check: run observed-only/imputation sensitivity before treating "
        "LightGBM as the next guaranteed step.",
        "",
        "## Overall Metrics",
        "",
        dataframe_to_markdown(summary),
        "",
        "## Best Test Baseline By Mandi",
        "",
        dataframe_to_markdown(test_market_table),
        "",
        "## Baseline Definitions",
        "",
        "- `seasonal_naive_7d`: predicts the 7-day-ahead price as the current as-of date modal price.",
        "- `moving_average_7d`: predicts using the 7-day rolling mean available on the as-of date.",
        "- `moving_average_30d`: predicts using the 30-day rolling mean available on the as-of date.",
        "- `ridge`: linear baseline using lag, rolling, return, calendar, market, and district features.",
        "",
        "## Metric Notes",
        "",
        "- MAE/RMSE are INR per quintal.",
        "- sMAPE is percentage error.",
        "- MASE is scaled by the average absolute 7-day seasonal difference in the training period.",
        "- Splits are date-based only; no random split is used.",
        "- The training split is purged by the forecast horizon so no training target resolves "
        "inside the validation window.",
        "- The validation split is also purged by the forecast horizon so no validation target "
        "resolves inside the test window (both gaps = horizon_days = 7 days).",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    feature_path = Path(args.features)
    report_path = Path(args.report)
    prediction_path = Path(args.predictions)

    trainable = load_trainable_features(feature_path)
    filtered = apply_row_filter(trainable, args.row_filter)
    train, validation, test, split_dates = make_temporal_splits(
        filtered,
        SplitConfig(
            validation_days=args.validation_days,
            test_days=args.test_days,
            horizon_days=args.horizon_days,
        ),
    )
    predictions = predict_baselines(train, validation, test, ridge_alpha=args.ridge_alpha)
    summary = summarize_predictions(predictions, train)

    per_market = pd.concat(
        [
            per_market_metrics(predictions, split_name, model_name, train)
            for split_name in ["validation", "test"]
            for model_name in sorted(predictions["model"].unique())
        ],
        ignore_index=True,
    )

    prediction_path.parent.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(prediction_path, index=False)
    write_report(
        report_path=report_path,
        feature_path=feature_path,
        prediction_path=prediction_path,
        split_dates=split_dates,
        row_filter=args.row_filter,
        train=train,
        validation=validation,
        test=test,
        summary=summary,
        per_market=per_market,
    )

    # MLflow tracking — one run per model
    set_experiment("mandipulse_baselines_7d")
    for model_name in sorted(summary["model"].unique()):
        val_row = summary[(summary["split"] == "validation") & (summary["model"] == model_name)]
        test_row = summary[(summary["split"] == "test") & (summary["model"] == model_name)]
        with start_run(run_name=f"baseline_{model_name}"):
            log_params(
                {
                    "model": model_name,
                    "row_filter": args.row_filter,
                    "ridge_alpha": args.ridge_alpha,
                    "train_start": str(split_dates.train_start.date()),
                    "train_end": str(split_dates.train_end.date()),
                    "validation_start": str(split_dates.validation_start.date()),
                    "validation_end": str(split_dates.validation_end.date()),
                    "test_start": str(split_dates.test_start.date()),
                    "test_end": str(split_dates.test_end.date()),
                }
            )
            metrics: dict[str, float] = {}
            if not val_row.empty:
                r = val_row.iloc[0]
                metrics.update(
                    {
                        "val_mae": float(r["mae"]),
                        "val_rmse": float(r["rmse"]),
                        "val_smape_pct": float(r["smape_pct"]),
                        "val_mase": float(r["mase"]),
                    }
                )
            if not test_row.empty:
                r = test_row.iloc[0]
                metrics.update(
                    {
                        "test_mae": float(r["mae"]),
                        "test_rmse": float(r["rmse"]),
                        "test_smape_pct": float(r["smape_pct"]),
                        "test_mase": float(r["mase"]),
                    }
                )
            log_metrics(metrics)
            log_artifact(report_path)

    print(f"Wrote predictions: {prediction_path}")
    print(f"Wrote report: {report_path}")
    print(summary.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
