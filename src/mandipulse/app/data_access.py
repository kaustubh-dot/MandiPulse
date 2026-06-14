from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from mandipulse.paths import (  # noqa: E402
    clean_panel_path,
    feature_table_path,
    forecast_outputs_path,
    mvp_mandis_path,
    recommendation_outputs_path,
    reports_modeling_dir,
)


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
    path = clean_panel_path()
    if not path.exists():
        _missing_artifact_error(path)
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df


@st.cache_data(show_spinner=False)
def load_feature_table() -> pd.DataFrame:
    path = feature_table_path()
    if not path.exists():
        _missing_artifact_error(path)
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df


@st.cache_data(show_spinner=False)
def load_forecasts() -> pd.DataFrame:
    path = forecast_outputs_path()
    if not path.exists():
        _missing_artifact_error(path)
    return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def load_recommendations() -> pd.DataFrame:
    path = recommendation_outputs_path()
    if not path.exists():
        _missing_artifact_error(path)
    return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def load_mandi_metadata() -> pd.DataFrame:
    return pd.read_csv(mvp_mandis_path())


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
