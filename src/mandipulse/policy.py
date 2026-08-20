from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pandas as pd


FORECAST_AS_OF_POLICY = "as_of_equals_bundle_max"


def _parse_date_series(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        raise ValueError(f"Missing required date column: {column}.")
    if frame.empty:
        raise ValueError("Forecast data is empty.")

    parsed = pd.to_datetime(frame[column], errors="coerce")
    if parsed.isna().any():
        raise ValueError(f"Column {column} contains an invalid or missing date.")
    return parsed


def _parse_date(value: Any, *, label: str) -> date:
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        raise ValueError(f"{label} must be a valid date.")
    return parsed.date()


def canonical_forecast_as_of(
    forecasts: pd.DataFrame,
    *,
    column: str = "as_of_date",
) -> date:
    """Return the bundle-wide canonical forecast origin.

    Phase 1 freezes the public policy as the maximum valid ``as_of_date`` in
    the forecast bundle.
    """

    return _parse_date_series(forecasts, column).max().date()


def select_recommendation_candidates(
    forecasts: pd.DataFrame,
    *,
    column: str = "as_of_date",
) -> pd.DataFrame:
    """Return forecasts eligible under ``as_of_equals_bundle_max``."""

    parsed = _parse_date_series(forecasts, column)
    canonical = parsed.max().date()
    eligible = forecasts.loc[parsed.dt.date == canonical].copy()
    if eligible.empty:
        raise ValueError("No forecasts are eligible at the canonical as-of date.")
    return eligible


def select_latest_forecast_for_market(
    forecasts: pd.DataFrame,
    market_id: Any,
    *,
    market_column: str = "market_id",
    as_of_column: str = "as_of_date",
) -> pd.Series:
    """Return a market's latest row, even when it predates the bundle maximum."""

    if market_column not in forecasts.columns:
        raise ValueError(f"Missing required market column: {market_column}.")
    matches = forecasts.loc[forecasts[market_column] == market_id]
    if matches.empty:
        raise ValueError(f"No forecast is available for market_id={market_id}.")
    parsed = _parse_date_series(matches, as_of_column)
    return matches.loc[parsed.idxmax()].copy()


def cap_history_at_as_of(
    history: pd.DataFrame,
    as_of_date: Any,
    *,
    date_column: str = "date",
) -> pd.DataFrame:
    """Keep only observations available on or before a forecast origin."""

    if date_column not in history.columns:
        raise ValueError(f"Missing required date column: {date_column}.")
    if history.empty:
        return history.copy()
    parsed = pd.to_datetime(history[date_column], errors="coerce")
    if parsed.isna().any():
        raise ValueError(f"Column {date_column} contains an invalid or missing date.")
    cutoff = _parse_date(as_of_date, label="as_of_date")
    return history.loc[parsed.dt.date <= cutoff].copy()


def forecast_target_date(as_of_date: Any, horizon_days: int) -> date:
    """Return the target date implied by a forecast origin and horizon."""

    if isinstance(horizon_days, bool) or not isinstance(horizon_days, int) or horizon_days <= 0:
        raise ValueError("horizon_days must be a positive integer.")
    return _parse_date(as_of_date, label="as_of_date") + timedelta(days=horizon_days)
