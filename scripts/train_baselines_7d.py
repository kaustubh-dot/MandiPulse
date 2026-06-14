from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


TARGET_COLUMN = "target_price_t_plus_7"
CURRENT_PRICE_COLUMN = "modal_price_inr_qtl"
DATE_COLUMN = "date"
MARKET_ID_COLUMN = "market_id"
MARKET_NAME_COLUMN = "market_name"

NUMERIC_FEATURES = [
    CURRENT_PRICE_COLUMN,
    "price_lag_1",
    "price_lag_3",
    "price_lag_7",
    "price_lag_14",
    "price_lag_30",
    "rolling_mean_3",
    "rolling_mean_7",
    "rolling_mean_14",
    "rolling_mean_30",
    "rolling_median_3",
    "rolling_median_7",
    "rolling_median_14",
    "rolling_median_30",
    "rolling_std_3",
    "rolling_std_7",
    "rolling_std_14",
    "rolling_std_30",
    "return_1d",
    "return_7d",
    "day_of_week",
    "month",
    "day_of_year",
    "month_sin",
    "month_cos",
    "dow_sin",
    "dow_cos",
]
CATEGORICAL_FEATURES = ["market_id", "district_id"]


@dataclass(frozen=True)
class SplitConfig:
    validation_days: int
    test_days: int
    horizon_days: int


@dataclass(frozen=True)
class SplitDates:
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    validation_start: pd.Timestamp
    validation_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp


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
    return parser.parse_args()


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    columns = [str(column) for column in df.columns]
    rows = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for _, row in df.iterrows():
        rows.append("| " + " | ".join(str(row[column]) for column in df.columns) + " |")
    return "\n".join(rows)


def load_trainable_features(path: Path) -> pd.DataFrame:
    features = pd.read_csv(path)
    features[DATE_COLUMN] = pd.to_datetime(features[DATE_COLUMN])

    required_columns = {
        DATE_COLUMN,
        MARKET_ID_COLUMN,
        MARKET_NAME_COLUMN,
        CURRENT_PRICE_COLUMN,
        TARGET_COLUMN,
        "feature_row_valid",
        *NUMERIC_FEATURES,
        *CATEGORICAL_FEATURES,
    }
    missing = sorted(required_columns - set(features.columns))
    if missing:
        raise ValueError(f"Feature table is missing required columns: {missing}")

    trainable = features[features["feature_row_valid"].astype(bool)].copy()
    trainable = trainable.dropna(subset=[TARGET_COLUMN, CURRENT_PRICE_COLUMN])
    if trainable.empty:
        raise ValueError("No trainable rows found in feature table.")
    return trainable.sort_values([DATE_COLUMN, MARKET_ID_COLUMN]).reset_index(drop=True)


def make_temporal_splits(df: pd.DataFrame, config: SplitConfig) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, SplitDates]:
    max_date = df[DATE_COLUMN].max().normalize()
    test_start = max_date - pd.Timedelta(days=config.test_days - 1)
    validation_end = test_start - pd.Timedelta(days=1)
    validation_start = validation_end - pd.Timedelta(days=config.validation_days - 1)

    train_cutoff = validation_start - pd.Timedelta(days=config.horizon_days)

    train = df[df[DATE_COLUMN] < train_cutoff].copy()
    validation = df[(df[DATE_COLUMN] >= validation_start) & (df[DATE_COLUMN] <= validation_end)].copy()
    test = df[df[DATE_COLUMN] >= test_start].copy()

    if train.empty or validation.empty or test.empty:
        raise ValueError(
            "Temporal split produced an empty partition. "
            f"train={len(train)}, validation={len(validation)}, test={len(test)}"
        )

    split_dates = SplitDates(
        train_start=train[DATE_COLUMN].min(),
        train_end=train[DATE_COLUMN].max(),
        validation_start=validation[DATE_COLUMN].min(),
        validation_end=validation[DATE_COLUMN].max(),
        test_start=test[DATE_COLUMN].min(),
        test_end=test[DATE_COLUMN].max(),
    )
    return train, validation, test, split_dates


def smape(y_true: pd.Series | np.ndarray, y_pred: pd.Series | np.ndarray) -> float:
    y_true_array = np.asarray(y_true, dtype=float)
    y_pred_array = np.asarray(y_pred, dtype=float)
    denominator = (np.abs(y_true_array) + np.abs(y_pred_array)) / 2
    valid = denominator > 0
    if not np.any(valid):
        return np.nan
    return float(np.mean(np.abs(y_true_array[valid] - y_pred_array[valid]) / denominator[valid]) * 100)


def mase_scale(train: pd.DataFrame) -> float:
    diffs: list[pd.Series] = []
    for _, group in train.sort_values(DATE_COLUMN).groupby(MARKET_ID_COLUMN):
        current = group[CURRENT_PRICE_COLUMN]
        seasonal_diff = (current - current.shift(7)).abs().dropna()
        if not seasonal_diff.empty:
            diffs.append(seasonal_diff)
    if not diffs:
        return np.nan
    scale = pd.concat(diffs).mean()
    return float(scale) if scale > 0 else np.nan


