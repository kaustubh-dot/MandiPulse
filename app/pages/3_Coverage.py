"""Coverage and provenance page — what the snapshot actually contains.

Mirrors the Next.js ``/coverage`` route under the Quiet Exchange
contract: snapshot range, explicit row definitions, a per-mandi comparability
table, a focused single-mandi view, trainability facts, and provenance report
links. Absence is reported as absence — missing mandi-days and missing artifacts
are never rendered as zeros.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pandas as pd  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

from mandipulse.app.data_access import (  # noqa: E402
    history_for_mandi,
    load_baseline_sensitivity,
    load_clean_panel,
    load_feature_table,
    load_interval_metadata,
    load_mandi_metadata,
    load_recommendation_backtest,
    load_report_markdown,
)
from mandipulse.app.design import (  # noqa: E402
    EM_DASH,
    INK_HEX,
    WARNING_HEX,
    format_date_iso,
    format_inr_per_qtl,
    format_pct,
    inject_base_css,
    plotly_theme,
    render_frozen_notice,
    render_page_header,
    render_section_heading,
)

st.set_page_config(page_title="Coverage · MandiPulse", layout="wide")
inject_base_css()

# How many recent rows the focused mandi view charts.
FOCUS_WINDOW_ROWS = 120

# The only model that ships; mirrors the held-out selection policy.
SHIPPED_MODEL = "moving_average_7d"

# One-line row definitions (wording aligned with docs/DATA_SCHEMA.md).
ROW_DEFINITIONS: tuple[tuple[str, str], ...] = (
    ("Observed", "`modal_price_inr_qtl` present in the source records; `is_imputed` is False."),
    ("Imputed", "Price present but pipeline-filled; flagged `is_imputed` True in the export."),
    (
        "Unavailable",
        "No observation exists for that mandi-day (`modal_price_inr_qtl` null); "
        "absence, never a zero price.",
    ),
    (
        "Trainable",
        "Feature-table row with `feature_row_valid == True`; its lookback window is satisfied.",
    ),
)


def _fmt_count(value: float) -> str:
    """Format a count with thousands separators (web ``formatCount`` parity)."""
    return f"{int(value):,}"


def _flag_series(frame: pd.DataFrame, column: str) -> pd.Series:
    """Return a boolean Series for a flag column, treating NaN as False."""
    return frame[column].fillna(False).astype(bool)


def _cell_text(value: object) -> str:
    """Text cell: trimmed string, or an em dash when absent."""
    try:
        if value is None or pd.isna(value):
            return EM_DASH
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    return text if text else EM_DASH


def _cell_count(value: object) -> str:
    """Count cell: grouped integer, or an em dash when absent."""
    try:
        if value is None or pd.isna(value):
            return EM_DASH
    except (TypeError, ValueError):
        return EM_DASH
    return _fmt_count(float(value))


def _cell_date(value: object) -> str:
    """Date cell routed through the shared ISO formatter."""
    try:
        missing = value is None or pd.isna(value)
    except (TypeError, ValueError):
        missing = False
    return EM_DASH if missing else format_date_iso(value)


def compute_mandi_coverage(panel: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    """Aggregate availability, imputation, and absence shares per mandi.

    Shares run over every row of the cleaned panel for each mandi. Unavailable
    rows are true absences (null modal price) and never count as zero prices.
    """
    price = pd.to_numeric(panel["modal_price_inr_qtl"], errors="coerce")
    imputed = _flag_series(panel, "is_imputed")
    available = price.notna()

    work = pd.DataFrame(
        {
            "market_id": panel["market_id"].astype(int),
            "market_name": panel["market_name"].astype(str),
            "date": pd.to_datetime(panel["date"], errors="coerce"),
            "available": available,
            "imputed": available & imputed,
        }
    )

    totals = work.groupby("market_id").agg(
        market_name=("market_name", "first"),
        total_rows=("available", "size"),
        available_rows=("available", "sum"),
        imputed_rows=("imputed", "sum"),
    )
    seen = work.loc[work["available"]].groupby("market_id")["date"].agg(["min", "max"])
    seen.columns = ["first_date", "last_date"]

    stats = totals.join(seen, how="left").reset_index()
    keep = [col for col in ("market_id", "district_name", "active_days") if col in meta.columns]
    stats = stats.merge(meta[keep], on="market_id", how="left")
    for optional_column in ("district_name", "active_days"):
        if optional_column not in stats.columns:
            stats[optional_column] = pd.NA

    stats["observed_rows"] = stats["available_rows"] - stats["imputed_rows"]
    stats["unavailable_rows"] = stats["total_rows"] - stats["available_rows"]
    denominator = stats["total_rows"].mask(stats["total_rows"] <= 0)
    stats["available_pct"] = stats["available_rows"] * 100 / denominator
    stats["imputed_pct"] = stats["imputed_rows"] * 100 / denominator
    stats["unavailable_pct"] = stats["unavailable_rows"] * 100 / denominator
    return stats


def coverage_display_frame(stats: pd.DataFrame) -> pd.DataFrame:
    """Pre-format coverage aggregates into display cells for ``st.dataframe``."""
    return pd.DataFrame(
        {
            "Mandi": stats["market_name"].map(_cell_text),
            "District": stats["district_name"].map(_cell_text),
            "First seen": stats["first_date"].map(_cell_date),
            "Last seen": stats["last_date"].map(_cell_date),
            "Active trading days": stats["active_days"].map(_cell_count),
            "Rows": stats["total_rows"].map(_cell_count),
            "Available": stats["available_pct"].map(format_pct),
            "Imputed": stats["imputed_pct"].map(format_pct),
            "Unavailable": stats["unavailable_pct"].map(format_pct),
        }
    )


def focus_window_chart(window: pd.DataFrame) -> go.Figure:
    """Chart one mandi's recent window, separating observed and imputed points.

    Missing prices contribute no points at all: gaps stay empty instead of
    being drawn as zero prices.
    """
    price = pd.to_numeric(window["modal_price_inr_qtl"], errors="coerce")
    dates = pd.to_datetime(window["date"], errors="coerce")
    imputed = _flag_series(window, "is_imputed") & price.notna()
    observed = price.notna() & ~imputed

    price_observed = price.copy()
    price_observed[~observed] = float("nan")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=price_observed,
            mode="lines+markers",
            name="Observed",
            line={"color": INK_HEX, "width": 1.5},
            marker={"color": INK_HEX, "size": 5},
            connectgaps=False,
            hovertemplate="%{x|%d %b %Y}<br>%{y:,.0f} INR/qtl<extra>Observed</extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=dates[imputed],
            y=price[imputed],
            mode="markers",
            name="Imputed",
            marker={"color": WARNING_HEX, "size": 8, "symbol": "diamond-open"},
            hovertemplate="%{x|%d %b %Y}<br>%{y:,.0f} INR/qtl<extra>Imputed</extra>",
        )
    )
    fig.update_layout(**plotly_theme())
    fig.update_layout(
        height=320,
        hovermode="closest",
        yaxis_title="Modal price (INR/qtl)",
        legend_orientation="h",
    )
    return fig


def render_missing_artifact_notice(expected_artifact: str, regenerate_command: str) -> None:
    """Report an optional artifact's absence honestly instead of faking values."""
    st.warning(
        f"**Artifact not generated:** `{expected_artifact}` is absent from this bundle.\n\n"
        f"Regenerate it with `{regenerate_command}` from the repository root.\n\n"
        "The related evidence stays omitted rather than shown as zeros."
    )


