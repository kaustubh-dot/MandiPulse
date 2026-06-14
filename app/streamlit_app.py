from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st  # noqa: E402

st.set_page_config(
    page_title="MandiPulse India",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("MandiPulse India — Onion / Maharashtra")
st.caption(
    "Transport-cost-aware 7-day mandi decision intelligence · "
    "Data: CEDA/AGMARKNET · As-of date: **2025-10-30** (offline showcase)"
)

st.info(
    "**Offline Demo Mode** — all forecasts and recommendations are computed from cached data "
    "(Oct 2025). No live API key is required. Use the sidebar to navigate between pages.",
    icon="ℹ️",
)

st.markdown("### How to use")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("**1 · Data Coverage**\n\nVerify the dataset quality before trusting forecasts.")
with col2:
    st.markdown(
        "**2 · Forecast**\n\nSelect a mandi and review its 7-day price forecast with uncertainty bounds."
    )
with col3:
    st.markdown(
        "**3 · Recommendation**\n\nEnter your farm location to rank mandis by net price after transport cost."
    )
