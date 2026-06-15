from __future__ import annotations

from datetime import timedelta

import pandas as pd

from mandipulse.recommend.engine import (
    compute_transport_cost_inr_qtl,
    haversine_km,
    score_recommendations,
)


def realized_net_price(
    panel: pd.DataFrame,
    market_id: int,
    target_date: pd.Timestamp,
    transport_cost_inr_qtl: float,
    tolerance_days: int = 2,
) -> float | None:
    """Return realized net price (INR/quintal) at target_date for market_id.

    Searches ±tolerance_days for an observed row. Prefers is_observed=True rows.
    Returns None if no usable row is found within the tolerance window.
    """
    mandi_rows = panel[panel["market_id"] == market_id].copy()
    if mandi_rows.empty:
        return None

    mandi_rows = mandi_rows.copy()
    mandi_rows["date"] = pd.to_datetime(mandi_rows["date"])
    window_start = target_date - timedelta(days=tolerance_days)
    window_end = target_date + timedelta(days=tolerance_days)
    window = mandi_rows[
        (mandi_rows["date"] >= window_start) & (mandi_rows["date"] <= window_end)
    ].copy()
    if window.empty:
        return None

    # Prefer observed rows; among those, pick the closest date to target_date
    observed = window[window["is_observed"].astype(bool)]
    candidates = observed if not observed.empty else window
    candidates = candidates.copy()
    candidates["date_dist"] = (candidates["date"] - target_date).abs()
    best = candidates.sort_values("date_dist").iloc[0]
    realized_price = float(best["modal_price_inr_qtl"])
    return realized_price - transport_cost_inr_qtl


def regret_at_k(
    ranked: pd.DataFrame,
    realized: dict[int, float],
    k: int,
) -> float | None:
    """Compute regret@K = best_realized_net_price - max(realized over top-K market_ids).

    Returns None if no realized prices are available for the top-K mandis.
    realized: {market_id -> realized_net_price_inr_qtl}
    ranked: DataFrame with 'market_id' and 'rank' columns, sorted by rank ascending.
    """
    if not realized:
        return None

    best_realized = max(realized.values())
    top_k_ids = ranked.sort_values("rank").head(k)["market_id"].tolist()
    top_k_realized = [realized[mid] for mid in top_k_ids if mid in realized]
    if not top_k_realized:
        return None

    return best_realized - max(top_k_realized)


def nearest_mandi_regret(
    realized: dict[int, float],
    farmer_lat: float,
    farmer_lon: float,
    mandis: pd.DataFrame,
) -> float | None:
    """Compute regret of the nearest-mandi baseline.

    nearest_mandi_regret = best_realized - realized_net_price(nearest mandi by airline distance).
    Returns None if nearest mandi has no realized price.
    mandis: DataFrame with market_id, latitude, longitude columns.
    """
    if not realized:
        return None

    best_realized = max(realized.values())

    candidate_mandis = mandis[
        mandis["market_id"].isin(realized)
        & mandis["latitude"].notna()
        & mandis["longitude"].notna()
    ].copy()
    if candidate_mandis.empty:
        return None

    candidate_mandis["air_dist_km"] = candidate_mandis.apply(
        lambda row: haversine_km(
            farmer_lat, farmer_lon, float(row["latitude"]), float(row["longitude"])
        ),
        axis=1,
    )
    nearest_id = int(candidate_mandis.sort_values("air_dist_km").iloc[0]["market_id"])
    nearest_realized = realized.get(nearest_id)
    if nearest_realized is None:
        return None

    return best_realized - nearest_realized


def summarize_backtest(backtest: pd.DataFrame, k_values: list[int]) -> dict:
    """Return headline backtest metrics as a flat dict (no I/O, no formatting).

    Keys per k in k_values: regret_at_{k}_mean, regret_at_{k}_median,
    optimal_rate_{k} (fraction top-K captured the best mandi, i.e. regret<=0),
    beats_nearest_{k} (fraction where regret_at_k < nearest_mandi_regret).
    Plus: nearest_mandi_regret_mean, nearest_mandi_regret_median,
    n_dates, date_min, date_max, n_dropped.
    Returns {} for an empty frame.
    """
    if backtest.empty:
        return {}

    result: dict = {}

    for k in k_values:
        col = f"regret_at_{k}"
        if col not in backtest.columns:
            continue
        valid = backtest[col].dropna()
        result[f"regret_at_{k}_mean"] = float(valid.mean()) if not valid.empty else float("nan")
        result[f"regret_at_{k}_median"] = float(valid.median()) if not valid.empty else float("nan")
        result[f"optimal_rate_{k}"] = (
            float((valid <= 0).mean()) if not valid.empty else float("nan")
        )
        both = backtest[[col, "nearest_mandi_regret"]].dropna()
        result[f"beats_nearest_{k}"] = (
            float((both[col] < both["nearest_mandi_regret"]).mean())
            if not both.empty
            else float("nan")
        )

    nm_regret = backtest["nearest_mandi_regret"].dropna()
    result["nearest_mandi_regret_mean"] = (
        float(nm_regret.mean()) if not nm_regret.empty else float("nan")
    )
    result["nearest_mandi_regret_median"] = (
        float(nm_regret.median()) if not nm_regret.empty else float("nan")
    )
    result["n_dates"] = len(backtest)
    result["date_min"] = str(backtest["as_of_date"].min())
    result["date_max"] = str(backtest["as_of_date"].max())
    result["n_dropped"] = int(backtest["n_dropped"].sum())

    return result


