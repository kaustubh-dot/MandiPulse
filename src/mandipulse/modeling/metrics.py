from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error

from mandipulse.modeling.columns import (
    CURRENT_PRICE_COLUMN,
    DATE_COLUMN,
    MARKET_ID_COLUMN,
    MARKET_NAME_COLUMN,
    TARGET_COLUMN,
)


def smape(y_true: pd.Series | np.ndarray, y_pred: pd.Series | np.ndarray) -> float:
    y_true_array = np.asarray(y_true, dtype=float)
    y_pred_array = np.asarray(y_pred, dtype=float)
    denominator = (np.abs(y_true_array) + np.abs(y_pred_array)) / 2
    valid = denominator > 0
    if not np.any(valid):
        return np.nan
    return float(
        np.mean(np.abs(y_true_array[valid] - y_pred_array[valid]) / denominator[valid]) * 100
    )


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


def summarize_predictions(predictions: pd.DataFrame, train: pd.DataFrame) -> pd.DataFrame:
    scale = mase_scale(train)
    rows = []
    for (model_name, split_name), group in predictions.groupby(["model", "split"]):
        rows.append(
            metric_row(model_name, split_name, group[TARGET_COLUMN], group["prediction"], scale)
        )
    summary = pd.DataFrame(rows)
    split_order = {"validation": 0, "test": 1}
    return summary.sort_values(
        by=["split", "mae"],
        key=lambda series: series.map(split_order) if series.name == "split" else series,
    ).reset_index(drop=True)
