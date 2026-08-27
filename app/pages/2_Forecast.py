"""Forecast exploration page — Streamlit parity with the Next.js ``/forecast`` route.

Follows ``docs/APP_FLOW.md`` section 5.2 content order exactly: mandi identity
and forecast date, headline forecast price, prediction-interval bounds with a
data-driven method label, history-plus-forecast chart, model-versus-baseline
evidence, a missingness/data-quality note, and a closing action back to the
Decision workbench. All presentation tokens, formatters, and the Plotly theme
come exclusively from :mod:`mandipulse.app.design`.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pandas as pd  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

from mandipulse.app.data_access import (  # noqa: E402
    add_staleness_days,
    available_mandis,
    history_for_mandi,
    load_baseline_sensitivity,
    load_clean_panel,
    load_forecasts,
    load_mandi_metadata,
    persist_decision_location,
)
from mandipulse.app.design import (  # noqa: E402
    ACCENT_HEX,
    ACCENT_INK_HEX,
    EM_DASH,
    INK_HEX,
    MUTED_HEX,
    format_date_iso,
    format_inr_per_qtl,
    format_interval,
    format_pct,
    inject_base_css,
    plotly_theme,
    render_frozen_notice,
    render_page_header,
    render_section_heading,
)

st.set_page_config(page_title="Forecast · MandiPulse", layout="wide")

inject_base_css()

SELECT_KEY = "forecast_mandi"
HISTORY_WINDOW_DAYS = 90

PANEL_REGEN_COMMANDS = (
    "python scripts/build_clean_onion_panel.py\n"
    "python scripts/build_feature_table.py\n"
    "python scripts/train_baselines_7d.py\n"
    "python scripts/train_lightgbm_7d.py\n"
    "python scripts/build_forecast_intervals_7d.py\n"
    "python scripts/build_recommendations_7d.py"
)


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    """Convert an ``#rrggbb`` design token into an ``rgba()`` string."""
    value = hex_color.lstrip("#")
    red, green, blue = (int(value[i : i + 2], 16) for i in (0, 2, 4))
    return f"rgba({red}, {green}, {blue}, {alpha})"


def _default_mandi_name(forecasts: pd.DataFrame) -> str | None:
    """Pick the default mandi: freshest as-of date first, alphabetical tie-break."""
    if forecasts.empty:
        return None
    dates = pd.to_datetime(forecasts["as_of_date"])
    freshest = dates.max()
    fresh_names = sorted(forecasts.loc[dates == freshest, "mandi"].tolist())
    return str(fresh_names[0])


def _selected_forecast_row(forecasts: pd.DataFrame, mandi_name: str) -> pd.Series:
    """Return the freshest forecast row for one mandi name."""
    rows = forecasts[forecasts["mandi"] == mandi_name]
    return rows.sort_values("as_of_date").iloc[-1]


def _load_panel_or_stop() -> pd.DataFrame:
    """Load the clean daily panel, or stop with exact regeneration guidance."""
    try:
        return load_clean_panel()
    except Exception as exc:  # noqa: BLE001 - surface any read failure as guidance
        st.error(
            f"**Clean price panel unavailable** ({exc}).\n\n"
            "The Forecast page needs the cleaned daily onion-price panel "
            "(`clean_mandi_prices.csv`). Regenerate the artifacts:\n"
            f"```\n{PANEL_REGEN_COMMANDS}\n```\n"
            "If the full snapshot is unavailable, the bundled sample is used automatically."
        )
        st.stop()


def _load_metadata_safe() -> pd.DataFrame | None:
    """Load mandi metadata, returning None (not failing) when it cannot be read."""
    try:
        metadata = load_mandi_metadata()
    except Exception:  # noqa: BLE001 - district names are optional context
        return None
    return None if metadata.empty else metadata


def _district_for(metadata: pd.DataFrame | None, market_id: object) -> str:
    """Resolve the district name for a market id, or an em dash when unknown."""
    if metadata is None or "district_name" not in metadata.columns:
        return EM_DASH
    matches = metadata.loc[metadata["market_id"] == market_id, "district_name"]
    if matches.empty:
        return EM_DASH
    value = str(matches.iloc[0])
    return value if value.strip().lower() not in {"", "nan", "none"} else EM_DASH


