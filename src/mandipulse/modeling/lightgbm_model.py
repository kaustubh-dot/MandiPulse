from __future__ import annotations

import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from mandipulse.modeling.columns import (
    CATEGORICAL_FEATURES,
    DATE_COLUMN,
    MARKET_ID_COLUMN,
    MARKET_NAME_COLUMN,
    NUMERIC_FEATURES,
    TARGET_COLUMN,
)


def build_lightgbm_pipeline(
    n_estimators: int = 400,
    learning_rate: float = 0.05,
    num_leaves: int = 31,
    min_child_samples: int = 20,
    subsample: float = 0.9,
    colsample_bytree: float = 0.9,
    reg_alpha: float = 0.0,
    reg_lambda: float = 0.0,
    random_state: int = 42,
) -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", SimpleImputer(strategy="median"), NUMERIC_FEATURES),
            (
                "cat",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                CATEGORICAL_FEATURES,
            ),
        ]
    )
    model = LGBMRegressor(
        objective="regression",
        n_estimators=n_estimators,
        learning_rate=learning_rate,
        num_leaves=num_leaves,
        min_child_samples=min_child_samples,
        subsample=subsample,
        colsample_bytree=colsample_bytree,
        reg_alpha=reg_alpha,
        reg_lambda=reg_lambda,
        random_state=random_state,
    )
    return Pipeline(steps=[("preprocessor", preprocessor), ("model", model)])


def predict_lightgbm(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    test: pd.DataFrame,
    n_estimators: int = 400,
    learning_rate: float = 0.05,
    num_leaves: int = 31,
    min_child_samples: int = 20,
    subsample: float = 0.9,
    colsample_bytree: float = 0.9,
    reg_alpha: float = 0.0,
    reg_lambda: float = 0.0,
    random_state: int = 42,
) -> pd.DataFrame:
    model = build_lightgbm_pipeline(
        n_estimators=n_estimators,
        learning_rate=learning_rate,
        num_leaves=num_leaves,
        min_child_samples=min_child_samples,
        subsample=subsample,
        colsample_bytree=colsample_bytree,
        reg_alpha=reg_alpha,
        reg_lambda=reg_lambda,
        random_state=random_state,
    )
    feature_columns = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    model.fit(train[feature_columns], train[TARGET_COLUMN])

    frames: list[pd.DataFrame] = []
    for split_name, split_df in [("validation", validation), ("test", test)]:
        frame = split_df[
            [
                DATE_COLUMN,
                MARKET_ID_COLUMN,
                MARKET_NAME_COLUMN,
                "mandi_id",
                "district",
                TARGET_COLUMN,
            ]
        ].copy()
        frame["split"] = split_name
        frame["model"] = "lightgbm"
        frame["prediction"] = model.predict(split_df[feature_columns])
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)
