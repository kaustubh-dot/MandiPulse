from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient

    from api.main import app

    return TestClient(app)


class TestHealth:
    def test_returns_200(self, client) -> None:
        r = client.get("/health")
        assert r.status_code == 200

    def test_data_status_available(self, client) -> None:
        r = client.get("/health")
        body = r.json()
        assert body["data_status"] == "available"

    def test_response_shape(self, client) -> None:
        body = client.get("/health").json()
        for key in (
            "status",
            "api_version",
            "data_status",
            "supported_crops",
            "supported_horizons",
        ):
            assert key in body, f"Missing key in /health: {key}"

    def test_supported_crops_contains_onion(self, client) -> None:
        body = client.get("/health").json()
        assert "onion" in body["supported_crops"]

    def test_supported_horizons_contains_7(self, client) -> None:
        body = client.get("/health").json()
        assert 7 in body["supported_horizons"]


class TestForecast:
    _VALID = {"crop": "onion", "state": "maharashtra", "mandi": "lasalgaon", "horizon_days": 7}

    def test_happy_path_200(self, client) -> None:
        r = client.post("/forecast", json=self._VALID)
        assert r.status_code == 200

    def test_response_has_bounds(self, client) -> None:
        body = client.post("/forecast", json=self._VALID).json()
        assert "lower_bound_inr_qtl" in body
        assert "upper_bound_inr_qtl" in body
        assert body["lower_bound_inr_qtl"] < body["forecast_price_inr_qtl"]
        assert body["upper_bound_inr_qtl"] > body["forecast_price_inr_qtl"]

    def test_response_has_confidence(self, client) -> None:
        body = client.post("/forecast", json=self._VALID).json()
        assert 0 < body["confidence_level"] <= 1.0

    def test_risk_level_valid(self, client) -> None:
        body = client.post("/forecast", json=self._VALID).json()
        assert body["risk_level"] in {"low", "medium", "high"}

    def test_unsupported_crop(self, client) -> None:
        r = client.post("/forecast", json={**self._VALID, "crop": "tomato"})
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "UNSUPPORTED_CROP"

    def test_unsupported_state(self, client) -> None:
        r = client.post("/forecast", json={**self._VALID, "state": "karnataka"})
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "UNSUPPORTED_STATE"

    def test_unsupported_horizon(self, client) -> None:
        r = client.post("/forecast", json={**self._VALID, "horizon_days": 14})
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "UNSUPPORTED_HORIZON"

    def test_mandi_not_found(self, client) -> None:
        r = client.post("/forecast", json={**self._VALID, "mandi": "nonexistent_mandi_xyz"})
        assert r.status_code == 404
        assert r.json()["error"]["code"] == "MANDI_NOT_FOUND"

    def test_validation_error_bad_body(self, client) -> None:
        r = client.post("/forecast", json={"crop": "onion"})
        assert r.status_code == 422
        assert r.json()["error"]["code"] == "VALIDATION_ERROR"

    def test_unknown_request_field_is_rejected(self, client) -> None:
        r = client.post("/forecast", json={**self._VALID, "unexpected": True})
        assert r.status_code == 422
        assert r.json()["error"]["code"] == "VALIDATION_ERROR"

    def test_response_exposes_canonical_as_of_and_target(self, client) -> None:
        body = client.post("/forecast", json=self._VALID).json()
        assert body["canonical_as_of_date"] == "2025-10-30"
        assert body["target_date"] == "2025-11-06"
        assert body["staleness_days"] == 0


