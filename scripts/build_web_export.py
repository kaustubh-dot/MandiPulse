from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mandipulse.config import load_yaml_config  # noqa: E402
from mandipulse.recommend.engine import score_recommendations  # noqa: E402
from mandipulse.utils.text import make_mandi_id  # noqa: E402

SAMPLE = Path("data/sample")
MANDIS_CSV = Path("data/external/mvp_mandis.csv")
OUT = Path("web/public/data")

DEFAULT_LAT = 19.99750
DEFAULT_LON = 73.78981

# Committed report numbers (from reports/modeling/*.md — do not recompute).
HONEST_RESULTS = [
    {"model": "moving_average_7d", "test_mae": 139.57, "ships": True},
    {"model": "ridge", "test_mae": 224.43, "ships": False},
    {"model": "lightgbm", "test_mae": 188.2, "ships": False},
    {"model": "lightgbm_residual", "test_mae": 195.63, "ships": False},
]

# Expected summary numbers from README — used for validation only.
_EXPECTED_REGRET_AT_1 = 296.3
_EXPECTED_NEAREST_REGRET = 370.1
_EXPECTED_PCT_BEATS = 78.8
_TOLERANCE = 5.0  # INR/qtl; flag if recomputed mean deviates more than this


def _dump(name: str, obj: object) -> None:
    path = OUT / name
    path.write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")
    size_kb = path.stat().st_size / 1024
    print(f"  wrote {name} ({size_kb:.1f} KB)")


