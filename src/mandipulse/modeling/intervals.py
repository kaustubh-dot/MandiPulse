from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pandas as pd

from mandipulse.modeling.columns import (
    CURRENT_PRICE_COLUMN,
    DATE_COLUMN,
    MARKET_ID_COLUMN,
    MARKET_NAME_COLUMN,
    TARGET_COLUMN,
)

REQUIRED_FORECAST_COLUMNS = [
    CURRENT_PRICE_COLUMN,
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

# Minimum columns required per model for latest-forecast eligibility.
# Rows lacking these are excluded from the forecast output.
_MODEL_REQUIRED_COLUMNS: dict[str, list[str]] = {
    "seasonal_naive_7d": [CURRENT_PRICE_COLUMN],
    "moving_average_7d": ["rolling_mean_7"],
    "moving_average_30d": ["rolling_mean_30"],
}


def latest_forecastable_rows(
    features: pd.DataFrame,
    model_name: str | None = None,
) -> pd.DataFrame:
    check_cols = (
        _MODEL_REQUIRED_COLUMNS.get(model_name) if model_name else REQUIRED_FORECAST_COLUMNS
    )
    if check_cols is None:
        check_cols = REQUIRED_FORECAST_COLUMNS
    forecastable = features[features[check_cols].notna().all(axis=1)].copy()
    forecastable = forecastable.dropna(
        subset=[DATE_COLUMN, MARKET_ID_COLUMN, MARKET_NAME_COLUMN, CURRENT_PRICE_COLUMN]
    )
    latest = (
        forecastable.sort_values([MARKET_ID_COLUMN, DATE_COLUMN])
        .groupby(MARKET_ID_COLUMN, as_index=False)
        .tail(1)
        .sort_values([DATE_COLUMN, MARKET_ID_COLUMN])
        .reset_index(drop=True)
    )
    if latest.empty:
        raise ValueError("No forecastable rows found for latest forecast output.")
    return latest


def compute_interval_residuals(
    predictions: pd.DataFrame,
    model_name: str,
    confidence_level: float,
) -> tuple[float, float]:
    alpha = 1.0 - confidence_level
    validation = predictions[
        (predictions["split"] == "validation") & (predictions["model"] == model_name)
    ].copy()
    if validation.empty:
        raise ValueError(f"No validation predictions found for model '{model_name}'.")
    residuals = validation[TARGET_COLUMN] - validation["prediction"]
    lower_residual = float(residuals.quantile(alpha / 2))
    upper_residual = float(residuals.quantile(1 - alpha / 2))
    return lower_residual, upper_residual


def build_backtest(
    predictions: pd.DataFrame,
    model_name: str,
    lower_residual: float,
    upper_residual: float,
    confidence_level: float,
) -> pd.DataFrame:
    selected = predictions[predictions["model"] == model_name].copy()
    selected["lower_bound_inr_qtl"] = selected["prediction"] + lower_residual
    selected["upper_bound_inr_qtl"] = selected["prediction"] + upper_residual
    selected["covered"] = (selected[TARGET_COLUMN] >= selected["lower_bound_inr_qtl"]) & (
        selected[TARGET_COLUMN] <= selected["upper_bound_inr_qtl"]
    )
    selected["interval_width_inr_qtl"] = (
        selected["upper_bound_inr_qtl"] - selected["lower_bound_inr_qtl"]
    )
    selected["confidence_level"] = confidence_level
    return selected.reset_index(drop=True)


def summarize_backtest(backtest: pd.DataFrame) -> pd.DataFrame:
    _COVERAGE_LABEL = {
        "validation": "coverage (in-sample calibration)",
        "test": "coverage (out-of-sample)",
    }
    rows = []
    for split_name, group in backtest.groupby("split"):
        rows.append(
            {
                "split": split_name,
                "coverage_type": _COVERAGE_LABEL.get(split_name, split_name),
                "rows": len(group),
                "empirical_coverage": round(float(group["covered"].mean()), 4),
                "avg_interval_width_inr_qtl": round(
                    float(group["interval_width_inr_qtl"].mean()), 2
                ),
                "median_interval_width_inr_qtl": round(
                    float(group["interval_width_inr_qtl"].median()), 2
                ),
            }
        )
    return pd.DataFrame(rows).sort_values("split").reset_index(drop=True)


def build_latest_forecast_output(
    latest_rows: pd.DataFrame,
    model_name: str,
    lower_residual: float,
    upper_residual: float,
    confidence_level: float,
) -> pd.DataFrame:
    prediction_column_map = {
        "seasonal_naive_7d": CURRENT_PRICE_COLUMN,
        "moving_average_7d": "rolling_mean_7",
        "moving_average_30d": "rolling_mean_30",
    }
    if model_name not in prediction_column_map:
        raise ValueError(
            f"Latest forecast output does not support model '{model_name}'. "
            f"Supported: {sorted(prediction_column_map)}."
        )
    prediction_column = prediction_column_map[model_name]
    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat()

    forecasts = latest_rows.copy()
    forecasts["forecast_price_inr_qtl"] = forecasts[prediction_column].astype(float)
    forecasts["lower_bound_inr_qtl"] = forecasts["forecast_price_inr_qtl"] + lower_residual
    forecasts["upper_bound_inr_qtl"] = forecasts["forecast_price_inr_qtl"] + upper_residual
    forecasts["forecast_id"] = [str(uuid.uuid4()) for _ in range(len(forecasts))]
    forecasts["generated_at"] = generated_at
    forecasts["as_of_date"] = forecasts[DATE_COLUMN].dt.date.astype(str)
    forecasts["crop"] = forecasts["crop"].fillna("onion")
    forecasts["crop_id"] = forecasts["crop_id"].fillna("onion")
    forecasts["state"] = forecasts["state"].fillna("maharashtra")
    forecasts["mandi"] = forecasts[MARKET_NAME_COLUMN]
    forecasts["horizon_days"] = 7
    forecasts["confidence_level"] = confidence_level
    forecasts["model_name"] = model_name
    forecasts["model_version"] = f"{model_name}_residual_interval_v1"

    output_columns = [
        "forecast_id",
        "generated_at",
        "as_of_date",
        "crop",
        "crop_id",
        "state",
        "mandi",
        "mandi_id",
        MARKET_ID_COLUMN,
        "horizon_days",
        "forecast_price_inr_qtl",
        "lower_bound_inr_qtl",
        "upper_bound_inr_qtl",
        "confidence_level",
        "model_name",
        "model_version",
    ]
    return forecasts[output_columns].sort_values("mandi_id").reset_index(drop=True)
