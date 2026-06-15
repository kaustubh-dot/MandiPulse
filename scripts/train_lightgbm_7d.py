from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mandipulse.modeling.baselines import predict_baselines  # noqa: E402
from mandipulse.modeling.columns import (  # noqa: E402
    CATEGORICAL_FEATURES,
    MARKET_ID_COLUMN,
    MARKET_NAME_COLUMN,
    NUMERIC_FEATURES,
    TARGET_COLUMN,
)
from mandipulse.modeling.lightgbm_model import (
    build_lightgbm_pipeline,
    predict_lightgbm,
    predict_lightgbm_residual,
)  # noqa: E402
from mandipulse.modeling.metrics import per_market_metrics, summarize_predictions  # noqa: E402
from mandipulse.modeling.persistence import save_feature_schema, save_model  # noqa: E402
from mandipulse.modeling.splits import (  # noqa: E402
    SplitConfig,
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
    parser.add_argument(
        "--model-path",
        default="artifacts/models/lightgbm_7d.joblib",
    )
    parser.add_argument(
        "--schema-path",
        default="artifacts/models/feature_schema_7d.json",
    )
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

    residual_rows = test_summary[test_summary["model"] == "lightgbm_residual"]
    residual_test = residual_rows.iloc[0] if not residual_rows.empty else None

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
        f"- LightGBM (level) test MAE: {lightgbm_test['mae']} INR/quintal",
        f"- Moving-average 7d test MAE: {moving_average_test['mae']} INR/quintal",
        f"- LightGBM (level) MAE delta vs moving_average_7d: {mae_delta} INR/quintal",
    ]

    if residual_test is not None:
        residual_delta = round(residual_test["mae"] - moving_average_test["mae"], 2)
        lines.append(
            f"- LightGBM (residual) test MAE: {residual_test['mae']} INR/quintal"
            f" (delta vs moving_average_7d: {residual_delta:+.2f} INR/quintal)"
        )

    lines += [
        "",
        "## Overall Metrics",
        "",
        dataframe_to_markdown(summary.sort_values(["split", "mae"]).reset_index(drop=True)),
        "",
        "## LightGBM (Level) Test Metrics By Mandi",
        "",
        dataframe_to_markdown(best_market_table),
        "",
        "## Decision: Residual-Target Reformulation (M3-04)",
        "",
    ]

    if residual_test is not None:
        residual_mae = float(residual_test["mae"])
        ma_mae = float(moving_average_test["mae"])
        residual_delta = round(residual_mae - ma_mae, 2)
        beats = residual_mae < ma_mae
        lines += [
            f"- Residual-LightGBM test MAE: **{residual_mae:.2f} INR/quintal**",
            f"- Moving-average baseline test MAE: **{ma_mae:.2f} INR/quintal**",
            f"- Delta: **{residual_delta:+.2f} INR/quintal** ({'residual wins' if beats else 'baseline wins'})",
            "",
        ]
        if beats:
            lines += [
                "**Promotion: YES.** The residual-target LightGBM beats the moving-average baseline "
                "on the held-out test split. It becomes the shipped forecaster.",
                "Downstream artifacts (forecast intervals, recommendations, backtest) are regenerated "
                "with `lightgbm_residual` predictions.",
            ]
        else:
            lines += [
                "**Promotion: NO.** The residual-target LightGBM does not beat the moving-average "
                "baseline on the held-out test split. The baseline remains the shipped forecaster.",
                "This is an honest outcome: a smaller residual-target variance reduces overfitting "
                "but the model has not found exploitable signal beyond the baseline.",
                "Next lever: richer exogenous features (arrivals, weather) or a different model family.",
            ]
    else:
        lines.append("*Residual model results not available in this run.*")

    lines += [
        "",
        "## Interview Note",
        "",
        "- Level-LightGBM (absolute target): overfits to training price levels; eats distribution shift on test.",
        "- Residual-LightGBM (target - rolling_mean_7): isolates what the baseline misses; can only add value where real signal exists.",
        "- See Decision section above for the promotion outcome of the residual experiment.",
        "- If neither model beats the baseline, the honest story remains strong: the baseline is tough, and the project reports that transparently.",
    ]

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    feature_path = Path(args.features)
    report_path = Path(args.report)
    metrics_path = Path(args.metrics_csv)
    predictions_path = Path(args.predictions_csv)
    model_path = Path(args.model_path)
    schema_path = Path(args.schema_path)

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
    lightgbm_residual_predictions = predict_lightgbm_residual(
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
    all_predictions = pd.concat(
        [baseline_predictions, lightgbm_predictions, lightgbm_residual_predictions],
        ignore_index=True,
    )
    all_predictions = all_predictions.dropna(subset=["prediction", TARGET_COLUMN]).reset_index(
        drop=True
    )

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

    # Save fitted model and feature schema
    lgbm_pipeline = build_lightgbm_pipeline(
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
    lgbm_pipeline.fit(train[NUMERIC_FEATURES + CATEGORICAL_FEATURES], train[TARGET_COLUMN])
    save_model(lgbm_pipeline, model_path)
    save_feature_schema(
        schema_path,
        numeric_features=NUMERIC_FEATURES,
        categorical_features=CATEGORICAL_FEATURES,
        target=TARGET_COLUMN,
        horizon_days=args.horizon_days,
    )

    # MLflow tracking
    lgbm_test = summary[(summary["split"] == "test") & (summary["model"] == "lightgbm")]
    lgbm_val = summary[(summary["split"] == "validation") & (summary["model"] == "lightgbm")]
    set_experiment("mandipulse_lightgbm_7d")
    with start_run(run_name="lightgbm_7d"):
        log_params(
            {
                "n_estimators": args.n_estimators,
                "learning_rate": args.learning_rate,
                "num_leaves": args.num_leaves,
                "min_child_samples": args.min_child_samples,
                "subsample": args.subsample,
                "colsample_bytree": args.colsample_bytree,
                "reg_alpha": args.reg_alpha,
                "reg_lambda": args.reg_lambda,
                "random_state": args.random_state,
                "row_filter": args.row_filter,
                "train_start": str(split_dates.train_start.date()),
                "train_end": str(split_dates.train_end.date()),
                "validation_start": str(split_dates.validation_start.date()),
                "validation_end": str(split_dates.validation_end.date()),
                "test_start": str(split_dates.test_start.date()),
                "test_end": str(split_dates.test_end.date()),
            }
        )
        if not lgbm_test.empty:
            row = lgbm_test.iloc[0]
            log_metrics(
                {
                    "test_mae": float(row["mae"]),
                    "test_rmse": float(row["rmse"]),
                    "test_smape_pct": float(row["smape_pct"]),
                    "test_mase": float(row["mase"]),
                }
            )
        if not lgbm_val.empty:
            row = lgbm_val.iloc[0]
            log_metrics(
                {
                    "val_mae": float(row["mae"]),
                    "val_rmse": float(row["rmse"]),
                    "val_smape_pct": float(row["smape_pct"]),
                    "val_mase": float(row["mase"]),
                }
            )
        log_artifact(report_path)
        log_artifact(metrics_path)

    print(f"Wrote metrics CSV: {metrics_path}")
    print(f"Wrote predictions CSV: {predictions_path}")
    print(f"Wrote report: {report_path}")
    print(f"Saved model: {model_path}")
    print(f"Saved schema: {schema_path}")
    print(summary.sort_values(["split", "mae"]).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