def render_trainability() -> None:
    """Summarize feature-table trainability, or say plainly why it cannot be."""
    render_section_heading("Trainability")
    try:
        features = load_feature_table()
    except Exception as exc:
        st.error(
            f"The feature table could not be loaded ({exc}). Regenerate it with "
            "`python scripts/build_feature_table.py`; trainable-row counts are omitted."
        )
        return

    if "feature_row_valid" not in features.columns:
        st.info(
            "The feature table loaded but carries no `feature_row_valid` column, so "
            "trainability cannot be counted. Regenerate it with "
            "`python scripts/build_feature_table.py`."
        )
        return

    valid = _flag_series(features, "feature_row_valid")
    total_rows = len(features)
    trainable_rows = int(valid.sum())
    dropped_rows = total_rows - trainable_rows
    st.markdown(
        "\n".join(
            [
                f"- **Feature-table rows:** {_fmt_count(total_rows)}",
                f"- **Trainable rows** (`feature_row_valid == True`): "
                f"{_fmt_count(trainable_rows)}",
                f"- **Dropped rows:** {_fmt_count(dropped_rows)}",
            ]
        )
    )
    st.caption(
        "A row is trainable when its lookback window before the feature date is satisfied; "
        "dropped rows carry insufficient history or missing lags."
    )


