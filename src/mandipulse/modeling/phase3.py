"""Small, deterministic helpers for the Phase 3 evidence package.

The public product contract is deliberately unchanged by this module.  It keeps
evaluation-only concerns (point-in-time filling, population accounting, interval
comparison, and provenance) together so reports cannot silently use a different
definition from the model or recommendation code.
"""

from __future__ import annotations

import hashlib
import math
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd


def impute_short_internal_gaps(
    frame: pd.DataFrame,
    *,
    value_columns: Sequence[str],
    group_column: str = "market_id",
    date_column: str = "date",
    max_gap_days: int = 3,
) -> pd.DataFrame:
    """Forward-fill short *internal* gaps without reading future values.

    ``next_seen`` is used only to identify a bounded gap.  The replacement value
    is always the last value available at that row (``ffill``), which is the
    point-in-time-safe rule used by the clean panel builder.  Leading/trailing
    gaps and gaps longer than ``max_gap_days`` remain missing.
    """

    if not value_columns:
        raise ValueError("value_columns must contain at least one column")
    if max_gap_days < 1:
        raise ValueError("max_gap_days must be positive")
    required = {group_column, date_column, *value_columns}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Frame is missing required columns: {missing}")

    result = frame.copy()
    result[date_column] = pd.to_datetime(result[date_column])
    frames: list[pd.DataFrame] = []
    for _, group in result.groupby(group_column, sort=False, dropna=False):
        group = group.sort_values(date_column).copy()
        missing_price = group[value_columns[0]].isna()
        run_id = missing_price.ne(missing_price.shift()).cumsum()
        run_lengths = missing_price.groupby(run_id).transform("sum")
        seen_before = group[value_columns[0]].notna().cummax()
        seen_after = group[value_columns[0]].notna()[::-1].cummax()[::-1]
        short_internal_gap = (
            missing_price & seen_before & seen_after & (run_lengths <= max_gap_days)
        )

        group["is_imputed"] = False
        group["imputation_method"] = ""
        if short_internal_gap.any():
            # Crucially, this is not bfill/interpolation: it cannot use a later
            # observation to populate a row's value.
            filled = group[list(value_columns)].ffill()
            group.loc[short_internal_gap, list(value_columns)] = filled.loc[
                short_internal_gap, list(value_columns)
            ]
            group.loc[short_internal_gap, "is_imputed"] = True
            group.loc[short_internal_gap, "imputation_method"] = f"ffill_gap_le_{max_gap_days}_days"
        frames.append(group)

    return (
        pd.concat(frames, ignore_index=True)
        .sort_values([group_column, date_column])
        .reset_index(drop=True)
    )