class TestRecommend:
    _VALID = {
        "crop": "onion",
        "farmer_location": {"latitude": 19.9975, "longitude": 73.7898},
        "candidate_states": ["maharashtra"],
        "horizon_days": 7,
        "quantity_quintal": 100.0,
    }

    def test_happy_path_200(self, client) -> None:
        r = client.post("/recommend", json=self._VALID)
        assert r.status_code == 200

    def test_alternatives_plural(self, client) -> None:
        body = client.post("/recommend", json=self._VALID).json()
        assert len(body["alternatives"]) > 1

    def test_rank1_is_recommended(self, client) -> None:
        body = client.post("/recommend", json=self._VALID).json()
        top = body["alternatives"][0]
        assert top["rank"] == 1
        assert top["mandi"] == body["recommended_mandi"]

    def test_transport_cost_present(self, client) -> None:
        body = client.post("/recommend", json=self._VALID).json()
        for alt in body["alternatives"]:
            assert alt["estimated_transport_cost_inr_qtl"] >= 0

    def test_risk_levels_valid(self, client) -> None:
        body = client.post("/recommend", json=self._VALID).json()
        for alt in body["alternatives"]:
            assert alt["risk_level"] in {"low", "medium", "high"}

    def test_unsupported_crop(self, client) -> None:
        r = client.post("/recommend", json={**self._VALID, "crop": "wheat"})
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "UNSUPPORTED_CROP"

    def test_unsupported_horizon(self, client) -> None:
        r = client.post("/recommend", json={**self._VALID, "horizon_days": 30})
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "UNSUPPORTED_HORIZON"

    def test_validation_error_bad_lat(self, client) -> None:
        bad = {**self._VALID, "farmer_location": {"latitude": 999, "longitude": 73.7}}
        r = client.post("/recommend", json=bad)
        assert r.status_code == 422
        assert r.json()["error"]["code"] == "VALIDATION_ERROR"

    def test_canonical_policy_and_default_limits_are_explicit(self, client) -> None:
        body = client.post("/recommend", json=self._VALID).json()
        assert body["as_of_date"] == "2025-10-30"
        assert body["as_of_policy"] == "as_of_equals_bundle_max"
        assert body["max_transport_radius_km"] == 500.0
        assert body["max_alternatives"] == 10
        assert len(body["alternatives"]) <= 10
        assert {row["as_of_date"] for row in body["alternatives"]} == {"2025-10-30"}

    def test_configured_alternative_limit_is_enforced(self, client) -> None:
        body = client.post("/recommend", json={**self._VALID, "max_alternatives": 1}).json()
        assert len(body["alternatives"]) == 1
        assert body["alternatives"][0]["rank"] == 1

    @pytest.mark.parametrize(
        "field,value",
        [
            ("max_transport_radius_km", 0),
            ("max_transport_radius_km", 501),
            ("max_alternatives", 0),
            ("max_alternatives", 11),
        ],
    )
    def test_configured_limits_are_validated(self, client, field, value) -> None:
        r = client.post("/recommend", json={**self._VALID, field: value})
        assert r.status_code == 422
        assert r.json()["error"]["code"] == "VALIDATION_ERROR"

    def test_empty_candidate_states_is_typed_validation_error(self, client) -> None:
        r = client.post("/recommend", json={**self._VALID, "candidate_states": []})
        assert r.status_code == 422
        assert r.json()["error"]["code"] == "VALIDATION_ERROR"

    def test_non_finite_quantity_is_rejected(self, client) -> None:
        body = json.dumps({**self._VALID, "quantity_quintal": float("nan")}, allow_nan=True)
        r = client.post(
            "/recommend",
            content=body,
            headers={"content-type": "application/json"},
        )
        assert r.status_code == 422
        assert r.json()["error"]["code"] == "VALIDATION_ERROR"

    def test_no_candidates_within_radius_is_typed_not_found(self, client) -> None:
        request = {
            **self._VALID,
            "farmer_location": {"latitude": 0.0, "longitude": 0.0},
            "max_transport_radius_km": 500,
        }
        r = client.post("/recommend", json=request)
        assert r.status_code == 404
        body = r.json()
        assert body["error"]["code"] == "NO_CANDIDATES_AVAILABLE"
        assert body["error"]["details"]["as_of_policy"] == "as_of_equals_bundle_max"

    def test_unknown_request_field_is_rejected(self, client) -> None:
        r = client.post("/recommend", json={**self._VALID, "unexpected": True})
        assert r.status_code == 422
        assert r.json()["error"]["code"] == "VALIDATION_ERROR"


