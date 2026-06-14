from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pandas as pd  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

from mandipulse.app.data_access import (  # noqa: E402
    load_forecasts,
    load_mandi_metadata,
)
from mandipulse.config import load_yaml_config  # noqa: E402
from mandipulse.recommend.engine import score_recommendations  # noqa: E402

st.set_page_config(page_title="Recommendation · MandiPulse", layout="wide")
st.title("Mandi Recommendation")
st.caption("Rank mandis by net price after transport cost. Adjust inputs to re-rank live.")

# Load config defaults
_cfg = load_yaml_config("configs/recommendation.yaml")
_tc = _cfg.get("transport_cost", {})
_rk = _cfg.get("ranking", {})
_rt = _cfg.get("risk_thresholds", {})

DEFAULT_ROAD_FACTOR = float(_tc.get("road_distance_factor", 1.3))
DEFAULT_COST_PER_KM = float(_tc.get("cost_per_km_per_quintal", 4.0))
DEFAULT_PENALTY = float(_rk.get("uncertainty_penalty_weight", 0.3))
LOW_MAX_PCT = float(_rt.get("low_max_interval_pct", 10)) / 100
HIGH_MIN_PCT = float(_rt.get("high_min_interval_pct", 25)) / 100

with st.spinner("Loading data…"):
    forecasts = load_forecasts()
    mandis_meta = load_mandi_metadata()

# --- Sidebar inputs ---
st.sidebar.header("Farmer Location & Inputs")

farmer_lat = st.sidebar.number_input(
    "Farmer Latitude",
    min_value=15.0,
    max_value=25.0,
    value=19.9975,
    step=0.01,
    format="%.4f",
    help="Default: Nashik region (19.9975°N)",
)
farmer_lon = st.sidebar.number_input(
    "Farmer Longitude",
    min_value=72.0,
    max_value=82.0,
    value=73.7898,
    step=0.01,
    format="%.4f",
    help="Default: Nashik region (73.7898°E)",
)
quantity_qtl = st.sidebar.number_input(
    "Quantity (quintals)",
    min_value=1.0,
    max_value=1000.0,
    value=100.0,
    step=10.0,
)

st.sidebar.divider()
st.sidebar.header("Transport Assumptions")
cost_per_km = st.sidebar.slider(
    "Cost per km per quintal (INR)",
    min_value=1.0,
    max_value=15.0,
    value=DEFAULT_COST_PER_KM,
    step=0.5,
    help=f"Config default: {DEFAULT_COST_PER_KM} INR/km/qtl",
)
road_factor = st.sidebar.slider(
    "Road distance factor",
    min_value=1.0,
    max_value=2.0,
    value=DEFAULT_ROAD_FACTOR,
    step=0.05,
    help=f"Airline → road multiplier. Config default: {DEFAULT_ROAD_FACTOR}",
)
penalty_weight = st.sidebar.slider(
    "Uncertainty penalty weight",
    min_value=0.0,
    max_value=1.0,
    value=DEFAULT_PENALTY,
    step=0.05,
    help=f"Fraction of interval width deducted from net price. Config default: {DEFAULT_PENALTY}",
)

# --- Score recommendations live ---
mandis_with_coords = mandis_meta.dropna(subset=["latitude", "longitude"])

try:
    recs = score_recommendations(
        forecasts=forecasts,
        mandis=mandis_with_coords,
        farmer_latitude=farmer_lat,
        farmer_longitude=farmer_lon,
        cost_per_km_per_quintal=cost_per_km,
        road_distance_factor=road_factor,
        uncertainty_penalty_weight=penalty_weight,
        low_max_interval_pct=LOW_MAX_PCT,
        high_min_interval_pct=HIGH_MIN_PCT,
        candidate_state="maharashtra",
    )
except Exception as exc:
    st.error(f"Recommendation engine error: {exc}")
    st.stop()

# --- Top-3 callout ---
st.markdown("### Top 3 Mandis by Risk-Adjusted Net Price")

_RISK_COLOR = {"low": "#16A34A", "medium": "#D97706", "high": "#DC2626"}
_RISK_ICON = {"low": "✅", "medium": "⚠️", "high": "🔴"}