def metric_row(
    model_name: str,
    split_name: str,
    y_true: pd.Series,
    y_pred: pd.Series,
    scale: float,
) -> dict[str, object]:
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    return {
        "model": model_name,
        "split": split_name,
        "rows": len(y_true),
        "mae": round(float(mae), 2),
        "rmse": round(float(rmse), 2),
        "smape_pct": round(smape(y_true, y_pred), 2),
        "mase": round(float(mae / scale), 3) if scale and not np.isnan(scale) else np.nan,
    }


def per_market_metrics(
    predictions: pd.DataFrame,
    split_name: str,
    model_name: str,
    train: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    split_predictions = predictions[
        (predictions["split"] == split_name) & (predictions["model"] == model_name)
    ]
    for market_id, group in split_predictions.groupby(MARKET_ID_COLUMN):
        market_train = train[train[MARKET_ID_COLUMN] == market_id]
        scale = mase_scale(market_train)
        rows.append(
            {
                **metric_row(
                    model_name=model_name,
                    split_name=split_name,
                    y_true=group[TARGET_COLUMN],
                    y_pred=group["prediction"],
                    scale=scale,
                ),
                MARKET_ID_COLUMN: market_id,
                MARKET_NAME_COLUMN: group[MARKET_NAME_COLUMN].iloc[0],
            }
        )
    return pd.DataFrame(rows)


def build_ridge_pipeline(alpha: float) -> Pipeline:
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, NUMERIC_FEATURES),
            ("cat", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )
    return Pipeline(steps=[("preprocessor", preprocessor), ("model", Ridge(alpha=alpha))])


def predict_baselines(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    test: pd.DataFrame,
    ridge_alpha: float,
) -> pd.DataFrame:
    ridge = build_ridge_pipeline(ridge_alpha)
    ridge.fit(train[NUMERIC_FEATURES + CATEGORICAL_FEATURES], train[TARGET_COLUMN])

    frames = []
    baseline_specs = [
        ("seasonal_naive_7d", CURRENT_PRICE_COLUMN),
        ("moving_average_7d", "rolling_mean_7"),
        ("moving_average_30d", "rolling_mean_30"),
    ]

    for split_name, split_df in [("validation", validation), ("test", test)]:
        base_columns = [
            DATE_COLUMN,
            MARKET_ID_COLUMN,
            MARKET_NAME_COLUMN,
            "mandi_id",
            "district",
            TARGET_COLUMN,
        ]
        for model_name, prediction_column in baseline_specs:
            frame = split_df[base_columns].copy()
            frame["split"] = split_name
            frame["model"] = model_name
            frame["prediction"] = split_df[prediction_column].astype(float).to_numpy()
            frames.append(frame)

        ridge_frame = split_df[base_columns].copy()
        ridge_frame["split"] = split_name
        ridge_frame["model"] = "ridge"
        ridge_frame["prediction"] = ridge.predict(split_df[NUMERIC_FEATURES + CATEGORICAL_FEATURES])
        frames.append(ridge_frame)

    predictions = pd.concat(frames, ignore_index=True)
    predictions = predictions.dropna(subset=["prediction", TARGET_COLUMN])
    return predictions


def summarize_predictions(predictions: pd.DataFrame, train: pd.DataFrame) -> pd.DataFrame:
    scale = mase_scale(train)
    rows = []
    for (model_name, split_name), group in predictions.groupby(["model", "split"]):
        rows.append(metric_row(model_name, split_name, group[TARGET_COLUMN], group["prediction"], scale))
    summary = pd.DataFrame(rows)
    split_order = {"validation": 0, "test": 1}
    return summary.sort_values(
        by=["split", "mae"],
        key=lambda series: series.map(split_order) if series.name == "split" else series,
    ).reset_index(drop=True)


def write_report(
    report_path: Path,
    feature_path: Path,
    prediction_path: Path,
    split_dates: SplitDates,
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
        .loc[:, [MARKET_ID_COLUMN, MARKET_NAME_COLUMN, "rows", "mae", "rmse", "smape_pct", "mase"]]
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
        "- `seasonal_naive_7d`: predicts the 7-day-ahead price as the current as-of date modal price. "
        "This is an explicit naive benchmark, not a feature used by Ridge.",
        "- `moving_average_7d`: predicts using the 7-day rolling mean available on the as-of date, "
        "including the current-day modal price.",
        "- `moving_average_30d`: predicts using the 30-day rolling mean available on the as-of date, "
        "including the current-day modal price.",
        "- `ridge`: linear baseline using lag, rolling, return, calendar, market, and district features. "
        "It includes current-day modal price because that value is known on the as-of date. "
        "It excludes future target columns.",
        "",
        "## Metric Notes",
        "",
        "- MAE/RMSE are INR per quintal.",
        "- sMAPE is percentage error.",
        "- MASE is scaled by the average absolute 7-day seasonal difference in the training period.",
        "- Splits are date-based only; no random split is used.",
        "- The training split is purged by the forecast horizon so no training target resolves "
        "inside the validation window.",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    feature_path = Path(args.features)
    report_path = Path(args.report)
    prediction_path = Path(args.predictions)

    trainable = load_trainable_features(feature_path)
    train, validation, test, split_dates = make_temporal_splits(
        trainable,
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
        train=train,
        validation=validation,
        test=test,
        summary=summary,
        per_market=per_market,
    )

    print(f"Wrote predictions: {prediction_path}")
    print(f"Wrote report: {report_path}")
    print(summary.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
