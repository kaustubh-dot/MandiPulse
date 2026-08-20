from __future__ import annotations

import json
import math
import sys
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mandipulse import __version__  # noqa: E402
from mandipulse.config import load_yaml_config  # noqa: E402
from mandipulse.policy import (  # noqa: E402
    FORECAST_AS_OF_POLICY,
    canonical_forecast_as_of,
    select_recommendation_candidates,
)
from mandipulse.recommend.engine import risk_level, score_recommendations  # noqa: E402
from mandipulse.utils.text import make_mandi_id  # noqa: E402
from scripts.validate_web_export import (  # noqa: E402
    ARTIFACT_SCHEMAS,
    DEFAULT_SCHEMA_DIR,
    sha256_file,
    validate_exports,
)

SAMPLE = Path("data/sample")
MANDIS_CSV = Path("data/external/mvp_mandis.csv")
CONFIG_PATH = Path("configs/recommendation.yaml")
OUT = Path("web/public/data")

BUNDLE_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"
DEFAULT_LAT = 19.99750
DEFAULT_LON = 73.78981
EMPIRICAL_COVERAGE = 0.8671
EMPIRICAL_COVERAGE_ROWS = 1204

# Canonical held-out values recorded in the committed modeling reports. The manifest hashes those
# reports so a report change invalidates the bundle until this export is intentionally regenerated.
HONEST_RESULTS = [
    {"model": "moving_average_7d", "test_mae": 139.57, "ships": True},
    {"model": "ridge", "test_mae": 224.43, "ships": False},
    {"model": "lightgbm", "test_mae": 188.2, "ships": False},
    {"model": "lightgbm_residual", "test_mae": 195.63, "ships": False},
]

PROVENANCE_INPUTS = [
    SAMPLE / "clean_mandi_prices.csv",
    SAMPLE / "forecast_outputs_7d.csv",
    SAMPLE / "recommendation_backtest_7d.csv",
    MANDIS_CSV,
    Path("reports/modeling/baseline_metrics_7d.md"),
    Path("reports/modeling/forecast_intervals_7d.md"),
    Path("reports/modeling/lightgbm_metrics_7d.md"),
    Path("reports/modeling/recommendation_backtest_7d.md"),
]


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("export contains a non-finite numeric value")
        return value
    raise TypeError(f"unsupported JSON export value: {type(value).__name__}")


def _write_json(directory: Path, name: str, obj: object) -> Path:
    path = directory / name
    payload = _json_ready(obj)
    path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _file_identity(path: Path) -> dict[str, Any]:
    return {
        "path": path.as_posix(),
        "sha256": sha256_file(PROJECT_ROOT / path),
        "bytes": (PROJECT_ROOT / path).stat().st_size,
    }


def _assert_one_value(frame: pd.DataFrame, column: str) -> Any:
    values = frame[column].dropna().unique().tolist()
    if len(values) != 1:
        raise ValueError(f"expected one {column} value, found {values}")
    return values[0]


def _build_manifest(
    staging: Path,
    payloads: dict[str, object],
    *,
    generated_at: str,
    snapshot_date: str,
    crop: str,
    state: str,
    horizon_days: int,
    canonical_as_of: str,
    forecast_rows: int,
    eligible_count: int,
    model_name: str,
    model_version: str,
    confidence_level: float,
) -> dict[str, Any]:
    artifacts: list[dict[str, Any]] = []
    for artifact_name in sorted(payloads):
        artifact_path = staging / artifact_name
        schema_name = ARTIFACT_SCHEMAS[artifact_name]
        instance = payloads[artifact_name]
        records = len(instance) if isinstance(instance, list) else 1
        artifacts.append(
            {
                "path": f"web/public/data/{artifact_name}",
                "schema_path": f"schemas/web_export/v1/{schema_name}",
                "schema_version": SCHEMA_VERSION,
                "sha256": sha256_file(artifact_path),
                "bytes": artifact_path.stat().st_size,
                "records": records,
            }
        )

    return {
        "manifest_version": "1.0.0",
        "bundle_version": BUNDLE_VERSION,
        "generated_at": generated_at,
        "snapshot": {
            "snapshot_date": snapshot_date,
            "crop": crop,
            "state": state,
            "forecast_horizon_days": horizon_days,
        },
        "as_of_policy": {
            "rule": FORECAST_AS_OF_POLICY,
            "canonical_as_of_date": canonical_as_of,
            "forecast_rows": forecast_rows,
            "eligible_count": eligible_count,
            "excluded_stale_count": forecast_rows - eligible_count,
        },
        "source": {
            "name": "CEDA/AGMARKNET",
            "mode": "committed_demo_snapshot",
        },
        "code": {
            "project_version": __version__,
            "generator_path": "scripts/build_web_export.py",
            "generator_sha256": sha256_file(PROJECT_ROOT / "scripts/build_web_export.py"),
        },
        "configuration": {
            "path": CONFIG_PATH.as_posix(),
            "sha256": sha256_file(PROJECT_ROOT / CONFIG_PATH),
        },
        "model": {
            "name": model_name,
            "version": model_version,
            "confidence_level": confidence_level,
            "empirical_coverage": EMPIRICAL_COVERAGE,
            "coverage_split": "test",
            "coverage_rows": EMPIRICAL_COVERAGE_ROWS,
        },
        "inputs": [_file_identity(path) for path in sorted(PROVENANCE_INPUTS)],
        "artifacts": artifacts,
        "validation": {
            "status": "passed",
            "strict_json": True,
            "schemas": True,
            "finite_numbers": True,
            "artifact_count": len(ARTIFACT_SCHEMAS),
        },
    }


