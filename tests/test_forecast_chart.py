from __future__ import annotations

import pandas as pd

from mandipulse.app.forecast_chart import build_forecast_figure


def _history() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2025-01-01", "2025-01-02", "2025-01-03"]),
            "modal_price_inr_qtl": [1000.0, 1010.0, 1020.0],
            "is_imputed": [False, True, False],
        }
    )


def test_forecast_uses_separate_endpoint_lane() -> None:
    target = pd.Timestamp("2025-01-10")
    figure = build_forecast_figure(
        history=_history(),
        forecast_value=1050.0,
        lower_bound=830.0,
        upper_bound=1340.0,
        as_of=pd.Timestamp("2025-01-03"),
        target=target,
    )

    assert figure.layout.xaxis.domain[1] < figure.layout.xaxis2.domain[0]
    endpoint = next(trace for trace in figure.data if trace.name == "7-day forecast")
    assert list(endpoint.x) == [target]
    assert tuple(endpoint.error_y.array) == (290.0,)
    assert tuple(endpoint.error_y.arrayminus) == (220.0,)


def test_history_line_stays_continuous_through_imputed_values() -> None:
    figure = build_forecast_figure(
        history=_history(),
        forecast_value=1050.0,
        lower_bound=830.0,
        upper_bound=1340.0,
        as_of=pd.Timestamp("2025-01-03"),
        target=pd.Timestamp("2025-01-10"),
    )

    history_trace = next(
        trace for trace in figure.data if trace.name == "Observed and imputed history"
    )
    assert list(history_trace.y) == [1000.0, 1010.0, 1020.0]
    imputed_trace = next(trace for trace in figure.data if trace.name == "Imputed value")
    assert list(imputed_trace.x) == [pd.Timestamp("2025-01-02")]
    assert all(getattr(trace, "fill", None) != "toself" for trace in figure.data)
