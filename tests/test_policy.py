from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from mandipulse.policy import (
    canonical_forecast_as_of,
    cap_history_at_as_of,
    forecast_target_date,
    select_latest_forecast_for_market,
    select_recommendation_candidates,
)


@pytest.fixture()
def forecast_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"market_id": 1, "as_of_date": "2025-10-29", "value": 10},
            {"market_id": 2, "as_of_date": "2025-10-30", "value": 20},
            {"market_id": 1, "as_of_date": "2025-10-30", "value": 30},
        ]
    )


def test_canonical_as_of_is_bundle_maximum(forecast_frame: pd.DataFrame) -> None:
    assert canonical_forecast_as_of(forecast_frame) == date(2025, 10, 30)


def test_recommendation_candidates_are_one_canonical_snapshot(
    forecast_frame: pd.DataFrame,
) -> None:
    eligible = select_recommendation_candidates(forecast_frame)
    assert eligible["market_id"].tolist() == [2, 1]
    assert set(eligible["as_of_date"]) == {"2025-10-30"}


def test_latest_forecast_is_selected_per_market_even_when_stale(
    forecast_frame: pd.DataFrame,
) -> None:
    row = select_latest_forecast_for_market(forecast_frame, 1)
    assert row["value"] == 30
    assert row["as_of_date"] == "2025-10-30"


def test_history_is_capped_at_forecast_origin() -> None:
    history = pd.DataFrame(
        {
            "date": ["2025-10-28", "2025-10-30", "2025-10-31"],
            "value": [1, 2, 3],
        }
    )
    capped = cap_history_at_as_of(history, "2025-10-30")
    assert capped["value"].tolist() == [1, 2]


def test_forecast_target_date_uses_origin_plus_horizon() -> None:
    assert forecast_target_date("2025-10-30", 7) == date(2025, 11, 6)


@pytest.mark.parametrize("horizon", [0, -1, True, 7.0])
def test_forecast_target_date_requires_positive_integer(horizon) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        forecast_target_date("2025-10-30", horizon)


def test_policy_rejects_invalid_dates() -> None:
    invalid = pd.DataFrame({"as_of_date": ["2025-10-30", None]})
    with pytest.raises(ValueError, match="invalid or missing date"):
        canonical_forecast_as_of(invalid)
