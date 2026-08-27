"""Decision workbench — ranks mandis by transport-adjusted net expected price.

Streamlit counterpart of the Next.js ``/recommend`` route under the Quiet
Exchange contract: decision inputs stay beside their results in the
page body, the shared recommendation engine produces the ranking, and every
figure traces back to the frozen October 2025 snapshot.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pandas as pd  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

from mandipulse.app.data_access import (  # noqa: E402
    add_staleness_days,
    load_forecasts,
    load_mandi_metadata,
    load_recommendation_backtest,
    load_report_markdown,
)
from mandipulse.app.design import (  # noqa: E402
    ACCENT_HEX,
    DEFAULT_LAT,
    DEFAULT_LON,
    DEFAULT_QUANTITY_QTL,
    EM_DASH,
    INK_HEX,
    MUTED_HEX,
    SNAPSHOT_LABEL,
    format_date_iso,
    format_inr,
    format_inr_per_qtl,
    format_interval,
    format_km,
    format_pct,
    format_quantity,
    inject_base_css,
    plotly_theme,
    render_frozen_notice,
    render_page_header,
    render_section_heading,
)
from mandipulse.config import load_yaml_config  # noqa: E402
from mandipulse.policy import (  # noqa: E402
    canonical_forecast_as_of,
    forecast_target_date,
    select_recommendation_candidates,
)
from mandipulse.recommend.engine import score_recommendations  # noqa: E402
from mandipulse.recommend.evaluation import summarize_backtest  # noqa: E402

st.set_page_config(page_title="Decision · MandiPulse", layout="wide")
inject_base_css()

_cfg = load_yaml_config("configs/recommendation.yaml")
_tc = _cfg.get("transport_cost", {})
_rk = _cfg.get("ranking", {})
_rt = _cfg.get("risk_thresholds", {})
COST_PER_KM = float(_tc.get("cost_per_km_per_quintal", 4.0))
ROAD_FACTOR = float(_tc.get("road_distance_factor", 1.3))
MAX_RADIUS_KM = float(_tc.get("max_transport_radius_km", 500))
PENALTY_WEIGHT = float(_rk.get("uncertainty_penalty_weight", 0.3))
MAX_ALTERNATIVES = int(_rk.get("max_alternatives", 10))
RISK_LOW_MAX_PCT = float(_rt.get("low_max_interval_pct", 10))
RISK_HIGH_MIN_PCT = float(_rt.get("high_min_interval_pct", 25))

# ---------------------------------------------------------------------------

_RISK_LABELS = {"low": "Low", "medium": "Medium", "high": "High"}


def _risk_label(level: Any) -> str:
    """Return a spoken risk label; text always accompanies any risk color."""
    return _RISK_LABELS.get(str(level), "Unknown")


def _arithmetic_sentence(row: pd.Series) -> str:
    """One-line arithmetic explanation of why a mandi holds its rank."""
    return (
        f"{row['mandi']}: forecast {format_inr_per_qtl(row['forecast_price_inr_qtl'])} "
        f"\u2212 transport {format_inr_per_qtl(row['estimated_transport_cost_inr_qtl'])} = "
        f"{format_inr_per_qtl(row['expected_net_price_inr_qtl'])} net "
        f"({format_km(row['road_distance_km'])} road, {format_km(row['air_distance_km'])} air)."
    )


def _ranking_table(ranked: pd.DataFrame) -> pd.DataFrame:
    """Build the ranked comparison frame with presentation-friendly columns."""
    return pd.DataFrame(
        {
            "Rank": ranked["rank"].astype(int),
            "Mandi": ranked["mandi"],
            "District": ranked["district_name"],
            "As-of": ranked["as_of_date"].map(format_date_iso),
            "Stale days": ranked["staleness_days"].astype(int),
            "Forecast (INR/qtl)": ranked["forecast_price_inr_qtl"],
            "Road km": ranked["road_distance_km"],
            "Transport (INR/qtl)": ranked["estimated_transport_cost_inr_qtl"],
            "Net price (INR/qtl)": ranked["expected_net_price_inr_qtl"],
            "Penalty (evidence only)": ranked["uncertainty_penalty_inr_qtl"],
            "Transport-adjusted net (INR/qtl)": ranked["transport_adjusted_net_price_inr_qtl"],
            "Risk": ranked["risk_level"].map(_risk_label),
        }
    )


def _candidate_map(ranked: pd.DataFrame, farmer_lat: float, farmer_lon: float) -> go.Figure:
    """Plot candidates on OpenStreetMap with the rank-1 marker dominant."""
    fig = go.Figure()
    others = ranked.iloc[1:]
    fig.add_trace(
        go.Scattermap(
            lat=others["latitude"].tolist(),
            lon=others["longitude"].tolist(),
            mode="markers",
            name="Other candidates",
            marker={"size": 11, "color": MUTED_HEX, "opacity": 0.85},
            text=[
                f"{row['mandi']} · Rank {int(row['rank'])} · "
                f"{format_inr_per_qtl(row['transport_adjusted_net_price_inr_qtl'])} net · "
                f"{format_km(row['road_distance_km'], 0)} road"
                for _, row in others.iterrows()
            ],
            hoverinfo="text",
        )
    )
    top = ranked.iloc[0]
    fig.add_trace(
        go.Scattermap(
            lat=[float(top["latitude"])],
            lon=[float(top["longitude"])],
            mode="markers",
            name="Rank 1 mandi",
            marker={"size": 22, "color": ACCENT_HEX, "opacity": 0.95},
            text=[
                f"{top['mandi']} · Rank 1 · "
                f"{format_inr_per_qtl(top['transport_adjusted_net_price_inr_qtl'])} net · "
                f"{format_km(top['road_distance_km'], 0)} road"
            ],
            hoverinfo="text",
        )
    )
    fig.add_trace(
        go.Scattermap(
            lat=[farmer_lat],
            lon=[farmer_lon],
            mode="markers",
            name="Your location",
            marker={"size": 15, "color": INK_HEX, "symbol": "circle"},
            text=["Selected farm location"],
            hoverinfo="text",
        )
    )
    lats = [farmer_lat, *ranked["latitude"].astype(float).tolist()]
    lons = [farmer_lon, *ranked["longitude"].astype(float).tolist()]
    fig.update_layout(**plotly_theme())
    fig.update_layout(
        map={
            "style": "open-street-map",
            "center": {"lat": sum(lats) / len(lats), "lon": sum(lons) / len(lons)},
            "zoom": 5,
        },
        height=440,
        showlegend=True,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 0.01,
            "x": 0,
            "bgcolor": "rgba(0,0,0,0)",
        },
    )
    return fig


# ---------------------------------------------------------------------------
# Header: title, caption, frozen notice.
# ---------------------------------------------------------------------------
render_page_header(
    "Decision workbench",
    "Set your location, lot size, and transport assumptions. Mandis rank by "
    "transport-adjusted net expected price from a frozen seven-day forecast.",
)
render_frozen_notice()

try:
    forecasts_all = add_staleness_days(load_forecasts())
    mandis_meta = load_mandi_metadata()
except Exception as exc:  # pragma: no cover — artifact read failures
    st.error(f"Snapshot artifacts are unavailable ({exc}). Run the pipeline, then reload.")
    st.stop()

for _key, _default in [
    ("saved_lat", DEFAULT_LAT),
    ("saved_lon", DEFAULT_LON),
    ("saved_quantity", DEFAULT_QUANTITY_QTL),
    ("saved_rate", COST_PER_KM),
    ("saved_radius", MAX_RADIUS_KM),
]:
    if _key not in st.session_state:
        st.session_state[_key] = _default


def _sync_decision_inputs() -> None:
    st.session_state["saved_lat"] = st.session_state["farmer_lat"]
    st.session_state["saved_lon"] = st.session_state["farmer_lon"]
    st.session_state["saved_quantity"] = st.session_state["quantity_qtl"]
    st.session_state["saved_rate"] = st.session_state["transport_rate"]
    st.session_state["saved_radius"] = st.session_state["radius_km"]


inputs_col, results_col = st.columns([1, 2], gap="large")

with inputs_col:
    st.subheader("Decision inputs")
    st.caption("Coordinates are expert input. There is no geocoding search.")
    farmer_lat = st.number_input(
        "Latitude",
        min_value=-90.0,
        max_value=90.0,
        value=float(st.session_state["saved_lat"]),
        step=0.0001,
        format="%.4f",
        help="Decimal degrees, \u221290 to 90.",
        key="farmer_lat",
        on_change=_sync_decision_inputs,
    )
    farmer_lon = st.number_input(
        "Longitude",
        min_value=-180.0,
        max_value=180.0,
        value=float(st.session_state["saved_lon"]),
        step=0.0001,
        format="%.4f",
        help="Decimal degrees, \u2212180 to 180.",
        key="farmer_lon",
        on_change=_sync_decision_inputs,
    )
    quantity_qtl = st.number_input(
        "Quantity (quintals)",
        min_value=0.5,
        value=float(st.session_state["saved_quantity"]),
        step=0.5,
        format="%.1f",
        help="Lot size used for the net estimate; must be greater than 0.",
        key="quantity_qtl",
        on_change=_sync_decision_inputs,
    )
    transport_rate = st.number_input(
        "Transport rate (INR/km/quintal)",
        min_value=0.0,
        value=float(st.session_state["saved_rate"]),
        step=0.5,
        format="%.2f",
        help="Scenario assumption, not a carrier quotation.",
        key="transport_rate",
        on_change=_sync_decision_inputs,
    )
    radius_km = st.number_input(
        "Maximum road radius (km)",
        min_value=1.0,
        value=float(st.session_state["saved_radius"]),
        step=10.0,
        format="%.0f",
        help="Candidates beyond this estimated road distance are excluded.",
        key="radius_km",
        on_change=_sync_decision_inputs,
    )
    st.caption(
        f"Road estimate: Haversine air distance \u00d7 {ROAD_FACTOR}. Results update "
        "automatically as inputs change \u2014 the workbench compares mandis on every edit."
    )

with results_col:
    st.subheader("Results")
    canonical_as_of = canonical_forecast_as_of(forecasts_all)
    try:
        candidates = select_recommendation_candidates(forecasts_all)
    except ValueError:
        st.warning(
            f"No forecasts match the canonical as-of policy (bundle maximum, "
            f"{format_date_iso(canonical_as_of)}), so no ranking can be produced. "
            "Regenerate the forecast artifacts, then reload."
        )
        st.stop()
    stale_excluded = len(forecasts_all) - len(candidates)

    mandis_coords = mandis_meta.dropna(subset=["latitude", "longitude"])
    try:
        scored = score_recommendations(
            forecasts=candidates,
            mandis=mandis_coords,
            farmer_latitude=float(farmer_lat),
            farmer_longitude=float(farmer_lon),
            cost_per_km_per_quintal=float(transport_rate),
            road_distance_factor=ROAD_FACTOR,
            uncertainty_penalty_weight=PENALTY_WEIGHT,
            low_max_interval_pct=RISK_LOW_MAX_PCT / 100,
            high_min_interval_pct=RISK_HIGH_MIN_PCT / 100,
            candidate_state="maharashtra",
        )
    except Exception as exc:
        st.error(f"Recommendation engine error: {exc}")
        st.stop()

    within_radius = scored["road_distance_km"] <= float(radius_km)
    beyond_radius_excluded = int((~within_radius).sum())
    ranked = scored.loc[within_radius].reset_index(drop=True)
    if ranked.empty:
        st.warning(
            f"No candidates within {format_km(radius_km, 0)}: {len(candidates)} eligible "
            f"forecasts at the canonical as-of date ({stale_excluded} excluded as stale "
            "by the canonical as-of policy), and "
            f"{beyond_radius_excluded} of those fresh forecasts sit beyond the radius. "
            "Increase the maximum road radius, then compare again."
        )
    else:
        ranked["rank"] = range(1, len(ranked) + 1)
        evidence = candidates[["market_id", "as_of_date", "staleness_days", "confidence_level"]]
        evidence = evidence.merge(
            mandis_coords[["market_id", "latitude", "longitude"]],
            on="market_id",
            how="inner",
            validate="one_to_one",
        )
        ranked = ranked.merge(evidence, on="market_id", how="left", validate="one_to_one")
        display_frame = ranked.head(MAX_ALTERNATIVES).copy()

        top = display_frame.iloc[0]
        top_net = float(top["transport_adjusted_net_price_inr_qtl"])
        st.metric("Transport-adjusted net expected price", format_inr_per_qtl(top_net))
        st.markdown(f"**Rank 1 — {top['mandi']}** · {top['district_name']}")
        st.markdown(_arithmetic_sentence(top))
        st.caption(
            f"Lot net estimate {format_inr(top_net * float(quantity_qtl), 0)} for "
            f"{format_quantity(quantity_qtl)}. Basis of the ranking: highest expected "
            "price after subtracting estimated transport from the frozen forecast."
        )
        top_stale_days = int(top["staleness_days"])
        if top_stale_days > 0:
            st.warning(
                f"This forecast is {top_stale_days} days behind the current snapshot window."
            )

        alternatives = display_frame.iloc[1:3]
        if not alternatives.empty:
            st.markdown("**Alternative recommendations**")
            for _, alt in alternatives.iterrows():
                alt_net = float(alt["transport_adjusted_net_price_inr_qtl"])
                diff = alt_net - top_net
                stale_note = ""
                if int(alt["staleness_days"]) > 0:
                    stale_note = (
                        f" · forecast {int(alt['staleness_days'])} days behind the "
                        "current snapshot window"
                    )
                st.markdown(
                    f"- **#{int(alt['rank'])} {alt['mandi']}** ({alt['district_name']}) {EM_DASH} "
                    f"{format_inr_per_qtl(alt_net)} net ({format_inr_per_qtl(diff)} vs rank 1) "
                    f"· forecast {format_inr_per_qtl(alt['forecast_price_inr_qtl'])} · "
                    f"transport {format_inr_per_qtl(alt['estimated_transport_cost_inr_qtl'])} · "
                    f"{format_km(alt['road_distance_km'], 0)} road · "
                    f"{_risk_label(alt['risk_level'])} risk{stale_note}"
                )

        render_section_heading(f"Top {len(display_frame)} eligible mandis")
        st.dataframe(
            _ranking_table(display_frame).round(1),
            hide_index=True,
            width="stretch",
        )
        st.caption(
            "Ranked by transport-adjusted net expected price, highest first; equal prices "
            "break by market identifier. Stale forecasts stay ranked and are flagged in "
            "the Stale days column; only the canonical as-of policy and the road radius "
            "exclude candidates."
        )

        render_section_heading("Candidate map")
        st.plotly_chart(
            _candidate_map(display_frame, float(farmer_lat), float(farmer_lon)),
            width="stretch",
        )
        st.caption(
            "Dark circle: rank-1 mandi. Smaller circles: other candidates. "
            "Exact distances repeat in the table above."
        )

        render_section_heading("Evidence")
        levels = sorted(set(candidates["confidence_level"].dropna().unique()))
        level_label = " / ".join(format_pct(float(level) * 100, 0) for level in levels) or EM_DASH
        target_date = forecast_target_date(top["as_of_date"], int(top["horizon_days"]))
        ev_left, ev_right = st.columns(2)
        with ev_left:
            st.markdown("**Interval method**")
            st.markdown(f"- Nominal level: {level_label}")
            st.markdown(
                "- Rank-1 bounds: "
                f"{format_interval(top['lower_bound_inr_qtl'], top['upper_bound_inr_qtl'])}"
            )
            st.markdown(
                "- Uncertainty penalty: "
                f"{format_inr_per_qtl(top['uncertainty_penalty_inr_qtl'])} {EM_DASH} "
                "identical across candidates; does not affect order."
            )
        with ev_right:
            st.markdown("**Snapshot and horizon**")
            st.markdown(f"- Snapshot date: {SNAPSHOT_LABEL.replace('Snapshot ', '')}")
            st.markdown(f"- Forecast as-of: {format_date_iso(canonical_as_of)}")
            st.markdown(f"- Sale target: {format_date_iso(target_date)}")
            st.markdown(f"- Horizon: {int(top['horizon_days'])}-day ahead")

render_section_heading(
    "Regret evaluation", "Held-out replay of the same ranking policy over historical as-of dates."
)
backtest_df = load_recommendation_backtest()
if backtest_df is None:
    st.info(
        "No recommendation backtest artifact was found, so ranking-regret evidence "
        "is unavailable. Generate it with:\n"
        "```\n"
        "python scripts/run_recommendation_backtest_7d.py\n"
        "```"
    )
else:
    summary = summarize_backtest(backtest_df, k_values=[1])
    if not summary:
        st.info(
            "The backtest artifact is empty. Regenerate it with "
            "`python scripts/run_recommendation_backtest_7d.py`."
        )
    else:
        b_regret, b_wins, b_baseline, b_dates = st.columns(4)
        b_regret.metric("Mean regret@1", format_inr_per_qtl(summary["regret_at_1_mean"], 1))
        b_wins.metric("Wins vs nearest", format_pct(summary["beats_nearest_1"] * 100))
        b_baseline.metric(
            "Nearest-mandi baseline regret",
            format_inr_per_qtl(summary["nearest_mandi_regret_mean"], 1),
        )
        b_dates.metric("Dates evaluated", f"{summary['n_dates']}")
        st.caption(
            f"Held-out window {format_date_iso(summary['date_min'])} \u2013 "
            f"{format_date_iso(summary['date_max'])}. Regret compares the realized "
            "net price of the picked mandi against the best realized net price."
        )
        with st.expander("Open the full backtest report"):
            st.markdown(load_report_markdown("recommendation_backtest_7d.md"))

with st.expander("Assumptions and ranking policy"):
    st.markdown(
        f"""
        - Road distance estimate: Haversine air distance \u00d7 {ROAD_FACTOR} (documented road factor).
        - Rate applied: {transport_rate:g} INR/km/quintal scenario, not a carrier quotation.
        - Maximum road radius: {format_km(radius_km, 0)}.
        - Risk thresholds: relative interval width at most {format_pct(RISK_LOW_MAX_PCT, 0)}
          is low risk; at least {format_pct(RISK_HIGH_MIN_PCT, 0)} is high risk.
        - Ranking: expected net price = forecast \u2212 estimated transport cost, sorted
          descending with market_id tie-break; the uncertainty penalty is separate
          evidence because the public interval width is global.
        """
    )

st.warning(
    "**Decision support, not guaranteed profit.** Figures come from a frozen seven-day "
    "forecast; transport costs are straight-line distance \u00d7 road factor \u00d7 your "
    "scenario rate, not route-accurate freight quotations."
)
