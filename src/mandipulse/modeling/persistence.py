from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    import joblib
except ImportError:
    joblib = None  # type: ignore[assignment]


def save_model(pipeline: Any, path: Path) -> None:
    if joblib is None:
        raise ImportError(
            "joblib is required for model persistence. Install it with: pip install joblib"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, path)


def load_model(path: Path) -> Any:
    if joblib is None:
        raise ImportError(
            "joblib is required for model loading. Install it with: pip install joblib"
        )
    return joblib.load(path)


def save_feature_schema(
    path: Path,
    numeric_features: list[str],
    categorical_features: list[str],
    target: str,
    horizon_days: int,
) -> None:
    schema = {
        "numeric_features": numeric_features,
        "categorical_features": categorical_features,
        "target": target,
        "horizon_days": horizon_days,
        "created_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(schema, indent=2), encoding="utf-8")


def load_feature_schema(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