def main() -> int:
    cfg = load_yaml_config(CONFIG_PATH)
    tc = cfg["transport_cost"]
    rk = cfg["ranking"]
    rt = cfg["risk_thresholds"]
    sens = cfg["sensitivity"]

    print("Building strict web/public/data JSON export from data/sample ...")
    forecasts = pd.read_csv(SAMPLE / "forecast_outputs_7d.csv")
    prices = pd.read_csv(SAMPLE / "clean_mandi_prices.csv", parse_dates=["date"])
    backtest = pd.read_csv(SAMPLE / "recommendation_backtest_7d.csv")
    mandis_raw = pd.read_csv(MANDIS_CSV)

    mandis_raw["mandi_id"] = mandis_raw["market_name"].fillna("").map(make_mandi_id)
    mandis_raw["district_name"] = mandis_raw["district_name"].fillna("")

    # Forecast views retain each market's most recent row. Recommendation candidates then apply the
    # shared, stricter bundle policy: only rows at the bundle-wide maximum as-of date are eligible.
    latest = forecasts.sort_values("as_of_date").groupby("market_id", as_index=False).tail(1)
    canonical_as_of = canonical_forecast_as_of(latest)
    eligible = select_recommendation_candidates(latest)

    ranked = score_recommendations(
        forecasts=eligible,
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
    ranked = ranked.merge(
        eligible[["market_id", "as_of_date"]],
        on="market_id",
        how="left",
        validate="one_to_one",
    )
    max_radius = float(tc["max_transport_radius_km"])
    max_alternatives = int(rk["max_alternatives"])
    ranked = ranked[ranked["road_distance_km"] <= max_radius].head(max_alternatives).copy()
    ranked["rank"] = range(1, len(ranked) + 1)

    snapshot_date = str(prices["date"].max().date())
    crop = str(_assert_one_value(latest, "crop"))
    state = str(_assert_one_value(latest, "state"))
    horizon_days = int(_assert_one_value(latest, "horizon_days"))
    model_name = str(_assert_one_value(latest, "model_name"))
    model_version = str(_assert_one_value(latest, "model_version"))
    confidence_level = float(_assert_one_value(latest, "confidence_level"))
    generated_at = pd.to_datetime(_assert_one_value(latest, "generated_at"), utc=True).isoformat()

    meta = {
        "as_of_date": canonical_as_of.isoformat(),
        "snapshot_date": snapshot_date,
        "forecast_horizon_days": horizon_days,
        "crop": crop,
        "state": state,
        "model_version": model_version,
        "confidence_level": confidence_level,
        "empirical_coverage": EMPIRICAL_COVERAGE,
        "candidate_policy": {
            "rule": FORECAST_AS_OF_POLICY,
            "eligible_as_of_date": canonical_as_of.isoformat(),
            "eligible_count": int(len(eligible)),
            "excluded_stale_count": int(len(latest) - len(eligible)),
        },
        "default_farmer": {"latitude": DEFAULT_LAT, "longitude": DEFAULT_LON},
        "ranking": {
            "cost_per_km_per_quintal": float(tc["cost_per_km_per_quintal"]),
            "road_distance_factor": float(tc["road_distance_factor"]),
            "max_transport_radius_km": max_radius,
            "max_alternatives": max_alternatives,
            "uncertainty_penalty_weight": float(rk["uncertainty_penalty_weight"]),
            "low_max_interval_pct": float(rt["low_max_interval_pct"]) / 100,
            "high_min_interval_pct": float(rt["high_min_interval_pct"]) / 100,
            "cost_variation_pct": float(sens["transport_cost_variation_pct"]),
        },
    }

    mcols = [
        "market_id",
        "mandi_id",
        "market_name",
        "district_name",
        "latitude",
        "longitude",
        "active_days",
    ]
    mandis = mandis_raw[mcols].to_dict("records")

    flat = latest.copy()
    relative_width = (flat["upper_bound_inr_qtl"] - flat["lower_bound_inr_qtl"]) / flat[
        "forecast_price_inr_qtl"
    ].clip(lower=1.0)
    flat["risk_level"] = relative_width.map(
        lambda width: risk_level(
            width,
            float(rt["low_max_interval_pct"]) / 100,
            float(rt["high_min_interval_pct"]) / 100,
        )
    )
    fcols = [
        "market_id",
        "mandi_id",
        "mandi",
        "as_of_date",
        "forecast_price_inr_qtl",
        "lower_bound_inr_qtl",
        "upper_bound_inr_qtl",
        "confidence_level",
        "risk_level",
    ]
    forecast_rows = flat[fcols].round(4).to_dict("records")

    rcols = [
        "rank",
        "market_id",
        "mandi_id",
        "mandi",
        "district_name",
        "as_of_date",
        "forecast_price_inr_qtl",
        "lower_bound_inr_qtl",
        "upper_bound_inr_qtl",
        "estimated_transport_cost_inr_qtl",
        "expected_net_price_inr_qtl",
        "uncertainty_penalty_inr_qtl",
        "risk_adjusted_score",
        "risk_level",
        "air_distance_km",
        "road_distance_km",
        "reason",
    ]
    recommendation_rows = ranked[rcols].round(4).to_dict("records")

    cutoff = prices["date"].max() - pd.Timedelta(days=180)
    recent = prices[prices["date"] >= cutoff].copy()
    recent["date"] = recent["date"].dt.strftime("%Y-%m-%d")
    # Missing observed prices are data absence, not zero. JSON null preserves that distinction while
    # remaining standards-compliant and is explicitly allowed only for this numeric field's schema.
    recent["modal_price_inr_qtl"] = (
        recent["modal_price_inr_qtl"]
        .astype(object)
        .where(recent["modal_price_inr_qtl"].notna(), None)
    )
    pcols = ["market_id", "market_name", "date", "modal_price_inr_qtl", "is_imputed"]
    price_history = recent[pcols].to_dict("records")

    regret_mean = float(backtest["regret_at_1"].mean())
    nearest_mean = float(backtest["nearest_mandi_regret"].mean())
    pct_beats = float((backtest["regret_at_1"] < backtest["nearest_mandi_regret"]).mean() * 100)
    backtest_summary = {
        # Preserve enough source precision for the frontend's one-decimal display; rounding to
        # two decimals here can double-round 296.346... to 296.4 instead of the documented 296.3.
        "mean_regret_at_1": round(regret_mean, 4),
        "nearest_mandi_baseline_regret": round(nearest_mean, 4),
        "pct_beats_nearest": round(pct_beats, 1),
        "n_dates_evaluated": int(len(backtest)),
        "test_window_start": str(backtest["as_of_date"].min()),
        "test_window_end": str(backtest["as_of_date"].max()),
    }

    payloads: dict[str, object] = {
        "backtest.json": backtest_summary,
        "forecasts.json": forecast_rows,
        "honest_results.json": HONEST_RESULTS,
        "mandis.json": mandis,
        "meta.json": meta,
        "price_history.json": price_history,
        "recommendations.json": recommendation_rows,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".mandipulse-web-export-", dir=OUT.parent) as tmp:
        staging = Path(tmp)
        for name, payload in payloads.items():
            _write_json(staging, name, payload)
        manifest = _build_manifest(
            staging,
            payloads,
            generated_at=generated_at,
            snapshot_date=snapshot_date,
            crop=crop,
            state=state,
            horizon_days=horizon_days,
            canonical_as_of=canonical_as_of.isoformat(),
            forecast_rows=len(latest),
            eligible_count=len(eligible),
            model_name=model_name,
            model_version=model_version,
            confidence_level=confidence_level,
        )
        _write_json(staging, "manifest.json", manifest)
        results = validate_exports(staging, DEFAULT_SCHEMA_DIR, PROJECT_ROOT)

        OUT.mkdir(parents=True, exist_ok=True)
        for artifact_name in ARTIFACT_SCHEMAS:
            (staging / artifact_name).replace(OUT / artifact_name)

    for result in results:
        size_kb = (OUT / result["artifact"]).stat().st_size / 1024
        print(f"  PASS {result['artifact']} ({size_kb:.1f} KB)")
    print(f"Done. {len(results)}/{len(ARTIFACT_SCHEMAS)} strict JSON artifacts validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
