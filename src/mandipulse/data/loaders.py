from __future__ import annotations

from pathlib import Path

import pandas as pd

from mandipulse.config import PROJECT_ROOT
from mandipulse.data.store import read_csv_via_duckdb
from mandipulse.paths import (
    clean_panel_path,
    feature_table_path,
    forecast_outputs_path,
    mvp_mandis_path,
    recommendation_backtest_path,
)

SAMPLE_DIR: Path = PROJECT_ROOT / "data" / "sample"

# Module-level flag set True when any loader fell back to the demo bundle.
# Streamlit Home reads this via data_access.RUNNING_ON_SAMPLE (re-exported).
_running_on_sample: bool = False


def running_on_sample() -> bool:
    return _running_on_sample


def resolve_or_sample(full_path: Path, sample_name: str) -> tuple[Path, bool]:
    """Return (path_to_use, used_sample).

    Prefers full_path when it exists; falls back to SAMPLE_DIR/sample_name.
    If neither exists, returns (full_path, False) so callers' exists()-guards fire.
    """
    if full_path.exists():
        return full_path, False
    sample = SAMPLE_DIR / sample_name
    if sample.exists():
        global _running_on_sample
        _running_on_sample = True
        return sample, True
    return full_path, False


def read_forecasts() -> pd.DataFrame:
    path, _ = resolve_or_sample(forecast_outputs_path(), "forecast_outputs_7d.csv")
    return read_csv_via_duckdb(path)


def read_mandi_metadata() -> pd.DataFrame:
    return read_csv_via_duckdb(mvp_mandis_path())


def read_recommendation_backtest() -> pd.DataFrame | None:
    path, _ = resolve_or_sample(recommendation_backtest_path(), "recommendation_backtest_7d.csv")
    if not path.exists():
        return None
    return read_csv_via_duckdb(path)


def read_clean_panel() -> pd.DataFrame:
    path, _ = resolve_or_sample(clean_panel_path(), "clean_mandi_prices.csv")
    return read_csv_via_duckdb(path, parse_dates=["date"])


def read_feature_table() -> pd.DataFrame:
    path, _ = resolve_or_sample(feature_table_path(), "feature_table_7d.csv")
    return read_csv_via_duckdb(path, parse_dates=["date"])
