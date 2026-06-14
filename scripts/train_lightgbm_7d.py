from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mandipulse.modeling.baselines import predict_baselines  # noqa: E402
from mandipulse.modeling.columns import MARKET_ID_COLUMN, MARKET_NAME_COLUMN  # noqa: E402
from mandipulse.modeling.lightgbm_model import predict_lightgbm  # noqa: E402
from mandipulse.modeling.metrics import per_market_metrics, summarize_predictions  # noqa: E402
from mandipulse.modeling.splits import (  # noqa: E402
    SplitConfig,
    apply_row_filter,
    load_trainable_features,
    make_temporal_splits,
)
from mandipulse.utils.formatting import dataframe_to_markdown  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train and evaluate a first LightGBM 7-day Onion/Maharashtra model."
    )
    parser.add_argument(
        "--features",
        default="data/processed/onion_maharashtra/feature_table_7d.csv",
    )
    parser.add_argument(
        "--report",
        default="reports/modeling/lightgbm_metrics_7d.md",
    )
    parser.add_argument(
        "--metrics-csv",
        default="artifacts/metrics/lightgbm_metrics_7d.csv",
    )
    parser.add_argument(
        "--predictions-csv",
        default="artifacts/predictions/lightgbm_predictions_7d.csv",
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
    parser.add_argument("--n-estimators", type=int, default=400)
    parser.add_argument("--learning-rate", type=float, default=0.05)
    parser.add_argument("--num-leaves", type=int, default=31)
    parser.add_argument("--min-child-samples", type=int, default=20)
    parser.add_argument("--subsample", type=float, default=0.9)
    parser.add_argument("--colsample-bytree", type=float, default=0.9)
    parser.add_argument("--reg-alpha", type=float, default=0.0)
    parser.add_argument("--reg-lambda", type=float, default=0.0)
    parser.add_argument("--random-state", type=int, default=42)
    return parser.parse_args()


def write_report(
    report_path: Path,
    feature_path: Path,
    metrics_path: Path,
    prediction_path: Path,
    row_filter: str,
    train: pd.DataFrame,
    validation: pd.DataFrame,
    test: pd.DataFrame,
    summary: pd.DataFrame,
    per_market: pd.DataFrame,
) -> None:
    test_summary = summary[summary["split"] == "test"].sort_values("mae").reset_index(drop=True)
    best_test = test_summary.iloc[0]
    lightgbm_test = test_summary[test_summary["model"] == "lightgbm"].iloc[0]
    moving_average_test = test_summary[test_summary["model"] == "moving_average_7d"].iloc[0]
    mae_delta = round(lightgbm_test["mae"] - moving_average_test["mae"], 2)
    best_market_table = (
        per_market[(per_market["split"] == "test") & (per_market["model"] == "lightgbm")]
        .sort_values("mae")
        .loc[
            :,
            [MARKET_ID_COLUMN, MARKET_NAME_COLUMN, "rows", "mae", "rmse", "smape_pct", "mase"],
        ]
    )

    lines = [
        "# Onion/Maharashtra 7-Day LightGBM Metrics",
        "",
        "## Summary",
        "",
        f"- Feature table: `{feature_path}`",
        f"- Metrics CSV: `{metrics_path}`",
        f"- Prediction rows: `{prediction_path}`",
        f"- Row filter: `{row_filter}`",
        f"- Train rows: {len(train):,}",
        f"- Validation rows: {len(validation):,}",
        f"- Test rows: {len(test):,}",
        f"- Markets: {train[MARKET_ID_COLUMN].nunique():,}",
        f"- Best test model by MAE: `{best_test['model']}` ({best_test['mae']} INR/quintal)",
        f"- LightGBM test MAE: {lightgbm_test['mae']} INR/quintal",
        f"- Moving-average 7d test MAE: {moving_average_test['mae']} INR/quintal",
        f"- LightGBM MAE delta vs moving_average_7d: {mae_delta} INR/quintal",
        "",
        "## Overall Metrics",
        "",
        dataframe_to_markdown(summary.sort_values(["split", "mae"]).reset_index(drop=True)),
        "",
        "## LightGBM Test Metrics By Mandi",
        "",
        dataframe_to_markdown(best_market_table),
        "",
        "## Interview Note",
        "",
        "- If LightGBM beats the moving average baseline, the nonlinear model earns its place in the MVP loop.",
        "- If it does not, the honest story is still strong: the baseline is tough, and the next lever is target reformulation or richer exogenous features rather than pretending the booster won.",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    feature_path = Path(args.features)
    report_path = Path(args.report)
    metrics_path = Path(args.metrics_csv)
    predictions_path = Path(args.predictions_csv)

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

    baseline_predictions = predict_baselines(train, validation, test, ridge_alpha=args.ridge_alpha)
    lightgbm_predictions = predict_lightgbm(
        train,
        validation,
        test,
        n_estimators=args.n_estimators,
        learning_rate=args.learning_rate,
        num_leaves=args.num_leaves,
        min_child_samples=args.min_child_samples,
        subsample=args.subsample,
        colsample_bytree=args.colsample_bytree,
        reg_alpha=args.reg_alpha,
        reg_lambda=args.reg_lambda,
        random_state=args.random_state,
    )
    all_predictions = pd.concat([baseline_predictions, lightgbm_predictions], ignore_index=True)
    all_predictions = all_predictions.dropna(
        subset=["prediction", "target_price_t_plus_7"]
    ).reset_index(drop=True)

    summary = summarize_predictions(all_predictions, train)
    per_market = pd.concat(
        [
            per_market_metrics(all_predictions, split_name, model_name, train)
            for split_name in ["validation", "test"]
            for model_name in sorted(all_predictions["model"].unique())
        ],
        ignore_index=True,
    )

    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    predictions_path.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(metrics_path, index=False)
    all_predictions.to_csv(predictions_path, index=False)
    write_report(
        report_path=report_path,
        feature_path=feature_path,
        metrics_path=metrics_path,
        prediction_path=predictions_path,
        row_filter=args.row_filter,
        train=train,
        validation=validation,
        test=test,
        summary=summary,
        per_market=per_market,
    )

    print(f"Wrote metrics CSV: {metrics_path}")
    print(f"Wrote predictions CSV: {predictions_path}")
    print(f"Wrote report: {report_path}")
    print(summary.sort_values(["split", "mae"]).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
