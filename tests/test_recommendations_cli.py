"""Tests for the offline recommendation artifact CLI contract."""

from pathlib import Path

from scripts.build_recommendations_7d import load_forecasts


def test_load_forecasts_uses_one_canonical_as_of_snapshot() -> None:
    forecasts = load_forecasts(
        Path("tests/golden/forecast_outputs_7d.csv"),
        candidate_state="maharashtra",
    )

    assert set(forecasts["as_of_date"].astype(str)) == {"2025-10-30"}
    assert len(forecasts) == 10
