from __future__ import annotations

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from mandipulse.modeling.columns import (
    CATEGORICAL_FEATURES,
    CURRENT_PRICE_COLUMN,
    DATE_COLUMN,
    MARKET_ID_COLUMN,
    MARKET_NAME_COLUMN,
    NUMERIC_FEATURES,
    TARGET_COLUMN,
)


def build_ridge_pipeline(alpha: float) -> Pipeline:
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, NUMERIC_FEATURES),
            ("cat", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )
    return Pipeline(steps=[("preprocessor", preprocessor), ("model", Ridge(alpha=alpha))])


def predict_baselines(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    test: pd.DataFrame,
    ridge_alpha: float,
) -> pd.DataFrame:
    ridge = build_ridge_pipeline(ridge_alpha)
    ridge.fit(train[NUMERIC_FEATURES + CATEGORICAL_FEATURES], train[TARGET_COLUMN])

    frames = []
    baseline_specs = [
        ("seasonal_naive_7d", CURRENT_PRICE_COLUMN),
        ("moving_average_7d", "rolling_mean_7"),
        ("moving_average_30d", "rolling_mean_30"),
    ]

    for split_name, split_df in [("validation", validation), ("test", test)]:
        base_columns = [
            DATE_COLUMN,
            MARKET_ID_COLUMN,
            MARKET_NAME_COLUMN,
            "mandi_id",
            "district",
            TARGET_COLUMN,
        ]
        for model_name, prediction_column in baseline_specs:
            frame = split_df[base_columns].copy()
            frame["split"] = split_name
            frame["model"] = model_name
            frame["prediction"] = split_df[prediction_column].astype(float).to_numpy()
            frames.append(frame)

        ridge_frame = split_df[base_columns].copy()
        ridge_frame["split"] = split_name
        ridge_frame["model"] = "ridge"
        ridge_frame["prediction"] = ridge.predict(split_df[NUMERIC_FEATURES + CATEGORICAL_FEATURES])
        frames.append(ridge_frame)

    predictions = pd.concat(frames, ignore_index=True)
    predictions = predictions.dropna(subset=["prediction", TARGET_COLUMN])
    return predictions
