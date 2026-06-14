from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mandipulse.modeling.baselines import predict_baselines  # noqa: E402
from mandipulse.modeling.metrics import summarize_predictions  # noqa: E402
from mandipulse.modeling.splits import (  # noqa: E402
    SplitConfig,
    apply_row_filter,
    load_trainable_features,
    make_temporal_splits,
)
from mandipulse.utils.formatting import dataframe_to_markdown  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run observed-only sensitivity checks for 7-day Onion/Maharashtra baselines."
    )
    parser.add_argument(
        "--features",
        default="data/processed/onion_maharashtra/feature_table_7d.csv",
    )
    parser.add_argument(
        "--report",
        default="reports/modeling/baseline_sensitivity_7d.md",
    )
    parser.add_argument(
        "--summary-csv",
        default="artifacts/metrics/baseline_sensitivity_7d.csv",
    )
    parser.add_argument(
        "--predictions-csv",
        default="artifacts/predictions/baseline_sensitivity_predictions_7d.csv",
    )
    parser.add_argument("--validation-days", type=int, default=90)
    parser.add_argument("--test-days", type=int, default=90)
    parser.add_argument("--horizon-days", type=int, default=7)
    parser.add_argument("--ridge-alpha", type=float, default=1.0)
    return parser.parse_args()


def write_report(
    report_path: Path,
    feature_path: Path,
    summary_all: pd.DataFrame,
    summary_observed: pd.DataFrame,
) -> None:
    lines = [
        "# Onion/Maharashtra 7-Day Baseline Sensitivity (Observed-Only vs All)",
        "",
        "## Summary",
        "",
        f"- Feature table: `{feature_path}`",
        "",
        "## All rows (imputed + observed)",
        "",
        dataframe_to_markdown(summary_all.sort_values(["split", "mae"]).reset_index(drop=True)),
        "",
        "## Observed-only rows",
        "",
        dataframe_to_markdown(
            summary_observed.sort_values(["split", "mae"]).reset_index(drop=True)
        ),
        "",
        "## Notes",
        "",
        "- If observed-only MAE differs substantially from all-rows MAE, imputation is affecting scores.",
        "- This check isolates the forward-fill from modeling quality.",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    feature_path = Path(args.features)
    report_path = Path(args.report)
    summary_csv = Path(args.summary_csv)
    predictions_csv = Path(args.predictions_csv)

    split_cfg = SplitConfig(
        validation_days=args.validation_days,
        test_days=args.test_days,
        horizon_days=args.horizon_days,
    )

    trainable = load_trainable_features(feature_path)

    filtered_all = apply_row_filter(trainable, "all")
    train_all, val_all, test_all, _ = make_temporal_splits(filtered_all, split_cfg)
    preds_all = predict_baselines(train_all, val_all, test_all, ridge_alpha=args.ridge_alpha)
    summary_all = summarize_predictions(preds_all, train_all)

    filtered_obs = apply_row_filter(trainable, "observed_only")
    train_obs, val_obs, test_obs, _ = make_temporal_splits(filtered_obs, split_cfg)
    preds_obs = predict_baselines(train_obs, val_obs, test_obs, ridge_alpha=args.ridge_alpha)
    summary_obs = summarize_predictions(preds_obs, train_obs)

    summary_csv.parent.mkdir(parents=True, exist_ok=True)
    predictions_csv.parent.mkdir(parents=True, exist_ok=True)
    summary_all.to_csv(summary_csv, index=False)
    preds_all.to_csv(predictions_csv, index=False)
    write_report(report_path, feature_path, summary_all, summary_obs)

    print(f"Wrote summary CSV: {summary_csv}")
    print(f"Wrote predictions CSV: {predictions_csv}")
    print(f"Wrote report: {report_path}")
    print("\n--- All rows ---")
    print(summary_all.sort_values(["split", "mae"]).to_string(index=False))
    print("\n--- Observed only ---")
    print(summary_obs.sort_values(["split", "mae"]).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
