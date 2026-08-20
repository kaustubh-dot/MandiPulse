from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mandipulse.modeling.baselines import predict_baselines  # noqa: E402
from mandipulse.modeling.metrics import metric_row  # noqa: E402
from mandipulse.modeling.phase3 import (  # noqa: E402
    adopt_interval_method,
    canonical_hash,
    compare_interval_methods,
    observed_target_mask,
    sha256_file,
    target_population_counts,
)
from mandipulse.modeling.splits import (  # noqa: E402
    RollingOriginSplit,
    SplitConfig,
    load_trainable_features,
    make_rolling_origin_splits,
    make_temporal_splits,
)
from mandipulse.paths import clean_panel_path, feature_table_path, mvp_mandis_path  # noqa: E402
from mandipulse.recommend.evaluation import (  # noqa: E402
    backtest_recommendations,
    summarize_backtest,
)
from mandipulse.utils.formatting import dataframe_to_markdown  # noqa: E402
from mandipulse.utils.text import make_mandi_id, slugify  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the deterministic Phase 3 leakage, holdout, interval, and recommendation evaluation."
    )
    parser.add_argument("--features", default=str(feature_table_path()))
    parser.add_argument("--panel", default=str(clean_panel_path()))
    parser.add_argument("--mandis", default=str(mvp_mandis_path()))
    parser.add_argument("--config", default="configs/recommendation.yaml")
    parser.add_argument("--report", default="reports/modeling/phase3_evaluation.md")
    parser.add_argument("--json-output", default="reports/modeling/phase3_evaluation.json")
    parser.add_argument("--model", default="moving_average_7d")
    parser.add_argument("--n-origins", type=int, default=3)
    parser.add_argument("--rolling-validation-days", type=int, default=30)
    parser.add_argument("--rolling-test-days", type=int, default=7)
    parser.add_argument("--final-holdout-days", type=int, default=90)
    parser.add_argument("--horizon-days", type=int, default=7)
    parser.add_argument("--confidence-level", type=float, default=0.90)
    return parser.parse_args()


def load_mandi_metadata(path: Path) -> pd.DataFrame:
    mandis = pd.read_csv(path)
    mandis["state"] = "maharashtra"
    mandis["mandi"] = mandis["market_name"].fillna("").map(slugify)
    mandis["mandi_id"] = mandis["market_name"].fillna("").map(make_mandi_id)
    return mandis


