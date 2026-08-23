"""MandiPulse overview — the Streamlit entry page.

Mirrors the Next.js ``/`` route under the Market Atlas Workbench contract:
a decision-first technical overview with a live decision preview at artifact
defaults, evaluation facts traced to committed artifacts, the ranking
pipeline, and an anchored method-and-limitations section. Navigation order
matches the Next.js rail: Overview (this page) -> Decision -> Forecast ->
Coverage.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st  # noqa: E402

from mandipulse.app.data_access import (  # noqa: E402
    RUNNING_ON_SAMPLE,
    add_staleness_days,
    load_baseline_sensitivity,
    load_forecasts,
    load_mandi_metadata,
    load_recommendation_backtest,
)
from mandipulse.app.design import (  # noqa: E402
    FROZEN_NOTICE,
    SNAPSHOT_LABEL,
    format_inr_per_qtl,
    format_pct,
    inject_base_css,
)
from mandipulse.config import load_yaml_config  # noqa: E402
from mandipulse.policy import (  # noqa: E402
    canonical_forecast_as_of,
    select_recommendation_candidates,
)
from mandipulse.recommend.engine import score_recommendations  # noqa: E402
from mandipulse.recommend.evaluation import summarize_backtest  # noqa: E402

st.set_page_config(
    page_title="MandiPulse — Onion Mandi Decision Intelligence",
    page_icon=":seedling:",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_base_css()

_cfg = load_yaml_config("configs/recommendation.yaml")
_tc = _cfg.get("transport_cost", {})
_rk = _cfg.get("ranking", {})
_rt = _cfg.get("risk_thresholds", {})
ROAD_FACTOR = float(_tc.get("road_distance_factor", 1.3))
COST_PER_KM = float(_tc.get("cost_per_km_per_quintal", 4.0))
MAX_RADIUS_KM = float(_tc.get("max_transport_radius_km", 500))
LOW_MAX_PCT = float(_rt.get("low_max_interval_pct", 10)) / 100
HIGH_MIN_PCT = float(_rt.get("high_min_interval_pct", 25)) / 100
PENALTY_WEIGHT = float(_rk.get("uncertainty_penalty_weight", 0.3))

# Default farmer mirrors the web client's meta.default_farmer (Nashik).
DEFAULT_LAT = 19.9975
DEFAULT_LON = 73.7898
DEFAULT_QUANTITY_QTL = 100

# ---------------------------------------------------------------------------
# Header: wordmark, snapshot status, frozen-data notice, primary CTA.
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <h1 class="mp-wordmark">MandiPulse</h1>
    <div class="mp-snapshot-label">{SNAPSHOT_LABEL} · onion · Maharashtra · 7-day horizon</div>
    <p class="mp-frozen-note">{FROZEN_NOTICE}</p>
    """,
    unsafe_allow_html=True,
)

if RUNNING_ON_SAMPLE():
    st.info(
        "Offline demo mode — running on the bundled Oct 2025 sample snapshot. "
        "No API key or live feed is used.",
        icon=":material/info:",
    )

st.markdown("#### Sell where the transport-adjusted net price is strongest.")
st.markdown(
    "MandiPulse ranks supported Maharashtra onion mandis by expected net price "
    "after estimated transport, using a frozen seven-day forecast. Every figure "
    "traces to a committed artifact; nothing is live."
)

st.page_link(
    "pages/1_Decision.py", label="Open the Decision workbench", icon=":material/arrow_forward:"
)
st.markdown("[Read the method](#method-and-limitations)")

# ---------------------------------------------------------------------------
# Decision preview at artifact defaults.
# ---------------------------------------------------------------------------
st.header("Decision preview at default assumptions")
st.caption(
    f"Location: default farmer ({DEFAULT_LAT:.4f}, {DEFAULT_LON:.4f}) · "
    f"quantity {DEFAULT_QUANTITY_QTL} qtl · rate {COST_PER_KM} INR/km/quintal scenario · "
    f"radius {MAX_RADIUS_KM:.0f} km. Adjust all of these in the workbench."
)

try:
    _all_forecasts = add_staleness_days(load_forecasts())
    _mandis = load_mandi_metadata()