def observed_target_mask(frame: pd.DataFrame) -> pd.Series:
    """Return the primary evaluation population mask.

    Both the as-of row and its t+7 target must be observed.  Imputed targets are
    intentionally not mixed into this population.
    """

    required = {"is_observed", "target_observed_t_plus_7"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Frame is missing observed-target columns: {missing}")
    return frame["is_observed"].fillna(False).astype(bool) & frame[
        "target_observed_t_plus_7"
    ].fillna(False).astype(bool)


def target_population_counts(frame: pd.DataFrame) -> dict[str, int]:
    """Return explicit denominator counts for observed, imputed, and unavailable targets."""

    as_of_observed = frame.get("is_observed", pd.Series(True, index=frame.index))
    target_observed = frame.get("target_observed_t_plus_7", pd.Series(False, index=frame.index))
    target_imputed = frame.get("target_imputed_t_plus_7", pd.Series(False, index=frame.index))
    observed = as_of_observed.fillna(False).astype(bool) & target_observed.fillna(False).astype(
        bool
    )
    imputed = target_imputed.fillna(False).astype(bool) & ~observed
    return {
        "rows": int(len(frame)),
        "observed_target_rows": int(observed.sum()),
        "imputed_target_rows": int(imputed.sum()),
        "unavailable_target_rows": int((~observed & ~imputed).sum()),
    }


def _quantile(values: Iterable[float], probability: float, *, method: str = "linear") -> float:
    values_array = np.asarray(list(values), dtype=float)
    values_array = values_array[np.isfinite(values_array)]
    if values_array.size == 0:
        raise ValueError("Cannot calculate an interval from empty/non-finite residuals")
    return float(np.quantile(values_array, probability, method=method))


def compare_interval_methods(
    predictions: pd.DataFrame,
    *,
    model_name: str,
    confidence_level: float = 0.90,
    calibration_split: str = "validation",
    evaluation_split: str = "test",
    observed_only: bool = True,
) -> pd.DataFrame:
    """Compare conditional residual and split-conformal intervals.

    Calibration and evaluation populations are selected independently.  The
    returned rows include the exact observed-target denominator and excluded
    imputed count so coverage cannot be interpreted without its population.
    """

    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must be between 0 and 1")
    selected = predictions[predictions["model"] == model_name].copy()
    if selected.empty:
        raise ValueError(f"No predictions found for model '{model_name}'")
    for column in ("split", "target_price_t_plus_7", "prediction"):
        if column not in selected:
            raise ValueError(f"Predictions are missing required column: {column}")

    calibration = selected[selected["split"] == calibration_split].copy()
    evaluation = selected[selected["split"] == evaluation_split].copy()
    evaluation_counts = target_population_counts(evaluation)
    if observed_only:
        calibration = calibration[observed_target_mask(calibration)]
        evaluation_observed = observed_target_mask(evaluation)
        excluded_imputed = int(
            evaluation.get("target_imputed_t_plus_7", pd.Series(False, index=evaluation.index))
            .fillna(False)
            .astype(bool)
            .sum()
        )
        evaluation = evaluation[evaluation_observed]
    else:
        excluded_imputed = 0
    if calibration.empty or evaluation.empty:
        raise ValueError(
            "Interval comparison needs non-empty calibration and evaluation populations"
        )

    residuals = calibration["target_price_t_plus_7"] - calibration["prediction"]
    alpha = 1.0 - confidence_level
    conditional_lower = _quantile(residuals, alpha / 2)
    conditional_upper = _quantile(residuals, 1 - alpha / 2)
    absolute_residuals = np.abs(np.asarray(residuals, dtype=float))
    # Finite-sample split conformal quantile.  ``higher`` makes the guarantee
    # conservative for the finite calibration sample rather than interpolating
    # below an observed residual.
    conformal_probability = min(
        1.0, math.ceil((len(absolute_residuals) + 1) * confidence_level) / len(absolute_residuals)
    )
    conformal_radius = _quantile(absolute_residuals, conformal_probability, method="higher")

    candidates = {
        "conditional_residual": (
            conditional_lower,
            conditional_upper,
            "asymmetric residual quantiles from observed validation targets",
        ),
        "split_conformal": (
            -conformal_radius,
            conformal_radius,
            "symmetric finite-sample absolute-residual quantile from observed validation targets",
        ),
    }
    rows: list[dict[str, object]] = []
    for method, (lower, upper, description) in candidates.items():
        lower_bounds = evaluation["prediction"] + lower
        upper_bounds = evaluation["prediction"] + upper
        covered = evaluation["target_price_t_plus_7"].between(lower_bounds, upper_bounds)
        rows.append(
            {
                "method": method,
                "description": description,
                "nominal_coverage": float(confidence_level),
                "calibration_rows": int(len(calibration)),
                "evaluation_rows": int(len(evaluation)),
                "excluded_imputed_rows": excluded_imputed,
                "excluded_unavailable_rows": evaluation_counts["unavailable_target_rows"],
                "empirical_coverage": float(covered.mean()),
                "coverage_error": float(covered.mean() - confidence_level),
                "coverage_shortfall": float(max(confidence_level - covered.mean(), 0.0)),
                "failure_mode": (
                    "undercoverage_on_observed_holdout"
                    if covered.mean() < confidence_level
                    else "nominal_or_overcoverage_with_width_tradeoff"
                ),
                "excluded_imputed_rate": float(
                    excluded_imputed / evaluation_counts["rows"]
                    if evaluation_counts["rows"]
                    else 0.0
                ),
                "excluded_unavailable_rate": float(
                    evaluation_counts["unavailable_target_rows"] / evaluation_counts["rows"]
                    if evaluation_counts["rows"]
                    else 0.0
                ),
                "avg_interval_width_inr_qtl": float((upper_bounds - lower_bounds).mean()),
                "median_interval_width_inr_qtl": float((upper_bounds - lower_bounds).median()),
                "lower_residual": float(lower),
                "upper_residual": float(upper),
            }
        )
    return pd.DataFrame(rows)


def adopt_interval_method(comparison: pd.DataFrame) -> tuple[str, str]:
    """Apply the pre-declared adoption rule to an interval comparison.

    Rule: choose the candidate whose observed holdout coverage is closest to
    nominal; break ties with the narrower mean interval.  This rule is fixed
    before looking at the generated comparison and is not a post-hoc model claim.
    """

    required = {"method", "nominal_coverage", "empirical_coverage", "avg_interval_width_inr_qtl"}
    missing = sorted(required - set(comparison.columns))
    if missing or comparison.empty:
        raise ValueError(f"Interval comparison is missing required fields: {missing}")
    ranked = comparison.assign(
        _coverage_error=(comparison["empirical_coverage"] - comparison["nominal_coverage"]).abs()
    ).sort_values(["_coverage_error", "avg_interval_width_inr_qtl", "method"])
    selected = ranked.iloc[0]
    reason = (
        "pre-declared rule: smallest absolute coverage error to nominal, "
        "then narrowest mean interval"
    )
    return str(selected["method"]), reason


def sha256_file(path: Path) -> str:
    """Return a deterministic SHA-256 for a local evidence input."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_hash(value: object) -> str:
    """Hash JSON-compatible configuration with stable key ordering."""

    import json

    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(payload).hexdigest()
