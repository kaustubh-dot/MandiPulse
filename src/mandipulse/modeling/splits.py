from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from mandipulse.modeling.columns import (
    CATEGORICAL_FEATURES,
    CURRENT_PRICE_COLUMN,
    DATE_COLUMN,
    MARKET_ID_COLUMN,
    MARKET_NAME_COLUMN,
    NUMERIC_FEATURES,
    TARGET_COLUMN,
)


@dataclass(frozen=True)
class SplitConfig:
    validation_days: int
    test_days: int
    horizon_days: int


@dataclass(frozen=True)
class SplitDates:
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    validation_start: pd.Timestamp
    validation_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp


@dataclass(frozen=True)
class RollingOriginSplit:
    """Date boundaries for one rolling-origin evaluation window."""

    origin_date: pd.Timestamp
    dates: SplitDates

    def select(self, frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Select train/validation/test rows for this origin from a feature frame."""

        dates = pd.to_datetime(frame[DATE_COLUMN])
        train = frame[(dates >= self.dates.train_start) & (dates <= self.dates.train_end)].copy()
        validation = frame[
            (dates >= self.dates.validation_start) & (dates <= self.dates.validation_end)
        ].copy()
        test = frame[(dates >= self.dates.test_start) & (dates <= self.dates.test_end)].copy()
        return train, validation, test


def load_trainable_features(path: Path) -> pd.DataFrame:
    features = pd.read_csv(path)
    features[DATE_COLUMN] = pd.to_datetime(features[DATE_COLUMN])

    required_columns = {
        DATE_COLUMN,
        MARKET_ID_COLUMN,
        MARKET_NAME_COLUMN,
        CURRENT_PRICE_COLUMN,
        TARGET_COLUMN,
        "feature_row_valid",
        "is_observed",
        "target_observed_t_plus_7",
        *NUMERIC_FEATURES,
        *CATEGORICAL_FEATURES,
    }
    missing = sorted(required_columns - set(features.columns))
    if missing:
        raise ValueError(f"Feature table is missing required columns: {missing}")

    trainable = features[features["feature_row_valid"].astype(bool)].copy()
    trainable = trainable.dropna(subset=[TARGET_COLUMN, CURRENT_PRICE_COLUMN])
    if trainable.empty:
        raise ValueError("No trainable rows found in feature table.")
    return trainable.sort_values([DATE_COLUMN, MARKET_ID_COLUMN]).reset_index(drop=True)


def apply_row_filter(df: pd.DataFrame, row_filter: str) -> pd.DataFrame:
    if row_filter == "all":
        return df.copy()
    if row_filter == "observed_only":
        filtered = df[
            df["is_observed"].astype(bool) & df["target_observed_t_plus_7"].astype(bool)
        ].copy()
        if filtered.empty:
            raise ValueError("Observed-only filter removed every row.")
        return filtered
    raise ValueError(f"Unsupported row filter: {row_filter}")


def make_temporal_splits(
    df: pd.DataFrame, config: SplitConfig
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, SplitDates]:
    max_date = df[DATE_COLUMN].max().normalize()
    test_start = max_date - pd.Timedelta(days=config.test_days - 1)
    # Purge gap: validation targets must not overlap the test period.
    # Since target is t+horizon, validation rows within horizon_days of
    # test_start would have targets landing inside the test window.
    validation_end = test_start - pd.Timedelta(days=1 + config.horizon_days)
    validation_start = validation_end - pd.Timedelta(days=config.validation_days - 1)

    # Purge gap: training targets must not overlap the validation period.
    train_cutoff = validation_start - pd.Timedelta(days=config.horizon_days)

    train = df[df[DATE_COLUMN] < train_cutoff].copy()
    validation = df[
        (df[DATE_COLUMN] >= validation_start) & (df[DATE_COLUMN] <= validation_end)
    ].copy()
    test = df[df[DATE_COLUMN] >= test_start].copy()

    if train.empty or validation.empty or test.empty:
        raise ValueError(
            "Temporal split produced an empty partition. "
            f"train={len(train)}, validation={len(validation)}, test={len(test)}"
        )

    split_dates = SplitDates(
        train_start=train[DATE_COLUMN].min(),
        train_end=train[DATE_COLUMN].max(),
        validation_start=validation[DATE_COLUMN].min(),
        validation_end=validation[DATE_COLUMN].max(),
        test_start=test[DATE_COLUMN].min(),
        test_end=test[DATE_COLUMN].max(),
    )
    return train, validation, test, split_dates


def make_rolling_origin_splits(
    df: pd.DataFrame,
    config: SplitConfig,
    *,
    n_origins: int = 3,
    final_holdout_days: int = 90,
) -> list[RollingOriginSplit]:
    """Build reproducible rolling windows before an untouched final holdout.

    Origins are spaced by one test window.  The latest rolling test window ends
    immediately before the final holdout, and every validation/train boundary is
    purged by ``horizon_days`` so a target cannot cross a split boundary.
    """

    if n_origins < 1:
        raise ValueError("n_origins must be positive")
    if final_holdout_days < 1:
        raise ValueError("final_holdout_days must be positive")
    if config.validation_days < 1 or config.test_days < 1 or config.horizon_days < 1:
        raise ValueError("split window and horizon values must be positive")
    if DATE_COLUMN not in df:
        raise ValueError(f"Frame is missing required column: {DATE_COLUMN}")

    dates = pd.to_datetime(df[DATE_COLUMN]).dt.normalize()
    max_date = dates.max()
    min_date = dates.min()
    final_holdout_start = max_date - pd.Timedelta(days=final_holdout_days - 1)
    latest_test_end = final_holdout_start - pd.Timedelta(days=1)
    origins: list[RollingOriginSplit] = []

    for offset in reversed(range(n_origins)):
        test_end = latest_test_end - pd.Timedelta(days=offset * config.test_days)
        test_start = test_end - pd.Timedelta(days=config.test_days - 1)
        validation_end = test_start - pd.Timedelta(days=config.horizon_days + 1)
        validation_start = validation_end - pd.Timedelta(days=config.validation_days - 1)
        train_end = validation_start - pd.Timedelta(days=config.horizon_days)
        train_start = min_date
        if train_end < train_start or validation_start < train_start or test_start < train_start:
            continue

        boundaries = SplitDates(
            train_start=train_start,
            train_end=train_end,
            validation_start=validation_start,
            validation_end=validation_end,
            test_start=test_start,
            test_end=test_end,
        )
        candidate = RollingOriginSplit(origin_date=test_end, dates=boundaries)
        train, validation, test = candidate.select(df)
        if train.empty or validation.empty or test.empty:
            continue
        origins.append(candidate)

    if len(origins) != n_origins:
        raise ValueError(
            "Unable to build the requested rolling origins; "
            f"requested={n_origins}, available={len(origins)}"
        )
    return origins
