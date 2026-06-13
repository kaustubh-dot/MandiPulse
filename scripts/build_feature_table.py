from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    columns = [str(column) for column in df.columns]
    rows = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for _, row in df.iterrows():
        rows.append("| " + " | ".join(str(row[column]) for column in df.columns) + " |")
    return "\n".join(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build 7-day Onion/Maharashtra feature table.")
    parser.add_argument(
        "--clean-input",
        default="data/processed/onion_maharashtra/clean_mandi_prices.csv",
    )
    parser.add_argument(
        "--output",
        default="data/processed/onion_maharashtra/feature_table_7d.csv",
    )
    parser.add_argument(
        "--report",
        default="reports/data_quality/onion_maharashtra_feature_table.md",
    )
    parser.add_argument("--horizon-days", type=int, default=7)
    return parser.parse_args()


def add_group_features(group: pd.DataFrame, horizon_days: int) -> pd.DataFrame:
    group = group.sort_values("date").copy()
    price = group["modal_price_inr_qtl"]

    for lag in [1, 3, 7, 14, 30]:
        group[f"price_lag_{lag}"] = price.shift(lag)
        group[f"observed_lag_{lag}"] = (
            group["is_observed"].astype("boolean").shift(lag).fillna(False).astype(bool)
        )
        group[f"imputed_lag_{lag}"] = (
            group["is_imputed"].astype("boolean").shift(lag).fillna(False).astype(bool)
        )

    shifted_price = price.shift(1)
    for window in [3, 7, 14, 30]:
        group[f"rolling_mean_{window}"] = shifted_price.rolling(window, min_periods=window).mean()
        group[f"rolling_median_{window}"] = (
            shifted_price.rolling(window, min_periods=window).median()
        )
        group[f"rolling_std_{window}"] = shifted_price.rolling(window, min_periods=window).std()

    group["return_1d"] = price.pct_change(1, fill_method=None).shift(1)
    group["return_7d"] = price.pct_change(7, fill_method=None).shift(1)
    group["target_price_t_plus_7"] = price.shift(-horizon_days)
    group["target_available"] = group["target_price_t_plus_7"].notna()
    return group


def build_features(clean: pd.DataFrame, horizon_days: int) -> pd.DataFrame:
    clean = clean.copy()
    clean["date"] = pd.to_datetime(clean["date"])
    clean = clean.sort_values(["market_id", "date"])

    feature_frames = [
        add_group_features(group, horizon_days)
        for _, group in clean.groupby("market_id", sort=False)
    ]
    features = pd.concat(feature_frames, ignore_index=True)

    features["day_of_week"] = features["date"].dt.dayofweek
    features["month"] = features["date"].dt.month
    features["day_of_year"] = features["date"].dt.dayofyear
    features["month_sin"] = np.sin(2 * np.pi * features["month"] / 12)
    features["month_cos"] = np.cos(2 * np.pi * features["month"] / 12)
    features["dow_sin"] = np.sin(2 * np.pi * features["day_of_week"] / 7)
    features["dow_cos"] = np.cos(2 * np.pi * features["day_of_week"] / 7)

    required_feature_columns = [
        "price_lag_1",
        "price_lag_3",
        "price_lag_7",
        "price_lag_14",
        "price_lag_30",
        "rolling_mean_7",
        "rolling_mean_14",
        "rolling_mean_30",
        "rolling_std_7",
        "rolling_std_14",
        "rolling_std_30",
        "return_1d",
        "return_7d",
    ]
    features["feature_row_valid"] = (
        features[required_feature_columns].notna().all(axis=1)
        & features["target_available"]
        & features["modal_price_inr_qtl"].notna()
    )
    return features


def write_report(features: pd.DataFrame, report_path: Path) -> None:
    trainable = features[features["feature_row_valid"]].copy()
    by_market = (
        features.groupby(["market_id", "market_name"], dropna=False)
        .agg(
            panel_rows=("date", "size"),
            trainable_rows=("feature_row_valid", "sum"),
            first_date=("date", "min"),
            last_date=("date", "max"),
        )
        .reset_index()
    )
    by_market["trainable_pct"] = (
        by_market["trainable_rows"] / by_market["panel_rows"] * 100
    ).round(2)
    by_market = by_market.sort_values("trainable_rows", ascending=False)

    lines = [
        "# Onion/Maharashtra 7-Day Feature Table",
        "",
        "## Summary",
        "",
        f"- Panel rows: {len(features):,}",
        f"- Trainable rows: {len(trainable):,}",
        f"- Markets: {features['market_id'].nunique():,}",
        f"- Date range: {features['date'].min().date()} to {features['date'].max().date()}",
        "- Target: `target_price_t_plus_7`",
        "- Leakage rule: lag and rolling features are shifted; rolling windows exclude "
        "current row.",
        "",
        "## Trainable Rows By Market",
        "",
        dataframe_to_markdown(by_market),
        "",
        "## Notes",
        "",
        "- Rows with missing lag/rolling features or missing target are not trainable.",
        "- Current-day modal price is retained for diagnostics but should not be used as "
        "a model feature.",
        "- Use `feature_row_valid == True` for baseline/model training.",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    clean = pd.read_csv(args.clean_input)
    features = build_features(clean, args.horizon_days)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    features.to_csv(output_path, index=False)

    report_path = Path(args.report)
    write_report(features, report_path)

    trainable_rows = int(features["feature_row_valid"].sum())
    print(f"Wrote feature table: {output_path}")
    print(f"Wrote report: {report_path}")
    print(f"panel_rows: {len(features)}")
    print(f"trainable_rows: {trainable_rows}")
    print(f"market_count: {features['market_id'].nunique()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
