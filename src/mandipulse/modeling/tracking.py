from __future__ import annotations

import warnings
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

from mandipulse.config import load_yaml_config, resolve_project_path

try:
    import mlflow

    _MLFLOW_AVAILABLE = True
except ImportError:
    mlflow = None  # type: ignore[assignment]
    _MLFLOW_AVAILABLE = False


def _tracking_uri() -> str:
    cfg = load_yaml_config("configs/app.yaml")
    raw = cfg.get("mlflow", {}).get("tracking_uri", "sqlite:///mlruns/mlflow.db")
    # Pass sqlite:// URIs through unchanged; resolve relative file paths to absolute.
    if raw.startswith("sqlite:///") or "://" in raw:
        return raw
    return resolve_project_path(raw).as_uri()


def set_experiment(name: str) -> None:
    if not _MLFLOW_AVAILABLE:
        warnings.warn("mlflow not installed; tracking is disabled.", stacklevel=2)
        return
    mlflow.set_tracking_uri(_tracking_uri())
    mlflow.set_experiment(name)


@contextmanager
def start_run(run_name: str | None = None) -> Generator[Any, None, None]:
    if not _MLFLOW_AVAILABLE:
        yield None
        return
    mlflow.set_tracking_uri(_tracking_uri())
    with mlflow.start_run(run_name=run_name) as run:
        yield run


def log_params(params: dict[str, Any]) -> None:
    if not _MLFLOW_AVAILABLE:
        return
    mlflow.log_params(params)


def log_metrics(metrics: dict[str, float]) -> None:
    if not _MLFLOW_AVAILABLE:
        return
    mlflow.log_metrics(metrics)


def log_artifact(path: Path) -> None:
    if not _MLFLOW_AVAILABLE:
        return
    mlflow.log_artifact(str(path))
