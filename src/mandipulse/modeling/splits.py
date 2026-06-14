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
    validation_end = test_start - pd.Timedelta(days=1)
    validation_start = validation_end - pd.Timedelta(days=config.validation_days - 1)

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