class TestUnavailableData:
    def test_health_reports_unavailable_snapshot(self, client, monkeypatch) -> None:
        from api import service

        def _raise_unavailable():
            raise OSError("snapshot is missing")

        monkeypatch.setattr(service, "read_forecasts", _raise_unavailable)
        r = client.get("/health")
        assert r.status_code == 503
        body = r.json()
        assert body["status"] == "not_ready"
        assert body["data_status"] == "unavailable"

    def test_health_rejects_malformed_nonempty_snapshot(self, client, monkeypatch) -> None:
        from api import service

        monkeypatch.setattr(
            service,
            "read_forecasts",
            lambda: pd.DataFrame({"as_of_date": ["2025-10-30"], "model_version": ["v1"]}),
        )
        r = client.get("/health")
        assert r.status_code == 503
        body = r.json()
        assert body["status"] == "not_ready"
        assert body["data_status"] == "unavailable"

    def test_health_requires_mandi_metadata(self, client, monkeypatch) -> None:
        from api import service

        def _raise_unavailable():
            raise OSError("metadata is missing")

        monkeypatch.setattr(service, "read_mandi_metadata", _raise_unavailable)
        r = client.get("/health")
        assert r.status_code == 503
        body = r.json()
        assert body["status"] == "not_ready"
        assert body["data_status"] == "unavailable"

    def test_health_reports_empty_mandi_metadata(self, client, monkeypatch) -> None:
        from api import service

        monkeypatch.setattr(service, "read_mandi_metadata", lambda: pd.DataFrame())
        r = client.get("/health")
        assert r.status_code == 503
        body = r.json()
        assert body["status"] == "not_ready"
        assert body["data_status"] == "empty"

    def test_forecast_reports_unavailable_snapshot(self, client, monkeypatch) -> None:
        from api import service

        monkeypatch.setattr(service, "read_forecasts", lambda: pd.DataFrame())
        r = client.post("/forecast", json=TestForecast._VALID)
        assert r.status_code == 503
        assert r.json()["error"]["code"] == "DATA_NOT_AVAILABLE"

    def test_malformed_forecast_columns_are_typed_unavailable(self, client, monkeypatch) -> None:
        from api import service

        monkeypatch.setattr(
            service,
            "read_forecasts",
            lambda: pd.DataFrame({"as_of_date": ["2025-10-30"]}),
        )
        r = client.post("/forecast", json=TestForecast._VALID)
        assert r.status_code == 503
        assert r.json()["error"]["code"] == "DATA_NOT_AVAILABLE"

    def test_malformed_mandi_metadata_is_typed_unavailable(self, client, monkeypatch) -> None:
        from api import service

        monkeypatch.setattr(
            service,
            "read_mandi_metadata",
            lambda: pd.DataFrame({"market_id": [1], "market_name": ["Mandi"]}),
        )
        r = client.post("/forecast", json=TestForecast._VALID)
        assert r.status_code == 503
        assert r.json()["error"]["code"] == "DATA_NOT_AVAILABLE"


class TestInternalErrorEnvelope:
    """RG-06: the 500 handler must render the standard error envelope."""

    def test_unhandled_exception_returns_internal_error_envelope(self) -> None:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from api.errors import internal_error_handler

        probe = FastAPI()
        probe.add_exception_handler(Exception, internal_error_handler)

        @probe.get("/boom")
        def _boom() -> dict:
            raise RuntimeError("boom")

        probe_client = TestClient(probe, raise_server_exceptions=False)
        r = probe_client.get("/boom")
        assert r.status_code == 500
        body = r.json()
        assert body["error"]["code"] == "INTERNAL_ERROR"
        assert body["error"]["message"] == "An unexpected internal error occurred."
        assert "details" not in body["error"]