def backtest_recommendations(
    panel: pd.DataFrame,
    mandis: pd.DataFrame,
    predictions: pd.DataFrame,
    k_values: list[int],
    farmer_lat: float,
    farmer_lon: float,
    cost_per_km_per_quintal: float,
    road_distance_factor: float,
    uncertainty_penalty_weight: float,
    low_max_interval_pct: float,
    high_min_interval_pct: float,
    lower_residual: float,
    upper_residual: float,
) -> pd.DataFrame:
    """Backtest recommendations over leakage-safe per-as-of-date predictions.

    predictions: DataFrame with columns date, market_id, market_name, mandi_id,
                 target_price_t_plus_7, split, model, prediction.
                 One row per (date, market_id) — the moving-average baseline predictions.
    lower_residual/upper_residual: residuals from the calibration step (from
                 artifacts/metrics or the forecast_intervals report).

    Returns one row per as-of-date with regret@K for each k in k_values, nearest-mandi
    regret, and the chosen/best mandi names.
    Dropped mandis (no realized price within tolerance) are logged via the 'n_dropped' column.
    """
    panel = panel.copy()
    panel["date"] = pd.to_datetime(panel["date"])

    # Build a minimal forecasts DataFrame for score_recommendations from each date's predictions
    mandis_with_coords = mandis.dropna(subset=["latitude", "longitude"])

    rows = []
    n_scoring_failures = 0
    first_scoring_error: str | None = None
    for as_of_date, group in predictions.groupby("date"):
        as_of_date = pd.Timestamp(as_of_date)
        target_date = as_of_date + timedelta(days=7)

        # Build per-mandi forecast using the moving-average prediction at this as-of date
        forecast_rows = group.copy()
        forecast_rows["forecast_price_inr_qtl"] = forecast_rows["prediction"]
        forecast_rows["lower_bound_inr_qtl"] = forecast_rows["prediction"] + lower_residual
        forecast_rows["upper_bound_inr_qtl"] = forecast_rows["prediction"] + upper_residual
        forecast_rows["as_of_date"] = as_of_date.date().isoformat()
        forecast_rows["horizon_days"] = 7
        forecast_rows["confidence_level"] = 0.9
        forecast_rows["model_name"] = forecast_rows["model"]
        forecast_rows["model_version"] = "backtest"
        forecast_rows["forecast_id"] = [str(i) for i in range(len(forecast_rows))]
        forecast_rows["generated_at"] = as_of_date.isoformat()
        forecast_rows["crop"] = "onion"
        forecast_rows["crop_id"] = "onion"
        forecast_rows["state"] = "maharashtra"
        forecast_rows["mandi"] = forecast_rows["market_name"]

        # Only keep mandis that have coordinates
        forecast_for_scoring = forecast_rows[
            forecast_rows["market_id"].isin(mandis_with_coords["market_id"])
        ].copy()
        if forecast_for_scoring.empty:
            continue

        # score_recommendations pulls market_name/district_name from the mandis frame;
        # drop the prediction-side copies so the merge does not produce _x/_y suffixes.
        forecast_for_scoring = forecast_for_scoring.drop(
            columns=["market_name", "district"], errors="ignore"
        )

        try:
            ranked = score_recommendations(
                forecasts=forecast_for_scoring,
                mandis=mandis_with_coords,
                farmer_latitude=farmer_lat,
                farmer_longitude=farmer_lon,
                cost_per_km_per_quintal=cost_per_km_per_quintal,
                road_distance_factor=road_distance_factor,
                uncertainty_penalty_weight=uncertainty_penalty_weight,
                low_max_interval_pct=low_max_interval_pct,
                high_min_interval_pct=high_min_interval_pct,
                candidate_state="maharashtra",
            )
        except Exception as exc:  # noqa: BLE001 — surface, don't silently skip
            n_scoring_failures += 1
            if first_scoring_error is None:
                first_scoring_error = f"{type(exc).__name__}: {exc}"
            continue

        # Compute per-mandi transport cost for realized net price calculation
        realized: dict[int, float] = {}
        n_dropped = 0
        for _, mandi_row in mandis_with_coords.iterrows():
            mid = int(mandi_row["market_id"])
            air_dist = haversine_km(
                farmer_lat, farmer_lon, float(mandi_row["latitude"]), float(mandi_row["longitude"])
            )
            road_dist = air_dist * road_distance_factor
            tc = compute_transport_cost_inr_qtl(road_dist, cost_per_km_per_quintal)
            net = realized_net_price(panel, mid, target_date, tc)
            if net is None:
                n_dropped += 1
            else:
                realized[mid] = net

        if not realized:
            continue

        row: dict = {
            "as_of_date": as_of_date.date().isoformat(),
            "target_date": target_date.date().isoformat(),
            "n_mandis_ranked": len(ranked),
            "n_dropped": n_dropped,
        }

        best_realized = max(realized.values())
        best_market_id = max(realized, key=realized.__getitem__)
        best_mandi_name = (
            mandis_with_coords[mandis_with_coords["market_id"] == best_market_id][
                "market_name"
            ].iloc[0]
            if best_market_id in mandis_with_coords["market_id"].values
            else str(best_market_id)
        )

        row["best_realized_net_price"] = best_realized
        row["best_mandi"] = best_mandi_name

        for k in k_values:
            regret = regret_at_k(ranked, realized, k)
            row[f"regret_at_{k}"] = regret
            top1_id = int(ranked.sort_values("rank").iloc[0]["market_id"])
            row[f"top{k}_mandi"] = (
                ranked[ranked["market_id"] == top1_id]["mandi"].iloc[0] if k == 1 else None
            )

        nm_regret = nearest_mandi_regret(realized, farmer_lat, farmer_lon, mandis_with_coords)
        row["nearest_mandi_regret"] = nm_regret

        rows.append(row)

    if n_scoring_failures:
        raise RuntimeError(
            f"score_recommendations failed on {n_scoring_failures} as-of date(s); "
            f"first error: {first_scoring_error}"
        )

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows)