except Exception as exc:  # artifact missing entirely
    st.error(
        f"Forecast artifacts are unavailable ({exc}). Run "
        "`python scripts/build_forecast_intervals_7d.py` to generate them."
    )
    st.stop()

_canonical_as_of = canonical_forecast_as_of(_all_forecasts)
_candidates = select_recommendation_candidates(_all_forecasts)
_mandis_coords = _mandis.dropna(subset=["latitude", "longitude"]).copy()

try:
    ranked = score_recommendations(
        forecasts=_candidates,
        mandis=_mandis_coords,
        farmer_latitude=DEFAULT_LAT,
        farmer_longitude=DEFAULT_LON,
        cost_per_km_per_quintal=COST_PER_KM,
        road_distance_factor=ROAD_FACTOR,
        uncertainty_penalty_weight=PENALTY_WEIGHT,
        low_max_interval_pct=LOW_MAX_PCT,
        high_min_interval_pct=HIGH_MIN_PCT,
        candidate_state="maharashtra",
    )
    ranked = ranked[ranked["road_distance_km"] <= MAX_RADIUS_KM].reset_index(drop=True)
    ranked["rank"] = range(1, len(ranked) + 1)
except Exception as exc:
    st.error(f"Recommendation engine error: {exc}")
    st.stop()

_n_stale = int((_all_forecasts["staleness_days"] > 0).sum())
st.caption(
    f"Canonical as-of {_canonical_as_of.isoformat()}: "
    f"{len(ranked)} eligible candidates · {_n_stale} stale excluded · "
    f"{len(_candidates) - len(ranked)} beyond radius excluded."
)

if ranked.empty:
    st.warning(
        "No eligible candidates at the default assumptions. Increase the road "
        "radius in the Decision workbench."
    )
else:
    top = ranked.iloc[0]
    alts = ranked.iloc[1:3]
    c_main, c_alt = st.columns([2, 3])
    with c_main:
        st.metric(
            "Rank 1 — transport-adjusted net price",
            format_inr_per_qtl(top["transport_adjusted_net_price_inr_qtl"]),
            help=(
                f"{top['mandi']} ({top['district_name']}): forecast "
                f"{format_inr_per_qtl(top['forecast_price_inr_qtl'])} minus transport "
                f"{format_inr_per_qtl(top['estimated_transport_cost_inr_qtl'])} "
                f"({top['road_distance_km']:.0f} km road)."
            ),
        )
        st.markdown(f"**{top['mandi']}** · {top['district_name']}")
        staleness = int(
            _all_forecasts.loc[
                _all_forecasts["market_id"] == top["market_id"], "staleness_days"
            ].iloc[0]
        )
        if staleness > 0:
            st.warning(f"This forecast is {staleness} days behind the current snapshot window.")
    with c_alt:
        st.markdown("**Next best options**")
        for _, alt in alts.iterrows():
            diff = (
                alt["transport_adjusted_net_price_inr_qtl"]
                - top["transport_adjusted_net_price_inr_qtl"]
            )
            st.markdown(
                f"- **{alt['mandi']}** ({alt['district_name']}) — "
                f"{format_inr_per_qtl(alt['transport_adjusted_net_price_inr_qtl'])} "
                f"({format_inr_per_qtl(diff)} vs rank 1)"
            )
    st.caption(
        "Ranking: expected net price minus estimated transport, highest first; "
        "equal prices break by market identifier. Forecast uncertainty is shown "
        "as separate evidence and does not change the order."
    )

# ---------------------------------------------------------------------------
# Evaluation facts.
# ---------------------------------------------------------------------------
st.header("Evaluation facts")

sensitivity = load_baseline_sensitivity()
backtest_df = load_recommendation_backtest()
bt = summarize_backtest(backtest_df, k_values=[1]) if backtest_df is not None else {}

f_scope, f_model, f_iv, f_rank = st.columns(4)
with f_scope:
    st.markdown("**Scope**")
    st.markdown(
        f"Onion · Maharashtra<br>{len(_mandis)} mandis<br>7-day horizon<br>"
        f"Snapshot end {SNAPSHOT_LABEL.replace('Snapshot ', '')}",
        unsafe_allow_html=True,
    )