# ---------------------------------------------------------------------------
# Page header: title, snapshot label, frozen-data notice.
# ---------------------------------------------------------------------------
render_page_header(
    "Coverage and provenance",
    "Data coverage, trainability, and model evaluation provenance.",
)
render_frozen_notice()
st.caption(
    "Every figure elsewhere traces back to one fixed data bundle. This page shows how much of "
    "that bundle exists, where the gaps sit, and which artifacts produced each number. Absence "
    "is reported as absence: missing mandi-days are never filled with zeros."
)

with st.spinner("Loading coverage, mandi metadata, and price history…"):
    panel = load_clean_panel()
    try:
        mandi_meta = load_mandi_metadata()
    except Exception as exc:
        st.warning(
            f"Mandi metadata could not be loaded ({exc}). Coverage totals remain available, "
            "but district and active-trading-day context is omitted. Regenerate "
            "`data/external/mvp_mandis.csv`, then reload."
        )
        mandi_meta = pd.DataFrame(columns=["market_id", "district_name", "active_days"])

if panel.empty:
    st.warning(
        "**No coverage data is available in this snapshot.** The bundle loaded but holds no "
        "clean-panel rows, so per-mandi coverage cannot be computed. Reporting this as absence "
        "keeps zero values out of the evidence."
    )
    st.stop()

stats = compute_mandi_coverage(panel, mandi_meta)

# ---------------------------------------------------------------------------
# 1. Snapshot range (APP_FLOW 6.1-6.2).
# ---------------------------------------------------------------------------
render_section_heading("Snapshot range")
first_available = stats["first_date"].min()
last_available = stats["last_date"].max()
n_mandis = int(panel["market_id"].nunique())
total_panel_rows = len(panel)

st.markdown(
    "\n".join(
        [
            f"- **First available observation:** {format_date_iso(first_available)}",
            f"- **Last available observation:** {format_date_iso(last_available)}",
            f"- **Clean-panel rows:** {_fmt_count(total_panel_rows)} mandi-day rows",
            f"- **Mandis in scope:** {_fmt_count(n_mandis)} selected mandis "
            f"(top {n_mandis} by historical coverage)",
        ]
    )
)
st.caption(
    "Range reflects dates present in `data/processed/onion_maharashtra/clean_mandi_prices.csv`."
)

# ---------------------------------------------------------------------------
# 2. Row definitions (APP_FLOW 6.3).
# ---------------------------------------------------------------------------
render_section_heading("Row definitions")
st.markdown(
    "| Row kind | Definition |\n|---|---|\n"
    + "\n".join(f"| **{kind}** | {definition} |" for kind, definition in ROW_DEFINITIONS)
)

# ---------------------------------------------------------------------------
# 3. Per-mandi comparability (APP_FLOW 6.4).
# ---------------------------------------------------------------------------
render_section_heading("Per-mandi comparability")
st.caption(
    "Shares are computed over all rows of the clean panel for each mandi. Gaps stay comparable "
    "in place rather than hidden inside averages."
)
stats_sorted = stats.sort_values(
    ["active_days", "market_name"], ascending=[False, True], na_position="last"
)
st.dataframe(
    coverage_display_frame(stats_sorted),
    hide_index=True,
    width="stretch",
)

# ---------------------------------------------------------------------------
# 4. Mandi focus (APP_FLOW 6.5).
# ---------------------------------------------------------------------------
render_section_heading("Mandi focus")
name_by_id = dict(zip(stats["market_id"], stats["market_name"]))
district_by_id = dict(zip(stats["market_id"], stats["district_name"]))


def _mandi_label(market_id: int) -> str:
    """Selectbox label combining mandi and district names."""
    name = _cell_text(name_by_id.get(market_id, str(market_id)))
    district = _cell_text(district_by_id.get(market_id))
    if district == EM_DASH:
        return name
    return f"{name} — {district}"


ordered_ids = sorted(name_by_id, key=lambda market_id: str(name_by_id[market_id]))
focused_id = int(st.selectbox("Choose a mandi", ordered_ids, format_func=_mandi_label))

focus_stats = stats.loc[stats["market_id"] == focused_id].iloc[0]
focus_history = history_for_mandi(panel, focused_id)
focus_window = focus_history.tail(FOCUS_WINDOW_ROWS)
observed_share = focus_stats["available_pct"] - focus_stats["imputed_pct"]

