"""F6-06 Streamlit smoke checks: server health, app shell, every page, ranking fixture.

Hermetic by construction: traffic stays on 127.0.0.1, artifacts come from the
committed snapshot/sample bundle, and server logs go to pytest tmp dirs.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from contextlib import suppress
from pathlib import Path
from typing import Iterator

import pandas as pd
import pytest
import requests

from mandipulse.app.data_access import add_staleness_days
from mandipulse.app.design import ACCENT_HEX, INK_HEX, MUTED_HEX
from mandipulse.policy import canonical_forecast_as_of, select_recommendation_candidates
from mandipulse.recommend.engine import score_recommendations

pytestmark = pytest.mark.streamlit_smoke

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_ENTRYPOINT = REPO_ROOT / "app" / "streamlit_app.py"
PAGE_DIR = REPO_ROOT / "app" / "pages"
MANDIS_PATH = REPO_ROOT / "data" / "external" / "mvp_mandis.csv"

HEALTH_TIMEOUT_SECONDS = 60.0
POLL_INTERVAL_SECONDS = 0.5

# Same scenario as tests/test_pipeline_smoke.py: reproduces the committed
# recommendation artifact from the golden forecast bundle.
REC_KWARGS: dict = dict(
    farmer_latitude=19.99750,
    farmer_longitude=73.78981,
    cost_per_km_per_quintal=4.0,
    road_distance_factor=1.3,
    uncertainty_penalty_weight=0.3,
    low_max_interval_pct=0.10,
    high_min_interval_pct=0.25,
    candidate_state="maharashtra",
)

# Scenario C (RG-09 cross-surface parity): farmer at Nagpur, 60 qtl load.
# Exercises a far-haul distance regime; every eligible candidate sits beyond
# the 500 km display radius, so parity is asserted on the radius-free engine
# ordering shared with web/test/scenario-c.parity.test.ts.
SCENARIO_C_KWARGS: dict = dict(
    farmer_latitude=21.1458,
    farmer_longitude=79.0882,
    cost_per_km_per_quintal=4.0,
    road_distance_factor=1.3,
    uncertainty_penalty_weight=0.3,
    low_max_interval_pct=0.10,
    high_min_interval_pct=0.25,
    candidate_state="maharashtra",
)

# Streamlit discovers multipage apps by filename; each page runs its full
# top-level body here in bare mode, where widgets return their defaults.
PAGE_EXPECTED_NAMES: dict[str, tuple[str, ...]] = {
    "1_Decision.py": ("_risk_label", "_arithmetic_sentence", "_ranking_table", "_candidate_map"),
    "2_Forecast.py": (
        "_default_mandi_name",
        "_selected_forecast_row",
        "_build_forecast_figure",
        "_data_quality_note",
    ),
    "3_Coverage.py": (
        "compute_mandi_coverage",
        "coverage_display_frame",
        "focus_window_chart",
        "render_missing_artifact_notice",
        "render_trainability",
    ),
}


def _free_tcp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _log_tail(log_path: Path, limit: int = 1500) -> str:
    try:
        return log_path.read_text(encoding="utf-8", errors="replace")[-limit:]
    except OSError:
        return "<server log unavailable>"


def _stop_streamlit_server(proc: subprocess.Popen) -> None:
    """Kill the server process tree; escalate to SIGKILL if the grace wait lapses."""
    if proc.poll() is None:
        if sys.platform.startswith("win"):
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                capture_output=True,
                check=False,
            )
        else:
            with suppress(ProcessLookupError):
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    try:
        proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=10)


def _wait_until_healthy(base_url: str, proc: subprocess.Popen, log_path: Path) -> None:
    deadline = time.monotonic() + HEALTH_TIMEOUT_SECONDS
    last_error = "no response yet"
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            pytest.fail(
                f"Streamlit exited early with code {proc.returncode}.\n{_log_tail(log_path)}"
            )
        try:
            response = requests.get(f"{base_url}/_stcore/health", timeout=2)
            if response.status_code == 200 and response.text.strip() == "ok":
                return
            last_error = f"HTTP {response.status_code}"
        except requests.RequestException as exc:
            last_error = str(exc)
        time.sleep(POLL_INTERVAL_SECONDS)
    pytest.fail(f"Streamlit health check timed out ({last_error}).\n{_log_tail(log_path)}")


@pytest.fixture(scope="session")
def streamlit_base_url() -> Iterator[str]:
    port = _free_tcp_port()
    base_url = f"http://127.0.0.1:{port}"
    log_dir = Path(tempfile.mkdtemp(prefix="streamlit_smoke_"))
    log_path = log_dir / "server.log"
    popen_kwargs: dict = {}
    if sys.platform.startswith("win"):
        popen_kwargs["creationflags"] = (
            subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
        )
    else:
        popen_kwargs["start_new_session"] = True
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(APP_ENTRYPOINT),
        "--server.headless",
        "true",
        "--server.address",
        "127.0.0.1",
        "--server.port",
        str(port),
        "--browser.gatherUsageStats",
        "false",
    ]
    with log_path.open("w", encoding="utf-8") as log_file:
        proc = subprocess.Popen(
            command,
            cwd=str(REPO_ROOT),
            stdout=log_file,
            stderr=subprocess.STDOUT,
            env=dict(os.environ, PYTHONIOENCODING="utf-8"),
            **popen_kwargs,
        )
        try:
            _wait_until_healthy(base_url, proc, log_path)
            yield base_url
        finally:
            _stop_streamlit_server(proc)
            shutil.rmtree(log_dir, ignore_errors=True)


def _run_streamlit_script(path: Path):
    spec = importlib.util.spec_from_file_location(f"_mp_smoke_{path.stem}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestServerHealth:
    def test_health_endpoint_reports_ok(self, streamlit_base_url: str) -> None:
        response = requests.get(f"{streamlit_base_url}/_stcore/health", timeout=10)
        assert response.status_code == 200
        assert response.text.strip() == "ok"


class TestAppShell:
    def test_root_url_serves_html_shell(self, streamlit_base_url: str) -> None:
        response = requests.get(f"{streamlit_base_url}/", timeout=30)
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        assert "<html" in response.text.lower()


class TestPageModules:
    @pytest.mark.parametrize(("filename", "expected_names"), sorted(PAGE_EXPECTED_NAMES.items()))
    def test_page_executes_and_exposes_helpers(
        self, filename: str, expected_names: tuple[str, ...]
    ) -> None:
        module = _run_streamlit_script(PAGE_DIR / filename)
        missing = [name for name in expected_names if not callable(getattr(module, name, None))]
        assert not missing, f"{filename} is missing expected helpers: {missing}"

    def test_overview_decision_preview_ranks_pimpalgaon_first(self) -> None:
        module = _run_streamlit_script(APP_ENTRYPOINT)
        ranked = getattr(module, "ranked")
        assert isinstance(ranked, pd.DataFrame)
        assert len(ranked) > 0
        assert "Pimpalgaon" in str(ranked.iloc[0]["mandi"])
        assert list(ranked["rank"]) == list(range(1, len(ranked) + 1))

    def test_decision_map_uses_current_plotly_map_traces_and_semantic_colors(self) -> None:
        module = _run_streamlit_script(PAGE_DIR / "1_Decision.py")
        figure = module._candidate_map(module.display_frame, module.DEFAULT_LAT, module.DEFAULT_LON)

        assert {trace.type for trace in figure.data} == {"scattermap"}
        assert [trace.marker.color for trace in figure.data] == [MUTED_HEX, ACCENT_HEX, INK_HEX]

    def test_canonical_as_of_matches_frozen_snapshot(self, golden_forecasts: pd.DataFrame) -> None:
        as_of = canonical_forecast_as_of(golden_forecasts)
        candidates = select_recommendation_candidates(golden_forecasts)
        assert str(as_of) == "2025-10-30"
        assert len(candidates) > 0


class TestRecommendationFixtureParity:
    @staticmethod
    def _score(golden_forecasts: pd.DataFrame, kwargs: dict) -> pd.DataFrame:
        candidates = select_recommendation_candidates(add_staleness_days(golden_forecasts))
        mandis = pd.read_csv(MANDIS_PATH).dropna(subset=["latitude", "longitude"])
        return score_recommendations(candidates, mandis, **kwargs)

    def test_pune_pimpri_net_price_arithmetic(
        self,
        golden_forecasts: pd.DataFrame,
        golden_recommendations: pd.DataFrame,
    ) -> None:
        recs = self._score(golden_forecasts, REC_KWARGS)

        pimpri = recs.loc[recs["mandi"] == "Pune(Pimpri)"]
        assert len(pimpri) == 1
        row = pimpri.iloc[0]
        forecast = float(row["forecast_price_inr_qtl"])
        transport = float(row["estimated_transport_cost_inr_qtl"])
        net = float(row["expected_net_price_inr_qtl"])

        assert forecast == pytest.approx(1392.857142857143, rel=1e-9)
        assert transport == pytest.approx(800.3772371255968, rel=1e-6)
        assert net == pytest.approx(592.4799057315461, rel=1e-6)
        assert net == pytest.approx(forecast - transport, abs=1e-9)
        assert float(row["transport_adjusted_net_price_inr_qtl"]) == pytest.approx(net)

        golden_row = golden_recommendations.loc[
            golden_recommendations["market_id"] == int(row["market_id"])
        ].iloc[0]
        assert float(golden_row["transport_adjusted_net_price_inr_qtl"]) == pytest.approx(
            net, rel=1e-9
        )

    def test_ranking_orders_by_transport_adjusted_net_descending(
        self,
        golden_forecasts: pd.DataFrame,
    ) -> None:
        recs = self._score(golden_forecasts, REC_KWARGS)
        nets = recs["transport_adjusted_net_price_inr_qtl"].tolist()
        assert nets == sorted(nets, reverse=True)

    def test_scenario_c_nagpur_rank_1_matches_golden(
        self,
        golden_forecasts: pd.DataFrame,
        golden_scenario_c_recommendations: pd.DataFrame,
    ) -> None:
        recs = self._score(golden_forecasts, SCENARIO_C_KWARGS)
        top = recs.loc[recs["rank"] == 1].iloc[0]
        golden_top = golden_scenario_c_recommendations.loc[
            golden_scenario_c_recommendations["rank"] == 1
        ].iloc[0]

        assert int(top["market_id"]) == 581
        assert str(top["mandi_id"]) == "maharashtra__chattrapati_sambhajinagar"
        assert "Chattrapati Sambhajinagar" in str(top["mandi"])
        assert str(golden_top["mandi_id"]) == str(top["mandi_id"])
        assert float(top["expected_net_price_inr_qtl"]) == pytest.approx(
            float(golden_top["expected_net_price_inr_qtl"]), rel=1e-9
        )
        # Scenario context is recorded in the fixture header columns.
        assert float(golden_top["farmer_latitude"]) == pytest.approx(21.1458)
        assert float(golden_top["quantity_quintal"]) == pytest.approx(60.0)

    def test_scenario_c_full_candidate_ordering_matches_golden(
        self,
        golden_forecasts: pd.DataFrame,
        golden_scenario_c_recommendations: pd.DataFrame,
    ) -> None:
        recs = self._score(golden_forecasts, SCENARIO_C_KWARGS).set_index("market_id")
        golden = golden_scenario_c_recommendations.set_index("market_id")

        assert list(recs.index) == list(golden.index)
        assert recs["rank"].tolist() == list(range(1, len(recs) + 1))
        assert golden["rank"].tolist() == recs["rank"].tolist()
        for column in (
            "estimated_transport_cost_inr_qtl",
            "expected_net_price_inr_qtl",
            "transport_adjusted_net_price_inr_qtl",
        ):
            diff = (recs[column] - golden[column]).abs().max()
            assert diff < 1e-6, f"{column} deviates by {diff}"
