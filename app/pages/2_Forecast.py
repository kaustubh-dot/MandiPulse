from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

from mandipulse.app.data_access import (  # noqa: E402
    available_mandis,
    history_for_mandi,
    load_clean_panel,
    load_forecasts,
    load_report_markdown,
)

st.set_page_config(page_title="Forecast · MandiPulse", layout="wide")
st.title("7-Day Price Forecast")
st.caption("Select a mandi to review its price history, 7-day forecast, and uncertainty interval.")

with st.spinner("Loading data…"):
    panel = load_clean_panel()
    forecasts = load_forecasts()

mandis = available_mandis(forecasts)
selected_mandi = st.selectbox("Select Mandi", mandis, index=0)

mandi_row = forecasts[forecasts["mandi"] == selected_mandi].iloc[0]
market_id = int(mandi_row["market_id"])

history = history_for_mandi(panel, market_id)

# --- Forecast KPIs ---
st.divider()
col1, col2, col3, col4 = st.columns(4)
col1.metric(
    "Forecast Price (INR/qtl)",
    f"₹{mandi_row['forecast_price_inr_qtl']:.0f}",
)
col2.metric(
    "Lower Bound",
    f"₹{mandi_row['lower_bound_inr_qtl']:.0f}",
)
col3.metric(
    "Upper Bound",
    f"₹{mandi_row['upper_bound_inr_qtl']:.0f}",
)
col4.metric(
    "Confidence Level",
    f"{mandi_row['confidence_level']:.0%}",
)
st.caption(
    f"As-of date: **{mandi_row['as_of_date']}** · "
    f"Model: `{mandi_row['model_name']}` · "
    f"Horizon: {mandi_row['horizon_days']} days"
)

# --- Historical price chart with forecast + interval ---
st.markdown("### Price History + 7-Day Forecast")

# Last 90 days of history for readability
recent = history.tail(90)

fig = go.Figure()

# Historical actual prices
fig.add_trace(
    go.Scatter(
        x=recent["date"],
        y=recent["modal_price_inr_qtl"],
        mode="lines",
        name="Historical (modal)",
        line=dict(color="#1E40AF", width=2),
    )
)

# Imputed rows shown as lighter dots
imputed_mask = recent["is_imputed"].fillna(False).astype(bool)
if imputed_mask.any():
    fig.add_trace(
        go.Scatter(
            x=recent.loc[imputed_mask, "date"],
            y=recent.loc[imputed_mask, "modal_price_inr_qtl"],
            mode="markers",
            name="Imputed",
            marker=dict(color="#D97706", size=4, symbol="circle-open"),
        )
    )

# Forecast point (7 days after as_of_date)
import pandas as pd  # noqa: E402 (local import to avoid top-level namespace pollution)

as_of = pd.to_datetime(mandi_row["as_of_date"])
forecast_date = as_of + pd.Timedelta(days=7)

fig.add_trace(
    go.Scatter(
        x=[forecast_date],
        y=[mandi_row["forecast_price_inr_qtl"]],
        mode="markers",
        name="Forecast",
        marker=dict(color="#D97706", size=12, symbol="diamond"),
        error_y=dict(
            type="data",
            symmetric=False,
            array=[mandi_row["upper_bound_inr_qtl"] - mandi_row["forecast_price_inr_qtl"]],
            arrayminus=[mandi_row["forecast_price_inr_qtl"] - mandi_row["lower_bound_inr_qtl"]],
            visible=True,
            color="#D97706",
        ),
    )
)

# Confidence band (shaded area from last history date to forecast date)
fig.add_trace(
    go.Scatter(
        x=[as_of, forecast_date, forecast_date, as_of],
        y=[
            mandi_row["forecast_price_inr_qtl"],
            mandi_row["upper_bound_inr_qtl"],
            mandi_row["lower_bound_inr_qtl"],
            mandi_row["forecast_price_inr_qtl"],
        ],
        fill="toself",
        fillcolor="rgba(217,119,6,0.12)",
        line=dict(color="rgba(0,0,0,0)"),
        showlegend=True,
        name="90% interval",
    )
)

fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Modal Price (INR/quintal)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=420,
    plot_bgcolor="#F8FAFC",
    paper_bgcolor="#F8FAFC",
    hovermode="x unified",
)
st.plotly_chart(fig, use_container_width=True)

# --- Baseline comparison from report ---
st.markdown("### Baseline Model Metrics")
st.caption(
    "Lower MAE = better. `moving_average_7d` is the MVP production model for interval calibration."
)
with st.expander("View full baseline metrics report"):
    md = load_report_markdown("baseline_metrics_7d.md")
    st.markdown(md)

# --- Data notes ---
st.info(
    f"**{selected_mandi}** · market_id={market_id} · "
    f"History rows: {len(history)} · "
    f"Observed: {int(history['is_observed'].sum())} / Imputed: {int(history['is_imputed'].fillna(False).sum())}",
    icon="ℹ️",
)
