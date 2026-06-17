from __future__ import annotations

import sys
from pathlib import Path

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
