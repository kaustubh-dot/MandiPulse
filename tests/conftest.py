from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

GOLDEN_DIR = Path(__file__).parent / "golden"


@pytest.fixture()
def golden_clean_panel() -> pd.DataFrame:
    df = pd.read_csv(GOLDEN_DIR / "clean_mandi_prices.csv")
    df["date"] = pd.to_datetime(df["date"])
    return df


@pytest.fixture()
def golden_feature_table() -> pd.DataFrame:
    df = pd.read_csv(GOLDEN_DIR / "feature_table_7d.csv")
    df["date"] = pd.to_datetime(df["date"])
    return df


@pytest.fixture()
def golden_forecasts() -> pd.DataFrame:
    return pd.read_csv(GOLDEN_DIR / "forecast_outputs_7d.csv")


@pytest.fixture()
def golden_recommendations() -> pd.DataFrame:
    return pd.read_csv(GOLDEN_DIR / "recommendation_outputs_7d.csv")


def _make_mandi_panel(market_id: int, market_name: str, n_days: int = 80) -> pd.DataFrame:
    rng = np.random.default_rng(seed=market_id)
    dates = pd.date_range("2022-01-01", periods=n_days, freq="D")
    price = 1000.0 + rng.normal(0, 50, size=n_days).cumsum()
    price = np.clip(price, 200, 5000)
    rows = []
    for i, (d, p) in enumerate(zip(dates, price)):
        rows.append(
            {
                "date": d,
                "market_id": market_id,
                "market_name": market_name,
                "mandi_id": f"mh__{market_name.lower()}",
                "district_id": 100 + market_id,
                "district": "test_district",
                "state": "maharashtra",
                "crop": "onion",
                "crop_id": "onion",
                "modal_price_inr_qtl": round(p, 2),
                "is_observed": True,
                "is_imputed": False,
                "feature_row_valid": i >= 30,
                "target_price_t_plus_7": round(price[min(i + 7, n_days - 1)], 2),
                "target_available": True,
                "target_observed_t_plus_7": True,
                "target_imputed_t_plus_7": False,
                "price_lag_1": round(price[max(i - 1, 0)], 2) if i >= 1 else np.nan,
                "price_lag_3": round(price[max(i - 3, 0)], 2) if i >= 3 else np.nan,
                "price_lag_7": round(price[max(i - 7, 0)], 2) if i >= 7 else np.nan,
                "price_lag_14": round(price[max(i - 14, 0)], 2) if i >= 14 else np.nan,
                "price_lag_30": round(price[max(i - 30, 0)], 2) if i >= 30 else np.nan,
                "rolling_mean_3": round(float(np.mean(price[max(i - 2, 0) : i + 1])), 2),
                "rolling_median_3": round(float(np.median(price[max(i - 2, 0) : i + 1])), 2),
                "rolling_std_3": round(float(np.std(price[max(i - 2, 0) : i + 1])), 2),
                "rolling_mean_7": round(float(np.mean(price[max(i - 6, 0) : i + 1])), 2),
                "rolling_median_7": round(float(np.median(price[max(i - 6, 0) : i + 1])), 2),
                "rolling_std_7": round(float(np.std(price[max(i - 6, 0) : i + 1])), 2),
                "rolling_mean_14": round(float(np.mean(price[max(i - 13, 0) : i + 1])), 2),
                "rolling_median_14": round(float(np.median(price[max(i - 13, 0) : i + 1])), 2),
                "rolling_std_14": round(float(np.std(price[max(i - 13, 0) : i + 1])), 2),
                "rolling_mean_30": round(float(np.mean(price[max(i - 29, 0) : i + 1])), 2),
                "rolling_median_30": round(float(np.median(price[max(i - 29, 0) : i + 1])), 2),
                "rolling_std_30": round(float(np.std(price[max(i - 29, 0) : i + 1])), 2),
                "return_1d": (
                    round((p - price[max(i - 1, 0)]) / price[max(i - 1, 0)], 4)
                    if i >= 1
                    else np.nan
                ),
                "return_7d": (
                    round((p - price[max(i - 7, 0)]) / price[max(i - 7, 0)], 4)
                    if i >= 7
                    else np.nan
                ),
                "day_of_week": d.dayofweek,
                "month": d.month,
                "day_of_year": d.day_of_year,
                "month_sin": round(np.sin(2 * np.pi * d.month / 12), 6),
                "month_cos": round(np.cos(2 * np.pi * d.month / 12), 6),
                "dow_sin": round(np.sin(2 * np.pi * d.dayofweek / 7), 6),
                "dow_cos": round(np.cos(2 * np.pi * d.dayofweek / 7), 6),
            }
        )
    return pd.DataFrame(rows)


@pytest.fixture()
def synthetic_features() -> pd.DataFrame:
    """Three-mandi leakage-safe feature table for split/metric tests."""
    frames = [
        _make_mandi_panel(1, "MandiA", n_days=80),
        _make_mandi_panel(2, "MandiB", n_days=80),
        _make_mandi_panel(3, "MandiC", n_days=80),
    ]
    return (
        pd.concat(frames, ignore_index=True)
        .sort_values(["date", "market_id"])
        .reset_index(drop=True)
    )