with f_model:
    st.markdown("**Shipped forecaster**")
    if sensitivity is not None:
        test_rows = sensitivity[sensitivity["split"] == "test"]
        shipped = test_rows[test_rows["model"] == "moving_average_7d"]
        if not shipped.empty:
            row = shipped.iloc[0]
            st.markdown(
                f"`moving_average_7d`<br>Test MAE {format_inr_per_qtl(row['mae'], 2)}",
                unsafe_allow_html=True,
            )
        unshipped = test_rows[test_rows["model"] != "moving_average_7d"]
        for _, u in unshipped.iterrows():
            st.markdown(f"Not shipped: `{u['model']}` — {u['mae']:.0f} INR/qtl MAE")
    else:
        st.markdown("_Run the pipeline to see the model comparison table._")
with f_iv:
    st.markdown("**Prediction interval**")
    levels = sorted(set(_candidates["confidence_level"].unique()))
    level_label = " / ".join(format_pct(lv * 100, 0) for lv in levels) if levels else "—"
    st.markdown(f"Nominal level {level_label}")
    st.markdown("Empirical coverage below nominal on held-out dates; stated as such.")
with f_rank:
    st.markdown("**Ranking evaluation**")
    if bt:
        st.markdown(
            f"Mean regret@1 {format_inr_per_qtl(bt['regret_at_1_mean'], 1)}<br>"
            f"Nearest-mandi baseline {format_inr_per_qtl(bt['nearest_mandi_regret_mean'], 1)}<br>"
            f"Wins vs nearest {format_pct(bt['beats_nearest_1'] * 100)}<br>"
            f"{bt['n_dates']} dates, {bt['date_min']} – {bt['date_max']}",
            unsafe_allow_html=True,
        )
    else:
        st.markdown("_Run `scripts/run_recommendation_backtest_7d.py` for regret evidence._")

st.caption(
    "Evaluation uses temporal splits with a purge gap of at least the seven-day "
    "horizon; three rolling origins precede an untouched final holdout."
)

# ---------------------------------------------------------------------------
# How a ranking is produced.
# ---------------------------------------------------------------------------
st.header("How a ranking is produced")
st.markdown(
    rf"""
    1. **Frozen data snapshot** — a cleaned daily onion-price panel ending
       {_canonical_as_of.strftime("%d %b %Y")} feeds every surface. Imputed and
       unavailable days are flagged, never silently filled.
    2. **Seven-day forecast with interval** — each mandi receives a 7-day-ahead price
       estimate plus a prediction interval from the shipped policy above.
    3. **Transport estimate** — straight-line distance times the documented road factor
       ({ROAD_FACTOR}) times your scenario rate approximates cost per quintal. It is not
       a route quote.
    4. **Transport-adjusted comparison** — forecast minus transport gives expected net
       price per quintal; mandis rank highest-first with deterministic tie-breaks.
    """
)

# ---------------------------------------------------------------------------
# Method and limitations.
# ---------------------------------------------------------------------------
st.header("Method and limitations")
st.markdown(
    f"""
    - **Scope.** One commodity (onion), one state (Maharashtra), {len(_mandis)} mandis,
      a seven-day horizon, and a frozen snapshot. Nothing outside that boundary is estimated.
    - **Temporal evaluation.** Splits advance forward in time with a purge gap of at least
      the horizon so no target leaks into training. Three rolling origins precede an
      untouched final holdout; reported metrics come from held-out dates only.
    - **Forecasting policy.** The shipped forecaster (`moving_average_7d`) holds the best
      held-out MAE among evaluated model families; stronger families were trained,
      evaluated honestly, and do not ship because they did not beat this baseline.
    - **Uncertainty.** Prediction intervals accompany every forecast. Observed coverage on
      held-out dates was below the nominal level and is reported as such rather than
      described as conservative.
    - **Why uncertainty sits beside the rank, not inside it.** The shipped interval width
      is identical for every candidate in a snapshot, so subtracting it would shift all
      prices equally and change no order. It is displayed as evidence per candidate instead.
    - **What this product does not do:** no live prices or market feed; no guaranteed,
      optimal, or risk-adjusted outcome claims; transport figures are scenario estimates
      from air distance x {ROAD_FACTOR} x your rate, not navigation or carrier quotations;
      coordinates are expert input with no geocoding search; no booking, payment, trade
      execution, accounts, or messaging; no additional crops, states, horizons, or models
      beyond the frozen scope.
    """
)
