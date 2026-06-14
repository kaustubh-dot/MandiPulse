from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st  # noqa: E402

from mandipulse.app.data_access import add_staleness_days, load_forecasts  # noqa: E402

st.set_page_config(
    page_title="MandiPulse India",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("MandiPulse India — Onion / Maharashtra")

try:
    _forecasts_with_staleness = add_staleness_days(load_forecasts())
    _max_as_of = _forecasts_with_staleness["as_of_date"].max()
    _n_stale = int((_forecasts_with_staleness["staleness_days"] > 0).sum())
    _staleness_note = (
        " · some mandis older — see Forecast/Recommendation pages" if _n_stale > 0 else ""
    )
    _as_of_label = f"**{_max_as_of}**{_staleness_note}"
except Exception:
    _as_of_label = "unavailable (run the pipeline first)"

st.caption(
    "Transport-cost-aware 7-day mandi decision intelligence · "
    f"Data: CEDA/AGMARKNET · Latest as-of date: {_as_of_label} (offline showcase)"
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