def _window_for_as_of(as_of: pd.Timestamp) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Return the inclusive day bounds of the plotted history window."""
    end = pd.Timestamp(as_of).normalize()
    return end - pd.Timedelta(days=HISTORY_WINDOW_DAYS - 1), end


def _imputed_mask(frame: pd.DataFrame) -> pd.Series:
    """Return a boolean Series flagging imputed rows, tolerating missing flags."""
    if "is_imputed" not in frame.columns:
        return pd.Series(False, index=frame.index)
    return frame["is_imputed"].fillna(False).astype(bool)


def _build_forecast_figure(
    history: pd.DataFrame,
    forecast_value: float,
    lower_bound: float,
    upper_bound: float,
    as_of: pd.Timestamp,
    target: pd.Timestamp,
) -> go.Figure:
    """Compose the history + forecast chart with accessible series separation.

    Observed, imputed, and forecast points differ by marker symbol AND color AND
    legend label (never color alone); the interval renders as a shaded band.
    """
    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=[as_of, target, target, as_of],
            y=[lower_bound, lower_bound, upper_bound, upper_bound],
            fill="toself",
            fillcolor=_hex_to_rgba(ACCENT_HEX, 0.15),
            line={"color": _hex_to_rgba(ACCENT_HEX, 0.0), "width": 0},
            name="Prediction interval",
            hovertemplate=(
                "%{x|%d %b %Y}<br>Prediction interval bound: %{y:,.0f} INR/qtl"
                "<extra>Prediction interval</extra>"
            ),
        )
    )

    mask = _imputed_mask(history)
    observed = history.copy()
    observed.loc[mask, "modal_price_inr_qtl"] = float("nan")
    imputed = history[mask]

    figure.add_trace(
        go.Scatter(
            x=observed["date"],
            y=observed["modal_price_inr_qtl"],
            mode="lines+markers",
            line={"color": INK_HEX, "width": 2},
            marker={"symbol": "circle", "size": 5, "color": INK_HEX},
            name="Observed",
            connectgaps=False,
            hovertemplate="%{x|%d %b %Y}<br>Observed: %{y:,.0f} INR/qtl<extra>Observed</extra>",
        )
    )

    if not imputed.empty:
        figure.add_trace(
            go.Scatter(
                x=imputed["date"],
                y=imputed["modal_price_inr_qtl"],
                mode="markers",
                marker={
                    "symbol": "circle-open",
                    "size": 9,
                    "color": MUTED_HEX,
                    "line": {"width": 1.5},
                },
                name="Imputed observation",
                customdata=imputed["modal_price_inr_qtl"],
                hovertemplate=(
                    "%{x|%d %b %Y}<br>Imputed fill: %{customdata:,.0f} INR/qtl"
                    "<extra>Imputed observation</extra>"
                ),
            )
        )

    figure.add_trace(
        go.Scatter(
            x=[as_of, target],
            y=[forecast_value, forecast_value],
            mode="lines+markers",
            line={"color": ACCENT_HEX, "width": 2.5, "dash": "dash"},
            marker={
                "symbol": "diamond",
                "size": 10,
                "color": ACCENT_HEX,
                "line": {"color": ACCENT_INK_HEX, "width": 1},
            },
            name="7-day forecast",
            hovertemplate=(
                "%{x|%d %b %Y}<br>Forecast: %{y:,.0f} INR/qtl<extra>7-day forecast</extra>"
            ),
        )
    )

    figure.update_layout(**plotly_theme())
    figure.update_layout(
        height=440,
        hovermode="closest",
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02},
    )
    figure.update_xaxes(title_text="Date")
    figure.update_yaxes(title_text="Modal price (INR/qtl)")
    return figure


def _data_quality_note(panel: pd.DataFrame, market_id: object, as_of: pd.Timestamp) -> str:
    """Summarize missingness for one mandi over an explicitly stated window."""
    start, end = _window_for_as_of(as_of)
    rows = panel[
        (panel["market_id"] == market_id) & (panel["date"] >= start) & (panel["date"] <= end)
    ]
    scope = f"the last {HISTORY_WINDOW_DAYS} calendar days ending {format_date_iso(end)}"
    if rows.empty:
        rows = panel[panel["market_id"] == market_id]
        scope = "the full committed series"
        if rows.empty:
            return f"No clean-panel records exist for this mandi ({scope}: none found)."

    total = int(len(rows))
    imputed_count = int(_imputed_mask(rows).sum())
    unavailable_count = int(rows["modal_price_inr_qtl"].isna().sum())

    parts = [f"Window used: {scope}. Of {total} daily records in the clean panel,"]
    if unavailable_count > 0:
        parts.append(
            f" {unavailable_count} carry missing (null) modal prices and are omitted from the chart."
        )
    else:
        parts.append(" every record carries a finite modal price.")
    if imputed_count > 0:
        parts.append(
            f" {imputed_count} value{'s are' if imputed_count != 1 else ' is'} imputed fills,"
            " drawn as hollow markers."
        )
    return "".join(parts)


# ---------------------------------------------------------------------------
# Header: title, caption, frozen notice.
# ---------------------------------------------------------------------------
render_page_header(
    "Forecast evidence",
    "Inspect one Maharashtra onion mandi's recent wholesale prices beside its "
    "7-day forecast and prediction interval, with honest "
    "model-versus-baseline evidence and data-quality notes.",
)
render_frozen_notice()

# ---------------------------------------------------------------------------
# Load mandatory artifacts (missing forecasts stop inside load_forecasts).
# ---------------------------------------------------------------------------
forecasts_raw = load_forecasts()
if forecasts_raw.empty:
    st.warning(
        "The snapshot loaded successfully, but it contains no mandi forecast rows. "
        "See the Coverage page for data provenance."
    )
    st.stop()

forecast_frame = add_staleness_days(forecasts_raw)

with st.spinner("Loading supporting artifacts…"):
    panel = _load_panel_or_stop()
    mandi_metadata = _load_metadata_safe()

# ---------------------------------------------------------------------------
# Mandi selection persisted across reruns in session state.
# ---------------------------------------------------------------------------
mandi_options = available_mandis(forecast_frame)
freshness_reference = pd.to_datetime(forecast_frame["as_of_date"]).max()

if SELECT_KEY not in st.session_state or st.session_state[SELECT_KEY] not in mandi_options:
    default_name = _default_mandi_name(forecast_frame)
    st.session_state[SELECT_KEY] = default_name if default_name is not None else mandi_options[0]

selected_mandi: str = st.selectbox(
    "Choose a mandi",
    options=mandi_options,
    key=SELECT_KEY,
    help=(
        "As-of dates earlier than the freshness reference "
        f"({format_date_iso(freshness_reference)}) are flagged below."
    ),
)

row = _selected_forecast_row(forecast_frame, selected_mandi)
as_of_ts = pd.Timestamp(row["as_of_date"])
horizon_days = int(row["horizon_days"])
target_ts = as_of_ts + pd.Timedelta(days=horizon_days)
staleness_days = int(row["staleness_days"])

if staleness_days > 0:
    st.warning(
        f"This mandi's forecast is {staleness_days} days old relative to the "
        f"freshness reference ({format_date_iso(freshness_reference)}). It stays "
        "visible for transparency."
    )

# --- 5.2 (a) Mandi identity and forecast date -----------------------------
district = _district_for(mandi_metadata, row["market_id"])
identity_col, dates_col = st.columns([3, 2])
with identity_col:
    st.subheader(selected_mandi)
    district_line = f"{district} district, Maharashtra" if district != EM_DASH else "Maharashtra"
    st.caption(district_line)
with dates_col:
    st.caption(f"As-of: {format_date_iso(as_of_ts)} · Target: {format_date_iso(target_ts)}")

# --- 5.2 (b) Headline forecast price ---------------------------------------
confidence_level = float(row["confidence_level"])
interval_label = f"{confidence_level:.0%} prediction interval"
price_col, interval_col = st.columns(2)
with price_col:
    st.metric(
        f"{horizon_days}-day-ahead forecast price",
        format_inr_per_qtl(row["forecast_price_inr_qtl"]),
        help=f"As of {format_date_iso(as_of_ts)}, target {format_date_iso(target_ts)}.",
    )
with interval_col:
    st.caption(f"**{interval_label}**")
    st.markdown(f"**{format_interval(row['lower_bound_inr_qtl'], row['upper_bound_inr_qtl'])}**")
st.caption(
    f"Method: split-conformal at the {format_pct(confidence_level * 100, 0)} nominal "
    f"level. As-of {format_date_iso(as_of_ts)}, target {format_date_iso(target_ts)} "
    f"(as-of + {horizon_days} days). A prediction interval is a calibrated range, "
    "not a certainty."
)

# --- 5.2 (d) History + forecast chart --------------------------------------
render_section_heading(f"Price history and {horizon_days}-day forecast")

history_full = history_for_mandi(panel, row["market_id"])
window_start, window_end = _window_for_as_of(as_of_ts)
history_window = history_full[
    (history_full["date"] >= window_start) & (history_full["date"] <= window_end)
]

if history_window["modal_price_inr_qtl"].dropna().empty:
    st.warning(
        f"No plotted history: no finite observed prices exist in the "
        f"{HISTORY_WINDOW_DAYS}-day window ending {format_date_iso(as_of_ts)} for "
        "this mandi. Missing records remain flagged in the clean panel; see the "
        "Coverage page for provenance."
    )
else:
    figure = _build_forecast_figure(
        history=history_window,
        forecast_value=float(row["forecast_price_inr_qtl"]),
        lower_bound=float(row["lower_bound_inr_qtl"]),
        upper_bound=float(row["upper_bound_inr_qtl"]),
        as_of=as_of_ts,
        target=target_ts,
    )
    st.plotly_chart(figure, width="stretch")

# --- 5.2 (e) Model-versus-baseline evidence ---------------------------------
render_section_heading("Model-versus-baseline evidence")
st.markdown(f"Shipped forecaster: `{row['model_name']}` (version `{row['model_version']}`).")
st.caption(
    "LightGBM was trained honestly but did NOT beat the "
    "moving-average baseline on held-out test dates (test MAE 188 vs 140 "
    "INR/qtl), so the baseline ships."
)

sensitivity = load_baseline_sensitivity()
if sensitivity is not None and not sensitivity.empty:
    test_rows = sensitivity[sensitivity["split"] == "test"]
    if {"model", "mae"}.issubset(test_rows.columns) and not test_rows.empty:
        with st.expander("Baseline sensitivity — held-out test split"):
            comparison = test_rows[["model", "mae"]].copy()
            comparison["mae"] = comparison["mae"].map(lambda v: format_inr_per_qtl(v, 2))
            st.dataframe(
                comparison.rename(columns={"model": "Model", "mae": "Test MAE"}),
                hide_index=True,
                width="stretch",
            )
        st.caption("Lower test MAE wins. Only the best held-out performer ships to this page.")
    else:
        st.caption("Baseline-sensitivity artifact loaded, but holds no test-split rows.")
else:
    st.caption(
        "Baseline-sensitivity table not generated yet. Run the pipeline to produce "
        "`baseline_sensitivity_7d.csv`."
    )

# --- 5.2 (f) Missingness / data-quality note --------------------------------
render_section_heading("Data quality")
st.markdown(_data_quality_note(panel, row["market_id"], as_of_ts))

# --- 5.2 (g) Closing action --------------------------------------------------
if mandi_metadata is not None and not mandi_metadata.empty:
    m_match = mandi_metadata[mandi_metadata["market_id"] == row["market_id"]]
    if (
        not m_match.empty
        and "latitude" in m_match.columns
        and "longitude" in m_match.columns
        and pd.notna(m_match.iloc[0]["latitude"])
        and pd.notna(m_match.iloc[0]["longitude"])
    ):
        persist_decision_location(
            st.session_state,
            latitude=float(m_match.iloc[0]["latitude"]),
            longitude=float(m_match.iloc[0]["longitude"]),
        )

try:
    st.page_link(
        "pages/1_Decision.py",
        label="Use this mandi in the Decision workbench",
        icon=":material/arrow_forward:",
    )
except Exception:
    try:
        st.page_link(
            "1_Decision.py",
            label="Use this mandi in the Decision workbench",
            icon=":material/arrow_forward:",
        )
    except Exception as exc:
        st.warning(
            f"The Decision workbench link is unavailable in this host ({exc}). "
            "Open **Decision** from the sidebar to continue."
        )