def main() -> int:
    cfg = load_yaml_config("configs/recommendation.yaml")
    tc = cfg["transport_cost"]
    rk = cfg["ranking"]
    rt = cfg["risk_thresholds"]
    sens = cfg["sensitivity"]

    OUT.mkdir(parents=True, exist_ok=True)
    print("Building web/public/data/ JSON export from data/sample/ ...")

    # ------------------------------------------------------------------ load
    forecasts = pd.read_csv(SAMPLE / "forecast_outputs_7d.csv")
    prices = pd.read_csv(SAMPLE / "clean_mandi_prices.csv", parse_dates=["date"])
    backtest = pd.read_csv(SAMPLE / "recommendation_backtest_7d.csv")
    mandis_raw = pd.read_csv(MANDIS_CSV)

    # Enrich mandis with mandi_id (same logic as build_recommendations_7d.py)
    mandis_raw["mandi_id"] = mandis_raw["market_name"].fillna("").map(make_mandi_id)
    mandis_raw["district_name"] = mandis_raw["district_name"].fillna("")

    # Latest forecast per market_id (most recent as_of_date)
    latest = (
        forecasts.sort_values("as_of_date")
        .groupby("market_id", as_index=False)
        .tail(1)
    )

    # Default-location ranking via the same engine used by Streamlit/API
    ranked = score_recommendations(
        forecasts=latest,
        mandis=mandis_raw,
        farmer_latitude=DEFAULT_LAT,
        farmer_longitude=DEFAULT_LON,
        cost_per_km_per_quintal=float(tc["cost_per_km_per_quintal"]),
        road_distance_factor=float(tc["road_distance_factor"]),
        uncertainty_penalty_weight=float(rk["uncertainty_penalty_weight"]),
        low_max_interval_pct=float(rt["low_max_interval_pct"]) / 100,
        high_min_interval_pct=float(rt["high_min_interval_pct"]) / 100,
        candidate_state="maharashtra",
    )

    # ---------------------------------------------------------------- meta.json
    _dump(
        "meta.json",
        {
            "as_of_date": str(latest["as_of_date"].max()),
            "crop": "onion",
            "state": "maharashtra",
            "model_version": str(latest["model_name"].iloc[0]),
            "confidence_level": float(latest["confidence_level"].iloc[0]),
            "empirical_coverage": 0.8671,
            "default_farmer": {"latitude": DEFAULT_LAT, "longitude": DEFAULT_LON},
            "ranking": {
                "cost_per_km_per_quintal": float(tc["cost_per_km_per_quintal"]),
                "road_distance_factor": float(tc["road_distance_factor"]),
                "max_transport_radius_km": float(tc["max_transport_radius_km"]),
                "uncertainty_penalty_weight": float(rk["uncertainty_penalty_weight"]),
                "low_max_interval_pct": float(rt["low_max_interval_pct"]) / 100,
                "high_min_interval_pct": float(rt["high_min_interval_pct"]) / 100,
                "cost_variation_pct": float(sens["transport_cost_variation_pct"]),
            },
        },
    )

    # --------------------------------------------------------------- mandis.json
    mcols = ["market_id", "mandi_id", "market_name", "district_name", "latitude", "longitude", "active_days"]
    _dump("mandis.json", mandis_raw[mcols].to_dict("records"))

    # ------------------------------------------------------------- forecasts.json
    # risk_level is not in the CSV — attach it from the engine output.
    risk_map = ranked.set_index("market_id")["risk_level"].to_dict()
    flat = latest.copy()
    flat["risk_level"] = flat["market_id"].map(risk_map)
    fcols = [
        "market_id", "mandi_id", "mandi", "as_of_date",
        "forecast_price_inr_qtl", "lower_bound_inr_qtl", "upper_bound_inr_qtl",
        "confidence_level", "risk_level",
    ]
    _dump("forecasts.json", flat[fcols].round(4).to_dict("records"))

    # --------------------------------------------------------- recommendations.json
    rcols = [
        "rank", "market_id", "mandi_id", "mandi", "district_name",
        "forecast_price_inr_qtl", "lower_bound_inr_qtl", "upper_bound_inr_qtl",
        "estimated_transport_cost_inr_qtl", "expected_net_price_inr_qtl",
        "uncertainty_penalty_inr_qtl", "risk_adjusted_score", "risk_level",
        "air_distance_km", "road_distance_km", "reason",
    ]
    _dump("recommendations.json", ranked[rcols].round(4).to_dict("records"))

    # --------------------------------------------------------- price_history.json
    cutoff = prices["date"].max() - pd.Timedelta(days=180)
    recent = prices[prices["date"] >= cutoff].copy()
    recent["date"] = recent["date"].dt.strftime("%Y-%m-%d")
    pcols = ["market_id", "market_name", "date", "modal_price_inr_qtl", "is_imputed"]
    _dump("price_history.json", recent[pcols].to_dict("records"))

    # -------------------------------------------------------------- backtest.json
    regret_mean = float(backtest["regret_at_1"].mean())
    nearest_mean = float(backtest["nearest_mandi_regret"].mean())
    pct_beats = float((backtest["regret_at_1"] < backtest["nearest_mandi_regret"]).mean() * 100)

    # Validate against committed README numbers — flag drift, never silently mismatch.
    for label, computed, expected in [
        ("mean_regret_at_1", regret_mean, _EXPECTED_REGRET_AT_1),
        ("nearest_mandi_baseline_regret", nearest_mean, _EXPECTED_NEAREST_REGRET),
        ("pct_beats_nearest", pct_beats, _EXPECTED_PCT_BEATS),
    ]:
        if abs(computed - expected) > _TOLERANCE:
            print(
                f"  WARNING: {label} recomputed as {computed:.1f} "
                f"but README says {expected}. "
                f"Diff = {abs(computed - expected):.1f} > {_TOLERANCE}. "
                f"Check sample bundle or update README."
            )

    _dump(
        "backtest.json",
        {
            "mean_regret_at_1": round(regret_mean, 2),
            "nearest_mandi_baseline_regret": round(nearest_mean, 2),
            "pct_beats_nearest": round(pct_beats, 1),
            "n_dates_evaluated": int(len(backtest)),
            "test_window_start": str(backtest["as_of_date"].min()),
            "test_window_end": str(backtest["as_of_date"].max()),
        },
    )

    # --------------------------------------------------------- honest_results.json
    _dump("honest_results.json", HONEST_RESULTS)

    print("Done. 7 files written to web/public/data/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
