from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st  # noqa: E402

from mandipulse.app.data_access import (
    RUNNING_ON_SAMPLE,
    add_staleness_days,
    load_forecasts,
)  # noqa: E402
from mandipulse.app.design import FROZEN_NOTICE, SNAPSHOT_LABEL, inject_base_css  # noqa: E402

st.set_page_config(
    page_title="MandiPulse — Onion Mandi Decision Intelligence",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Single shared stylesheet for the whole app (shell + all pages).
inject_base_css()

try:
    _forecasts_with_staleness = add_staleness_days(load_forecasts())
    _max_as_of = _forecasts_with_staleness["as_of_date"].max()
    _n_stale = int((_forecasts_with_staleness["staleness_days"] > 0).sum())
    _staleness_note = (
        " · some mandis older — see Forecast/Recommendation pages" if _n_stale > 0 else ""
    )
    _as_of_label = f"{_max_as_of}{_staleness_note}"
except Exception:
    _as_of_label = "unavailable (run the pipeline first)"

# Compact header: product wordmark, snapshot status, frozen-data notice.
# Navigation order is fixed by app/pages numbering: 1 Data Coverage, 2 Forecast,
# 3 Recommendation.
st.markdown(
    f"""
    <h1 class="mp-wordmark">MandiPulse</h1>
    <div class="mp-snapshot-label">
      {SNAPSHOT_LABEL} · onion / Maharashtra · latest pipeline as-of date: {_as_of_label}
    </div>
    <p class="mp-frozen-note">{FROZEN_NOTICE}</p>
    """,
    unsafe_allow_html=True,
)

_data_source_note = (
    "Running on bundled demo data (Oct 2025 snapshot, column-trimmed). "
    "Clone the repo and run the full pipeline to load all columns."
    if RUNNING_ON_SAMPLE()
    else "Running on local pipeline artifacts (full data)."
)
st.markdown(
    "*Offline demo mode — forecasts and recommendations are computed from "
    f"cached data (Oct 2025). No live API key is required. {_data_source_note}*"
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
