from __future__ import annotations

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
ROW_FILTER_CHOICES = ("all", "observed_only")