def attach_target_flags(predictions: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
    flags = features[
        [
            "date",
            "market_id",
            "is_observed",
            "is_imputed",
            "target_observed_t_plus_7",
            "target_imputed_t_plus_7",
        ]
    ].copy()
    flags["date"] = pd.to_datetime(flags["date"])
    result = predictions.copy()
    result["date"] = pd.to_datetime(result["date"])
    result = result.merge(
        flags,
        on=["date", "market_id"],
        how="left",
        validate="many_to_one",
    )
    if result[["is_observed", "target_observed_t_plus_7"]].isna().any().any():
        raise ValueError("Prediction rows could not be reconciled to target eligibility flags")
    return result


def frame_metric(predictions: pd.DataFrame, *, model: str, split: str) -> dict[str, object]:
    selected = predictions[(predictions["model"] == model) & (predictions["split"] == split)].copy()
    counts = target_population_counts(selected)
    observed = selected[observed_target_mask(selected)]
    if observed.empty:
        raise ValueError(f"No observed target rows for model={model}, split={split}")
    row = metric_row(
        model_name=model,
        split_name=split,
        y_true=observed["target_price_t_plus_7"],
        y_pred=observed["prediction"],
        scale=float("nan"),
    )
    row["mase"] = None
    row.update(
        {
            "population": "observed_targets",
            "observed_target_rows": counts["observed_target_rows"],
            "imputed_target_rows_excluded": counts["imputed_target_rows"],
            "unavailable_target_rows": counts["unavailable_target_rows"],
        }
    )
    return row


def dates_record(split: RollingOriginSplit, frame: pd.DataFrame) -> dict[str, object]:
    train, validation, test = split.select(frame)
    return {
        "origin_date": split.origin_date.date().isoformat(),
        "train_start": split.dates.train_start.date().isoformat(),
        "train_end": split.dates.train_end.date().isoformat(),
        "validation_start": split.dates.validation_start.date().isoformat(),
        "validation_end": split.dates.validation_end.date().isoformat(),
        "test_start": split.dates.test_start.date().isoformat(),
        "test_end": split.dates.test_end.date().isoformat(),
        "train": {"rows": len(train), **target_population_counts(train)},
        "validation": {"rows": len(validation), **target_population_counts(validation)},
        "test": {"rows": len(test), **target_population_counts(test)},
    }


def _summary_row(
    *,
    origin: str,
    multiplier: float,
    cost_per_km: float,
    summary: dict[str, object],
    provenance_id: str,
) -> dict[str, object]:
    return {
        "origin": origin,
        "transport_cost_multiplier": multiplier,
        "cost_per_km_per_quintal": cost_per_km,
        "realized_target_population": "observed_only",
        "provenance_id": provenance_id,
        **summary,
    }


def _json_safe(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if np.isfinite(value) else None
    if value is pd.NA:
        return None
    if pd.isna(value) if not isinstance(value, (str, bool, int, Path)) else False:
        return None
    return value


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_json_safe(payload), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def write_report(path: Path, payload: dict[str, object]) -> None:
    interval = pd.DataFrame(payload["interval_comparison"])
    rolling_interval = pd.DataFrame(payload["rolling_interval_comparison"])
    metrics = pd.DataFrame(payload["final_holdout"]["metrics"])
    scenarios = pd.DataFrame(payload["recommendation_backtest"]["scenario_summary"])
    lines = [
        "# Phase 3 - Defensible ML Engineering Evidence",
        "",
        "## Scope and population policy",
        "",
        "- Frozen scope: Onion/Maharashtra, 15 mandis, 7-day horizon, snapshot through 2025-10-30.",
        "- Primary metric population: rows whose as-of value and t+7 target are observed.",
        "- Imputed targets are counted and excluded from primary metrics; unavailable targets are reported separately.",
        "- Rolling origins are evaluated before an untouched final holdout. The final holdout is evaluated last.",
        "- This is an internal evaluation evidence export; the public web/API v1 schemas remain unchanged.",
        "",
        "## Provenance",
        "",
        f"- Evidence provenance id: {payload['provenance_id']}",
        f"- Source snapshot: {payload['provenance']['source_data']['path']} ({payload['provenance']['source_data']['sha256']})",
        f"- Feature snapshot: {payload['provenance']['feature_table']['path']} ({payload['provenance']['feature_table']['sha256']})",
        f"- Coordinate source: {payload['provenance']['coordinates']['path']} ({payload['provenance']['coordinates']['sha256']})",
        f"- Transport config: {payload['provenance']['transport']}",
        "",
        "## Rolling origins",
        "",
        dataframe_to_markdown(pd.DataFrame(payload["rolling_origins"])),
        "",
        "## Untouched final holdout",
        "",
        f"- Definition: {payload['final_holdout']['definition']}",
        f"- Dates: {payload['final_holdout']['dates']['test_start']} to {payload['final_holdout']['dates']['test_end']}",
        f"- Test population counts: {payload['final_holdout']['dates']['test']}",
        "",
        dataframe_to_markdown(metrics),
        "",
        "## Conditional versus split-conformal intervals",
        "",
        dataframe_to_markdown(interval),
        "",
        "- Failure-mode comparison is explicit: undercoverage, coverage shortfall, excluded imputed/unavailable rows, and width tradeoffs are recorded for each candidate.",
        "",
        f"- Adopted method: {payload['interval_adoption']['method']}",
        f"- Adoption rule: {payload['interval_adoption']['rule']}",
        "",
        "## Rolling-origin interval calibration",
        "",
        "Each rolling origin calibrates its interval bounds on that origin's observed validation targets. The adopted method is fixed by the final comparison; holdout-derived bounds are not reused backward.",
        "",
        dataframe_to_markdown(rolling_interval),
        "",
        "## Multi-origin transport backtest",
        "",
        "Each scenario first applies the observed-target mask. Target-ineligible rows, coordinate exclusions, and realized-target drops are counted per as-of date; the realized lookup uses the declared matching tolerance only after eligibility is established.",
        "",
        dataframe_to_markdown(scenarios),
        "",
        "## Reproduction",
        "",
        "    python scripts/run_phase3_evaluation.py",
        "",
        "The JSON companion is strict JSON (no NaN/Infinity) and contains the complete split, denominator, interval, scenario, and provenance records.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    feature_path = Path(args.features)
    panel_path = Path(args.panel)
    mandis_path = Path(args.mandis)
    config_path = Path(args.config)
    features = load_trainable_features(feature_path)
    panel = pd.read_csv(panel_path)
    mandis = load_mandi_metadata(mandis_path)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    transport = config.get("transport_cost", {})
    ranking = config.get("ranking", {})
    thresholds = config.get("risk_thresholds", {})

    rolling_config = SplitConfig(
        validation_days=args.rolling_validation_days,
        test_days=args.rolling_test_days,
        horizon_days=args.horizon_days,
    )
    final_config = SplitConfig(
        validation_days=90,
        test_days=args.final_holdout_days,
        horizon_days=args.horizon_days,
    )
    origins = make_rolling_origin_splits(
        features,
        rolling_config,
        n_origins=args.n_origins,
        final_holdout_days=args.final_holdout_days,
    )

    final_train, final_validation, final_test, final_dates = make_temporal_splits(
        features, final_config
    )
    final_predictions = attach_target_flags(
        predict_baselines(final_train, final_validation, final_test, ridge_alpha=1.0), features
    )
    final_metrics = [frame_metric(final_predictions, model=args.model, split="test")]
    interval_comparison = compare_interval_methods(
        final_predictions,
        model_name=args.model,
        confidence_level=args.confidence_level,
        observed_only=True,
    )
    adopted_method, adoption_rule = adopt_interval_method(interval_comparison)
    adopted_row = interval_comparison[interval_comparison["method"] == adopted_method].iloc[0]

    rolling_records: list[dict[str, object]] = []
    rolling_predictions: list[tuple[str, pd.DataFrame, dict[str, object]]] = []
    rolling_interval_comparison: list[dict[str, object]] = []
    rolling_interval_bounds: list[dict[str, object]] = []
    for index, origin in enumerate(origins, start=1):
        origin_name = f"rolling_{index}"
        train, validation, test = origin.select(features)
        predictions = attach_target_flags(
            predict_baselines(train, validation, test, ridge_alpha=1.0), features
        )
        origin_comparison = compare_interval_methods(
            predictions,
            model_name=args.model,
            confidence_level=args.confidence_level,
            observed_only=True,
        )
        origin_row = origin_comparison[origin_comparison["method"] == adopted_method].iloc[0]
        origin_bounds: dict[str, object] = {
            "origin_id": origin_name,
            "method": adopted_method,
            "lower_residual": float(origin_row["lower_residual"]),
            "upper_residual": float(origin_row["upper_residual"]),
            "calibration_rows": int(origin_row["calibration_rows"]),
        }
        rolling_interval_bounds.append(origin_bounds)
        rolling_interval_comparison.extend(
            [
                {"origin_id": origin_name, **row}
                for row in origin_comparison.to_dict(orient="records")
            ]
        )
        rolling_records.append(
            {
                "origin_id": origin_name,
                **dates_record(origin, features),
                "metrics": [frame_metric(predictions, model=args.model, split="test")],
                "interval": origin_bounds,
            }
        )
        rolling_predictions.append(
            (
                origin_name,
                predictions[
                    (predictions["model"] == args.model) & (predictions["split"] == "test")
                ].copy(),
                origin_bounds,
            )
        )

    provenance = {
        "snapshot": {
            "crop": "onion",
            "state": "maharashtra",
            "horizon_days": args.horizon_days,
            "source_max_date": str(pd.to_datetime(panel["date"]).max().date()),
        },
        "source_data": {"path": panel_path.as_posix(), "sha256": sha256_file(panel_path)},
        "feature_table": {"path": feature_path.as_posix(), "sha256": sha256_file(feature_path)},
        "coordinates": {"path": mandis_path.as_posix(), "sha256": sha256_file(mandis_path)},
        "transport": {
            "road_distance_factor": float(transport.get("road_distance_factor", 1.3)),
            "base_cost_per_km_per_quintal": float(transport.get("cost_per_km_per_quintal", 4.0)),
            "scenario_multipliers": [0.8, 1.0, 1.2],
        },
        "model": {"name": args.model, "version": "phase3_baseline_v1"},
        "interval": {
            "confidence_level": args.confidence_level,
            "calibration_population": "observed_targets",
            "evaluation_population": "observed_targets",
            "adopted_method": adopted_method,
            "adoption_rule": adoption_rule,
            "lower_residual": float(adopted_row["lower_residual"]),
            "upper_residual": float(adopted_row["upper_residual"]),
        },
        "recommendation": {
            "target_population": "observed_targets",
            "observed_definition": "is_observed and target_observed_t_plus_7",
            "target_matching_tolerance_days": 2,
            "coordinate_exclusions": "counted per as-of date",
        },
        "rolling_interval_bounds": rolling_interval_bounds,
        "evaluation_protocol": {
            "rolling_origins": args.n_origins,
            "rolling_validation_days": args.rolling_validation_days,
            "rolling_test_days": args.rolling_test_days,
            "final_holdout_days": args.final_holdout_days,
            "horizon_days": args.horizon_days,
        },
        "configuration": {"path": config_path.as_posix(), "sha256": sha256_file(config_path)},
    }
    provenance_id = canonical_hash(provenance)
    interval_comparison["provenance_id"] = provenance_id
    for record in rolling_records:
        record["provenance_id"] = provenance_id
        record["interval"] = {**record["interval"], "provenance_id": provenance_id}
        for metric in record["metrics"]:
            metric["provenance_id"] = provenance_id
    for row in rolling_interval_comparison:
        row["provenance_id"] = provenance_id
    for metric in final_metrics:
        metric["provenance_id"] = provenance_id

    mandis_with_coords = mandis.dropna(subset=["latitude", "longitude"])
    scenario_summary: list[dict[str, object]] = []
    scenario_rows: list[dict[str, object]] = []
    base_cost = float(transport.get("cost_per_km_per_quintal", 4.0))
    road_factor = float(transport.get("road_distance_factor", 1.3))
    for origin_name, predictions, origin_bounds in rolling_predictions:
        for multiplier in (0.8, 1.0, 1.2):
            backtest = backtest_recommendations(
                panel=panel,
                mandis=mandis_with_coords,
                predictions=predictions,
                k_values=[1, 3],
                farmer_lat=19.99750,
                farmer_lon=73.78981,
                cost_per_km_per_quintal=base_cost * multiplier,
                road_distance_factor=road_factor,
                uncertainty_penalty_weight=float(ranking.get("uncertainty_penalty_weight", 0.3)),
                low_max_interval_pct=float(thresholds.get("low_max_interval_pct", 10)) / 100,
                high_min_interval_pct=float(thresholds.get("high_min_interval_pct", 25)) / 100,
                lower_residual=float(origin_bounds["lower_residual"]),
                upper_residual=float(origin_bounds["upper_residual"]),
                observed_target_only=True,
            )
            summary = summarize_backtest(backtest, [1, 3])
            summary_row = _summary_row(
                origin=origin_name,
                multiplier=multiplier,
                cost_per_km=base_cost * multiplier,
                summary=summary,
                provenance_id=provenance_id,
            )
            summary_row.update(
                {
                    "interval_method": origin_bounds["method"],
                    "lower_residual": origin_bounds["lower_residual"],
                    "upper_residual": origin_bounds["upper_residual"],
                    "target_matching_tolerance_days": 2,
                }
            )
            scenario_summary.append(summary_row)
            if not backtest.empty:
                scenario_frame = backtest.copy()
                scenario_frame["origin"] = origin_name
                scenario_frame["transport_cost_multiplier"] = multiplier
                scenario_frame["cost_per_km_per_quintal"] = base_cost * multiplier
                scenario_frame["provenance_id"] = provenance_id
                scenario_frame["interval_method"] = origin_bounds["method"]
                scenario_frame["lower_residual"] = origin_bounds["lower_residual"]
                scenario_frame["upper_residual"] = origin_bounds["upper_residual"]
                scenario_frame["target_matching_tolerance_days"] = 2
                scenario_rows.extend(scenario_frame.to_dict(orient="records"))

    final_holdout_dates = {
        "train_start": final_dates.train_start.date().isoformat(),
        "train_end": final_dates.train_end.date().isoformat(),
        "validation_start": final_dates.validation_start.date().isoformat(),
        "validation_end": final_dates.validation_end.date().isoformat(),
        "test_start": final_dates.test_start.date().isoformat(),
        "test_end": final_dates.test_end.date().isoformat(),
        "train": {"rows": len(final_train), **target_population_counts(final_train)},
        "validation": {
            "rows": len(final_validation),
            **target_population_counts(final_validation),
        },
        "test": {"rows": len(final_test), **target_population_counts(final_test)},
    }
    payload: dict[str, object] = {
        "schema_version": "phase3_evaluation.v1",
        "provenance_id": provenance_id,
        "provenance": provenance,
        "population_policy": {
            "primary": "observed_targets",
            "observed_definition": "is_observed and target_observed_t_plus_7",
            "imputed_targets": "excluded and counted",
            "unavailable_targets": "excluded and counted",
        },
        "rolling_origins": rolling_records,
        "rolling_interval_comparison": rolling_interval_comparison,
        "final_holdout": {
            "definition": "last 90 days of trainable as-of rows, evaluated after rolling origins",
            "dates": final_holdout_dates,
            "metrics": [dict(row, provenance_id=provenance_id) for row in final_metrics],
        },
        "interval_comparison": interval_comparison.to_dict(orient="records"),
        "interval_adoption": {
            "method": adopted_method,
            "rule": adoption_rule,
            "lower_residual": float(adopted_row["lower_residual"]),
            "upper_residual": float(adopted_row["upper_residual"]),
            "provenance_id": provenance_id,
        },
        "recommendation_backtest": {
            "scenario_multipliers": [0.8, 1.0, 1.2],
            "target_population": "observed_targets",
            "target_matching_tolerance_days": 2,
            "scenario_summary": scenario_summary,
            "rows": scenario_rows,
        },
    }
    write_json(Path(args.json_output), payload)
    write_report(Path(args.report), payload)
    print(f"Wrote Phase 3 JSON: {args.json_output}")
    print(f"Wrote Phase 3 report: {args.report}")
    print(f"Rolling origins: {len(rolling_records)}")
    print(f"Final holdout observed rows: {final_metrics[0]['observed_target_rows']}")
    print(interval_comparison.to_string(index=False))
    print(f"Adopted interval method: {adopted_method}")
    print(f"Recommendation scenario rows: {len(scenario_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
