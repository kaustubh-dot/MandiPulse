from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def test_overview_has_one_dominant_metric_and_quiet_heading():
    app = AppTest.from_file(str(ROOT / "app" / "streamlit_app.py")).run(timeout=60)
    assert not app.exception
    assert app.title[0].value == "Recommended mandi"
    assert app.metric[0].label == "Transport-adjusted net price"
    assert len(app.metric) <= 5


def test_decision_keeps_inputs_before_result_and_one_primary_metric():
    app = AppTest.from_file(str(ROOT / "app" / "pages" / "1_Decision.py")).run(timeout=60)
    assert not app.exception
    assert app.title[0].value == "Decision workbench"
    labels = [widget.label for widget in app.number_input]
    assert labels[:3] == ["Latitude", "Longitude", "Quantity (quintals)"]
    assert app.metric[0].label == "Transport-adjusted net price"
