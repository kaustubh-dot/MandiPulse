from __future__ import annotations

import tempfile
import warnings
from pathlib import Path

import pytest

import mandipulse.modeling.tracking as tracking


class TestTrackingUri:
    def test_sqlite_uri_passes_through(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            tracking,
            "load_yaml_config",
            lambda _: {"mlflow": {"tracking_uri": "sqlite:///mlruns/mlflow.db"}},
        )
        uri = tracking._tracking_uri()
        assert uri == "sqlite:///mlruns/mlflow.db"

    def test_generic_scheme_passes_through(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            tracking,
            "load_yaml_config",
            lambda _: {"mlflow": {"tracking_uri": "http://localhost:5000"}},
        )
        uri = tracking._tracking_uri()
        assert uri == "http://localhost:5000"

    def test_missing_key_uses_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(tracking, "load_yaml_config", lambda _: {})
        uri = tracking._tracking_uri()
        assert "sqlite:///" in uri


class TestMlflowAbsentDegradation:
    """When mlflow is unavailable, all public functions degrade silently."""

    def test_set_experiment_warns(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(tracking, "_MLFLOW_AVAILABLE", False)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            tracking.set_experiment("test_exp")
        assert any("mlflow" in str(w.message).lower() for w in caught)

    def test_start_run_yields_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(tracking, "_MLFLOW_AVAILABLE", False)
        with tracking.start_run("noop") as run:
            assert run is None

    def test_log_params_no_op(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(tracking, "_MLFLOW_AVAILABLE", False)
        tracking.log_params({"alpha": 1.0})  # must not raise

    def test_log_metrics_no_op(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(tracking, "_MLFLOW_AVAILABLE", False)
        tracking.log_metrics({"mae": 139.57})  # must not raise

    def test_log_artifact_no_op(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(tracking, "_MLFLOW_AVAILABLE", False)
        with tempfile.TemporaryDirectory() as tmpdir:
            tracking.log_artifact(Path(tmpdir) / "fake.csv")  # must not raise
