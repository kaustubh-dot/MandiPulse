from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from mandipulse.data.loaders import resolve_or_sample, running_on_sample  # noqa: E402
from mandipulse.data.store import read_csv_via_duckdb  # noqa: E402
from mandipulse.paths import (  # noqa: E402
    clean_panel_path,
    feature_table_path,
    forecast_outputs_path,
    recommendation_backtest_path,
    recommendation_outputs_path,
    reports_modeling_dir,
)

# Re-export running_on_sample() so Home can call RUNNING_ON_SAMPLE() from this module.
# The flag lives in loaders.py (shared with the API); data_access just re-exports it.
RUNNING_ON_SAMPLE = running_on_sample


def _resolve_or_sample(full_path: Path, sample_name: str) -> Path:
    path, _ = resolve_or_sample(full_path, sample_name)
    return path


def _missing_artifact_error(path: Path) -> None:
    st.error(
        f"**Artifact missing:** `{path}`\n\n"
        "Run the pipeline first:\n"
        "```\n"
        "python scripts/build_clean_onion_panel.py\n"
        "python scripts/build_feature_table.py\n"
        "python scripts/train_baselines_7d.py\n"
        "python scripts/train_lightgbm_7d.py\n"
        "python scripts/build_forecast_intervals_7d.py\n"
        "python scripts/build_recommendations_7d.py\n"
        "```"
    )
    st.stop()


@st.cache_data(show_spinner=False)
def load_clean_panel() -> pd.DataFrame:
    path = _resolve_or_sample(clean_panel_path(), "clean_mandi_prices.csv")
    if not path.exists():
        _missing_artifact_error(path)
    return read_csv_via_duckdb(path, parse_dates=["date"])


@st.cache_data(show_spinner=False)
def load_feature_table() -> pd.DataFrame:
    path = _resolve_or_sample(feature_table_path(), "feature_table_7d.csv")
    if not path.exists():
        _missing_artifact_error(path)
    return read_csv_via_duckdb(path, parse_dates=["date"])


@st.cache_data(show_spinner=False)
def load_forecasts() -> pd.DataFrame:
    path = _resolve_or_sample(forecast_outputs_path(), "forecast_outputs_7d.csv")
    if not path.exists():
        _missing_artifact_error(path)
    return read_csv_via_duckdb(path)


@st.cache_data(show_spinner=False)
def load_recommendations() -> pd.DataFrame:
    path = recommendation_outputs_path()
    if not path.exists():
        _missing_artifact_error(path)
    return read_csv_via_duckdb(path)


@st.cache_data(show_spinner=False)
def load_mandi_metadata() -> pd.DataFrame:
    from mandipulse.paths import mvp_mandis_path

    return read_csv_via_duckdb(mvp_mandis_path())


@st.cache_data(show_spinner=False)
def load_recommendation_backtest() -> pd.DataFrame | None:
    """Load the backtest artifact, or return None if it has not been generated yet.

    Unlike the mandatory artifacts, the backtest is optional context — a missing
    file must NOT stop the page. Return None and let the caller show guidance.
    Falls back to the demo sample when the full artifact is absent.
    """
    path = _resolve_or_sample(recommendation_backtest_path(), "recommendation_backtest_7d.csv")
    if not path.exists():
        return None
    return read_csv_via_duckdb(path)


@st.cache_data(show_spinner=False)
def load_report_markdown(name: str) -> str:
    path = reports_modeling_dir() / name
    if not path.exists():
        return f"*Report not found: `{path}`*"
    return path.read_text(encoding="utf-8")


def available_mandis(forecasts: pd.DataFrame) -> list[str]:
    return sorted(forecasts["mandi"].unique().tolist())


def history_for_mandi(panel: pd.DataFrame, market_id: int) -> pd.DataFrame:
    return panel[panel["market_id"] == market_id].sort_values("date").reset_index(drop=True)


def add_staleness_days(forecasts: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of forecasts with a staleness_days column.

    staleness_days = max(as_of_date) - as_of_date in integer days.
    The freshest mandi gets 0; older mandis get a positive integer.
    as_of_date is parsed robustly from string or datetime.
    """
    df = forecasts.copy()
    dates = pd.to_datetime(df["as_of_date"])
    max_date = dates.max()
    df["staleness_days"] = (max_date - dates).dt.days
    return df