st.markdown(
    f"**{_cell_text(focus_stats['market_name'])}** — " f"{_cell_text(focus_stats['district_name'])}"
)
st.markdown(
    "\n".join(
        [
            f"- First seen: {_cell_date(focus_stats['first_date'])} · "
            f"Last seen: {_cell_date(focus_stats['last_date'])} · "
            f"Active trading days: {_cell_count(focus_stats['active_days'])}",
            f"- Clean-panel rows: {_cell_count(focus_stats['total_rows'])} · "
            f"Observed: {_cell_count(focus_stats['observed_rows'])} "
            f"({format_pct(observed_share)})",
            f"- Imputed: {_cell_count(focus_stats['imputed_rows'])} "
            f"({format_pct(focus_stats['imputed_pct'])})",
            f"- Missing: {_cell_count(focus_stats['unavailable_rows'])} "
            f"({format_pct(focus_stats['unavailable_pct'])})",
            f"- Recent window charted: {_fmt_count(len(focus_window))} rows "
            f"(last {FOCUS_WINDOW_ROWS})",
        ]
    )
)
st.plotly_chart(focus_window_chart(focus_window), width="stretch")
st.caption(
    "Observed points use ink; imputed points use open diamonds in the warning hue. Gaps have "
    "no points: unavailable mandi-days are never rendered as zero prices."
)

# ---------------------------------------------------------------------------
# 5. Trainability summary.
# ---------------------------------------------------------------------------
render_trainability()

# ---------------------------------------------------------------------------
# 6. Model evidence availability — missing artifacts named honestly.
# ---------------------------------------------------------------------------
render_section_heading("Model evidence availability")

sensitivity = load_baseline_sensitivity()
st.markdown("#### Held-out model comparison")
if sensitivity is None:
    render_missing_artifact_notice(
        "artifacts/metrics/baseline_sensitivity_7d.csv",
        "python scripts/run_baseline_sensitivity_7d.py",
    )
else:
    test_rows = sensitivity[sensitivity["split"] == "test"]
    if {"model", "mae"}.issubset(test_rows.columns):
        comparison = pd.DataFrame(
            {
                "Model": test_rows["model"].map(_cell_text),
                "Held-out test MAE": test_rows["mae"].map(lambda v: format_inr_per_qtl(v, 2)),
                "Ships?": [
                    "Ships" if model == SHIPPED_MODEL else "Not shipped"
                    for model in test_rows["model"]
                ],
            }
        )
        st.dataframe(comparison, hide_index=True, width="stretch")
        st.caption(
            f"Lower MAE is better. `{SHIPPED_MODEL}` wins on the held-out test split, so only it "
            "ships to the forecast route; weaker families are shown, not hidden."
        )
    else:
        st.error("Missing required columns ('model', 'mae') in baseline sensitivity data.")

interval_meta = load_interval_metadata()
st.markdown("#### Prediction interval level")
if interval_meta is None:
    render_missing_artifact_notice(
        "artifacts/metrics/forecast_interval_metadata_7d.csv",
        "python scripts/build_forecast_intervals_7d.py",
    )
else:
    levels = sorted(set(interval_meta["confidence_level"].dropna()))
    if not levels:
        st.info("Interval metadata exists but carries no `confidence_level` values.")
    else:
        level_labels = ", ".join(format_pct(level * 100, 0) for level in levels)
        st.markdown(f"- **Nominal interval level:** {level_labels}")
        st.caption(
            "Empirical coverage on held-out dates is reported in the baseline metrics report."
        )

backtest = load_recommendation_backtest()
st.markdown("#### Ranking backtest")
if backtest is None:
    render_missing_artifact_notice(
        "artifacts/recommendations/recommendation_backtest_7d.csv",
        "python scripts/run_recommendation_backtest_7d.py",
    )
else:
    backtest_dates = pd.to_datetime(backtest["as_of_date"], errors="coerce").dropna()
    st.markdown(
        "\n".join(
            [
                f"- **Decision dates evaluated:** {_fmt_count(backtest_dates.nunique())}",
                f"- **Window:** {format_date_iso(backtest_dates.min())} – "
                f"{format_date_iso(backtest_dates.max())}",
                "- **Metric:** regret@1 against the best realized net price per decision date.",
            ]
        )
    )

# ---------------------------------------------------------------------------
# 7. Provenance and reports (APP_FLOW 6.6).
# ---------------------------------------------------------------------------
render_section_heading("Where these numbers come from")
st.markdown(
    "Modeling reports are committed under `reports/modeling/`. A missing report renders its "
    "fallback notice below instead of failing the page."
)
with st.expander("Baseline metrics report — reports/modeling/baseline_metrics_7d.md"):
    st.markdown(load_report_markdown("baseline_metrics_7d.md"))
with st.expander("Recommendation backtest report — reports/modeling/recommendation_backtest_7d.md"):
    st.markdown(load_report_markdown("recommendation_backtest_7d.md"))
