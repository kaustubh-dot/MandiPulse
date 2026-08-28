"""Shared Plotly composition for the Streamlit forecast endpoint view."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from mandipulse.app.design import (
    ACCENT_HEX,
    ACCENT_INK_HEX,
    INK_HEX,
    MUTED_HEX,
    RULE_HEX,
    SURFACE_HEX,
    plotly_theme,
)


def _imputed_mask(frame: pd.DataFrame) -> pd.Series:
    if "is_imputed" not in frame.columns:
        return pd.Series(False, index=frame.index)
    return frame["is_imputed"].fillna(False).astype(bool)


def build_forecast_figure(
    history: pd.DataFrame,
    forecast_value: float,
    lower_bound: float,
    upper_bound: float,
    as_of: pd.Timestamp,
    target: pd.Timestamp,
) -> go.Figure:
    """Compose continuous history and a separate target-only forecast lane."""
    plotted = history.copy()
    plotted["date"] = pd.to_datetime(plotted["date"], errors="coerce")
    plotted["modal_price_inr_qtl"] = pd.to_numeric(
        plotted["modal_price_inr_qtl"], errors="coerce"
    )
    plotted = plotted.dropna(subset=["date", "modal_price_inr_qtl"]).sort_values("date")

    mask = _imputed_mask(plotted)
    observed = plotted[~mask]
    imputed = plotted[mask]

    figure = make_subplots(
        rows=1,
        cols=2,
        shared_yaxes=True,
        column_widths=[0.78, 0.22],
        horizontal_spacing=0.08,
        subplot_titles=("Observed and imputed history", f"{target:%d %b} target"),
    )

    figure.add_trace(
        go.Scatter(
            x=plotted["date"],
            y=plotted["modal_price_inr_qtl"],
            mode="lines",
            line={"color": INK_HEX, "width": 2},
            name="Observed and imputed history",
            showlegend=False,
            connectgaps=False,
            hoverinfo="skip",
        ),
        row=1,
        col=1,
    )

    if not observed.empty:
        figure.add_trace(
            go.Scatter(
                x=observed["date"],
                y=observed["modal_price_inr_qtl"],
                mode="markers",
                marker={"symbol": "circle", "size": 5, "color": INK_HEX},
                name="Observed price",
                hovertemplate=(
                    "%{x|%d %b %Y}<br>Observed: %{y:,.0f} INR/qtl"
                    "<extra>Observed price</extra>"
                ),
            ),
            row=1,
            col=1,
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
                    "line": {"color": INK_HEX, "width": 1.5},
                },
                name="Imputed value",
                hovertemplate=(
                    "%{x|%d %b %Y}<br>Imputed fill: %{y:,.0f} INR/qtl"
                    "<extra>Imputed value</extra>"
                ),
            ),
            row=1,
            col=1,
        )

    figure.add_trace(
        go.Scatter(
            x=[target],
            y=[forecast_value],
            mode="markers+text",
            marker={
                "symbol": "diamond",
                "size": 12,
                "color": ACCENT_HEX,
                "line": {"color": ACCENT_INK_HEX, "width": 1},
            },
            text=[f"{forecast_value:,.0f}"],
            textposition="top center",
            textfont={"color": ACCENT_HEX, "family": "IBM Plex Mono, monospace"},
            error_y={
                "type": "data",
                "symmetric": False,
                "array": [upper_bound - forecast_value],
                "arrayminus": [forecast_value - lower_bound],
                "color": ACCENT_HEX,
                "thickness": 2,
                "width": 12,
                "visible": True,
            },
            name="7-day forecast",
            hovertemplate=(
                "%{x|%d %b %Y}<br>Forecast: %{y:,.0f} INR/qtl"
                f"<br>Prediction interval: {lower_bound:,.0f}–{upper_bound:,.0f} INR/qtl"
                "<extra>7-day forecast</extra>"
            ),
        ),
        row=1,
        col=2,
    )

    figure.update_layout(**plotly_theme())
    figure.update_layout(
        height=440,
        hovermode="closest",
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.12},
        margin={"l": 70, "r": 28, "t": 76, "b": 60},
    )
    figure.update_xaxes(title_text="Date", row=1, col=1)
    figure.update_xaxes(
        title_text="Forecast target",
        tickvals=[target],
        ticktext=[f"{target:%d %b}"],
        showgrid=False,
        linecolor=RULE_HEX,
        row=1,
        col=2,
    )
    figure.update_yaxes(title_text="Modal price (INR/qtl)", row=1, col=1)
    figure.update_yaxes(
        showgrid=True,
        gridcolor=RULE_HEX,
        linecolor=RULE_HEX,
        zeroline=False,
        row=1,
        col=2,
    )
    figure.update_layout(plot_bgcolor=SURFACE_HEX)
    return figure