top3 = recs.head(3)
cols = st.columns(3)
for i, (col, (_, row)) in enumerate(zip(cols, top3.iterrows())):
    risk = str(row["risk_level"])
    color = _RISK_COLOR.get(risk, "#475569")
    icon = _RISK_ICON.get(risk, "")
    with col:
        st.markdown(
            f"<div style='border:1px solid {color};border-radius:8px;padding:14px;background:#fff'>"
            f"<b>#{int(row['rank'])} {row['mandi']}</b><br>"
            f"<small style='color:#475569'>{row['district_name']}</small><br><br>"
            f"<b>Forecast:</b> ₹{row['forecast_price_inr_qtl']:.0f}<br>"
            f"<b>Transport:</b> ₹{row['estimated_transport_cost_inr_qtl']:.0f} "
            f"({row['road_distance_km']:.0f} km road)<br>"
            f"<b>Net price:</b> ₹{row['expected_net_price_inr_qtl']:.0f}<br>"
            f"<b>Risk:</b> <span style='color:{color}'>{icon} {risk.upper()}</span>"
            "</div>",
            unsafe_allow_html=True,
        )

st.divider()

# --- Full ranked table ---
st.markdown("### All Mandis Ranked")

display_cols = [
    "rank",
    "mandi",
    "district_name",
    "forecast_price_inr_qtl",
    "road_distance_km",
    "estimated_transport_cost_inr_qtl",
    "expected_net_price_inr_qtl",
    "uncertainty_penalty_inr_qtl",
    "risk_adjusted_score",
    "risk_level",
]
table = recs[display_cols].copy()
for col in [
    "forecast_price_inr_qtl",
    "road_distance_km",
    "estimated_transport_cost_inr_qtl",
    "expected_net_price_inr_qtl",
    "uncertainty_penalty_inr_qtl",
    "risk_adjusted_score",
]:
    table[col] = table[col].round(1)

table = table.rename(
    columns={
        "rank": "Rank",
        "mandi": "Mandi",
        "district_name": "District",
        "forecast_price_inr_qtl": "Forecast ₹/qtl",
        "road_distance_km": "Road km",
        "estimated_transport_cost_inr_qtl": "Transport ₹/qtl",
        "expected_net_price_inr_qtl": "Net Price ₹/qtl",
        "uncertainty_penalty_inr_qtl": "Penalty ₹/qtl",
        "risk_adjusted_score": "Score",
        "risk_level": "Risk",
    }
)
st.dataframe(table, use_container_width=True, hide_index=True)

# --- Map ---
st.markdown("### Map: Farmer Location + Mandis")

map_data = mandis_with_coords.merge(
    recs[["market_id", "rank", "risk_level"]], on="market_id", how="left"
)
map_data["color"] = (
    map_data["risk_level"]
    .map({"low": "#16A34A", "medium": "#D97706", "high": "#DC2626"})
    .fillna("#475569")
)

farmer_point = pd.DataFrame({"lat": [farmer_lat], "lon": [farmer_lon], "label": ["🧑‍🌾 Farmer"]})

fig_map = go.Figure()
fig_map.add_trace(
    go.Scattermapbox(
        lat=map_data["latitude"],
        lon=map_data["longitude"],
        mode="markers+text",
        marker=go.scattermapbox.Marker(
            size=12,
            color=map_data["color"],
        ),
        text=map_data["market_name"] + " #" + map_data["rank"].astype(str),
        textposition="top right",
        name="Mandis",
    )
)
fig_map.add_trace(
    go.Scattermapbox(
        lat=[farmer_lat],
        lon=[farmer_lon],
        mode="markers+text",
        marker=go.scattermapbox.Marker(size=16, color="#1E40AF", symbol="star"),
        text=["🧑‍🌾 Farm"],
        textposition="top right",
        name="Farmer",
    )
)
fig_map.update_layout(
    mapbox_style="open-street-map",
    mapbox_zoom=6,
    mapbox_center={"lat": (farmer_lat + 19.5) / 2, "lon": (farmer_lon + 75.5) / 2},
    height=450,
    margin=dict(t=0, b=0, l=0, r=0),
)
st.plotly_chart(fig_map, use_container_width=True)

# --- Config reference ---
with st.expander("Assumption details"):
    st.markdown(
        f"- Road distance factor: **{road_factor}** (config default: {DEFAULT_ROAD_FACTOR})\n"
        f"- Transport cost: **{cost_per_km} INR/km/qtl** (config default: {DEFAULT_COST_PER_KM})\n"
        f"- Uncertainty penalty weight: **{penalty_weight}** (config default: {DEFAULT_PENALTY})\n"
        f"- Risk thresholds: low ≤ {LOW_MAX_PCT:.0%}, high ≥ {HIGH_MIN_PCT:.0%}\n\n"
        "Ranking formula: `score = net_price − penalty_weight × interval_width`"
    )
st.warning(
    "This is decision support, not a guaranteed-profit recommendation. "
    "Transport cost estimates use haversine distance × road factor and do not account for "
    "seasonal road conditions, vehicle type, or market entry fees.",
    icon="⚠️",
)
