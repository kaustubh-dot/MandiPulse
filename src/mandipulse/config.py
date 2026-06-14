from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def resolve_project_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return PROJECT_ROOT / candidate


def load_yaml_config(path: str | Path) -> dict[str, Any]:
    config_path = resolve_project_path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}
