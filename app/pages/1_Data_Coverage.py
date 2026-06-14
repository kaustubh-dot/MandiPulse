from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import plotly.express as px  # noqa: E402
import streamlit as st  # noqa: E402

from mandipulse.app.data_access import (  # noqa: E402
    load_clean_panel,
    load_feature_table,
    load_mandi_metadata,
)

st.set_page_config(page_title="Data Coverage · MandiPulse", layout="wide")
st.title("Data Coverage")
st.caption("Verify dataset quality before trusting forecasts.")

with st.spinner("Loading data…"):
    panel = load_clean_panel()
    features = load_feature_table()
    mandis_meta = load_mandi_metadata()

# --- KPI strip ---
total_rows = len(panel)
observed = int(panel["is_observed"].sum())
imputed = int(panel["is_imputed"].fillna(False).sum())
date_min = panel["date"].min().date()
date_max = panel["date"].max().date()
n_mandis = panel["market_id"].nunique()
trainable = int(features["feature_row_valid"].astype(bool).sum())

st.markdown("### Dataset Overview")
k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Mandis", n_mandis)
k2.metric("Date Range", f"{date_min} → {date_max}")
k3.metric("Total Rows", f"{total_rows:,}")
k4.metric("Observed", f"{observed:,}", delta=f"{observed/total_rows:.0%}")
k5.metric("Imputed", f"{imputed:,}", delta=f"-{imputed/total_rows:.0%}", delta_color="inverse")
k6.metric("Trainable Rows", f"{trainable:,}")

st.divider()

# --- Per-mandi coverage bar chart ---
st.markdown("### Observed vs Imputed Rows per Mandi")

coverage = (
    panel.groupby(["market_id", "market_name"])
    .agg(
        observed=("is_observed", "sum"),
        imputed=("is_imputed", lambda x: x.fillna(False).sum()),
        total=("date", "count"),
    )
    .reset_index()
)
coverage["observed_pct"] = coverage["observed"] / coverage["total"]

coverage_long = coverage.melt(
    id_vars=["market_name"],
    value_vars=["observed", "imputed"],
    var_name="type",
    value_name="rows",
)
color_map = {"observed": "#1E40AF", "imputed": "#D97706"}
fig_cov = px.bar(
    coverage_long,
    x="market_name",
    y="rows",
    color="type",
    color_discrete_map=color_map,
    barmode="stack",
    labels={"market_name": "Mandi", "rows": "Rows", "type": "Type"},
    height=380,
)
fig_cov.update_layout(
    xaxis_tickangle=-40,
    legend_title_text="Row type",
    margin=dict(t=20, b=10),
    plot_bgcolor="#F8FAFC",
    paper_bgcolor="#F8FAFC",
)
st.plotly_chart(fig_cov, use_container_width=True)

# --- Missingness table ---
st.markdown("### Coverage Summary by Mandi")

coverage_display = coverage.merge(
    mandis_meta[["market_id", "district_name"]], on="market_id", how="left"
)[["market_name", "district_name", "total", "observed", "imputed", "observed_pct"]].copy()
coverage_display["observed_pct"] = (coverage_display["observed_pct"] * 100).round(1).astype(
    str
) + "%"
coverage_display = coverage_display.rename(
    columns={
        "market_name": "Mandi",
        "district_name": "District",
        "total": "Total",
        "observed": "Observed",
        "imputed": "Imputed",
        "observed_pct": "Obs %",
    }
).sort_values("Mandi")

st.dataframe(coverage_display, use_container_width=True, hide_index=True)

# --- Trainable rows per mandi ---
st.markdown("### Trainable Rows per Mandi (feature_row_valid = True)")
trainable_by_mandi = (
    features[features["feature_row_valid"].astype(bool)]
    .groupby("market_name")
    .size()
    .reset_index(name="trainable_rows")
    .sort_values("trainable_rows", ascending=False)
)
fig_tr = px.bar(
    trainable_by_mandi,
    x="market_name",
    y="trainable_rows",
    color_discrete_sequence=["#1E40AF"],
    labels={"market_name": "Mandi", "trainable_rows": "Trainable rows"},
    height=320,
)
fig_tr.update_layout(
    xaxis_tickangle=-40,
    margin=dict(t=20, b=10),
    plot_bgcolor="#F8FAFC",
    paper_bgcolor="#F8FAFC",
)
st.plotly_chart(fig_tr, use_container_width=True)

# --- Data caveat ---
st.markdown("### Data Notes")
st.warning(
    "**Data ends 2025-10-30.** All rows are from a cached CEDA/AGMARKNET dump. "
    "Imputed rows use forward-fill within a 7-day gap window. "
    "Rows with gaps > 7 days are flagged `long_gap` and excluded from training "
    "(`feature_row_valid = False`).",
    icon="⚠️",
)
