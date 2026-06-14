from __future__ import annotations

from pathlib import Path

from mandipulse.config import PROJECT_ROOT, load_yaml_config, resolve_project_path


def _app_cfg() -> dict:
    return load_yaml_config("configs/app.yaml")


def _data_cfg() -> dict:
    return load_yaml_config("configs/data.yaml")


# --- Processed data ---


def processed_dir() -> Path:
    return PROJECT_ROOT / "data" / "processed" / "onion_maharashtra"


def clean_panel_path() -> Path:
    return processed_dir() / "clean_mandi_prices.csv"


def feature_table_path() -> Path:
    return processed_dir() / "feature_table_7d.csv"


# --- Artifacts ---


def artifacts_dir() -> Path:
    return PROJECT_ROOT / "artifacts"


def forecasts_dir() -> Path:
    return artifacts_dir() / "forecasts"


def forecast_outputs_path() -> Path:
    return forecasts_dir() / "forecast_outputs_7d.csv"


def recommendations_dir() -> Path:
    return artifacts_dir() / "recommendations"


def recommendation_outputs_path() -> Path:
    return recommendations_dir() / "recommendation_outputs_7d.csv"


def metrics_dir() -> Path:
    return artifacts_dir() / "metrics"


def predictions_dir() -> Path:
    return artifacts_dir() / "predictions"


def models_dir() -> Path:
    cfg = _app_cfg()
    rel = cfg.get("artifacts", {}).get("model_artifact_path", "artifacts/models")
    return resolve_project_path(rel)


# --- Reports ---


def reports_modeling_dir() -> Path:
    return PROJECT_ROOT / "reports" / "modeling"


def reports_data_quality_dir() -> Path:
    cfg = _app_cfg()
    rel = cfg.get("artifacts", {}).get("quality_reports_path", "reports/data_quality")
    return resolve_project_path(rel)


# --- External data ---


def mvp_mandis_path() -> Path:
    return PROJECT_ROOT / "data" / "external" / "mvp_mandis.csv"
