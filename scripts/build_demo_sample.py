from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mandipulse.data.store import read_csv_via_duckdb  # noqa: E402
from mandipulse.paths import (  # noqa: E402
    clean_panel_path,
    feature_table_path,
    forecast_outputs_path,
    recommendation_backtest_path,
)

# Only the columns that the Streamlit pages actually read.
# Dropping unused columns is the main size-reduction lever.
_PANEL_COLS = [
    "date",
    "market_id",
    "market_name",
    "modal_price_inr_qtl",
    "is_observed",
    "is_imputed",
]
_FEATURE_COLS = ["date", "market_id", "market_name", "feature_row_valid"]


def _sample_dir() -> Path:
    from mandipulse.config import PROJECT_ROOT

    return PROJECT_ROOT / "data" / "sample"


def _build_slim_panel(src: Path) -> pd.DataFrame:
    df = read_csv_via_duckdb(src, parse_dates=["date"])
    missing = [c for c in _PANEL_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"clean panel missing expected columns: {missing}")
    return df[_PANEL_COLS]


def _build_slim_features(src: Path) -> pd.DataFrame:
    df = read_csv_via_duckdb(src, parse_dates=["date"])
    missing = [c for c in _FEATURE_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"feature table missing expected columns: {missing}")
    return df[_FEATURE_COLS]


def _verify(
    full_panel: pd.DataFrame,
    slim_panel: pd.DataFrame,
    full_features: pd.DataFrame,
    slim_features: pd.DataFrame,
) -> None:
    # Row counts must be preserved exactly
    assert len(slim_panel) == len(full_panel), "panel row count mismatch"
    assert len(slim_features) == len(full_features), "feature row count mismatch"

    # KPIs displayed on Data Coverage page must match
    assert int(slim_panel["is_observed"].sum()) == int(
        full_panel["is_observed"].sum()
    ), "observed count mismatch"
    assert int(slim_panel["is_imputed"].fillna(False).sum()) == int(
        full_panel["is_imputed"].fillna(False).sum()
    ), "imputed count mismatch"
    assert (
        slim_panel["market_id"].nunique() == full_panel["market_id"].nunique()
    ), "mandi count mismatch"
    assert slim_panel["date"].min() == full_panel["date"].min(), "date_min mismatch"
    assert slim_panel["date"].max() == full_panel["date"].max(), "date_max mismatch"

    # Trainable row count (the single KPI features drives)
    slim_trainable = int(slim_features["feature_row_valid"].astype(bool).sum())
    full_trainable = int(full_features["feature_row_valid"].astype(bool).sum())
    assert (
        slim_trainable == full_trainable
    ), f"trainable rows mismatch: {slim_trainable} vs {full_trainable}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a slim committed demo bundle from full pipeline artifacts."
    )
    parser.add_argument("--no-verify", action="store_true", help="Skip parity verification.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out = _sample_dir()
    out.mkdir(parents=True, exist_ok=True)

    # --- clean panel ---
    src_panel = clean_panel_path()
    if not src_panel.exists():
        print(f"ERROR: clean panel not found at {src_panel}")
        print("Run build_clean_onion_panel.py first.")
        sys.exit(1)
    full_panel = read_csv_via_duckdb(src_panel, parse_dates=["date"])
    slim_panel = _build_slim_panel(src_panel)
    slim_panel.to_csv(out / "clean_mandi_prices.csv", index=False)
    print(f"clean_mandi_prices.csv: {len(slim_panel):,} rows x {len(slim_panel.columns)} cols")

    # --- feature table ---
    src_feats = feature_table_path()
    if not src_feats.exists():
        print(f"ERROR: feature table not found at {src_feats}")
        print("Run build_feature_table.py first.")
        sys.exit(1)
    full_features = read_csv_via_duckdb(src_feats, parse_dates=["date"])
    slim_features = _build_slim_features(src_feats)
    slim_features.to_csv(out / "feature_table_7d.csv", index=False)
    print(f"feature_table_7d.csv: {len(slim_features):,} rows x {len(slim_features.columns)} cols")

    # --- forecast outputs (verbatim, already small) ---
    src_fc = forecast_outputs_path()
    if not src_fc.exists():
        print(f"ERROR: forecast outputs not found at {src_fc}")
        print("Run build_forecast_intervals_7d.py first.")
        sys.exit(1)
    fc = read_csv_via_duckdb(src_fc)
    fc.to_csv(out / "forecast_outputs_7d.csv", index=False)
    print(f"forecast_outputs_7d.csv: {len(fc)} rows")

    # --- recommendation backtest (verbatim, optional) ---
    src_bt = recommendation_backtest_path()
    if src_bt.exists():
        bt = read_csv_via_duckdb(src_bt)
        bt.to_csv(out / "recommendation_backtest_7d.csv", index=False)
        print(f"recommendation_backtest_7d.csv: {len(bt)} rows")
    else:
        print("recommendation_backtest_7d.csv: skipped (artifact not present; optional)")

    # --- verify parity ---
    if not args.no_verify:
        _verify(full_panel, slim_panel, full_features, slim_features)
        print("Parity verification passed.")

    total_mb = (
        sum((out / f).stat().st_size for f in out.iterdir() if f.suffix == ".csv") / 1_048_576
    )
    print(f"Total bundle size: {total_mb:.2f} MB in {out}")


if __name__ == "__main__":
    main()
