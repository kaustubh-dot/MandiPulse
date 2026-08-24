import { describe, it, afterEach } from "node:test";
import assert from "node:assert/strict";
import "./dom.setup";
import { cleanup, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ForecastChart from "../src/components/ForecastChart";
import { loadFixture } from "./dom.setup";
import { filterForecastHistory } from "../src/lib/policy";
import type { ForecastRow, PriceHistoryRow } from "../src/lib/types";
import { renderWithRouter } from "./router-stub";

afterEach(() => {
  cleanup();
});

const history = loadFixture<PriceHistoryRow[]>("price_history.json");
const forecasts = loadFixture<ForecastRow[]>("forecasts.json");

const eligible =
  forecasts.find(
    (row) =>
      row.as_of_date === "2025-10-30" && row.market_id === 2494
  ) ?? forecasts.find((row) => row.as_of_date === "2025-10-30")!;
const chartHistory = filterForecastHistory(history, eligible.market_id, eligible.as_of_date);

interface Props {
  history: PriceHistoryRow[];
  forecast: ForecastRow | null;
  forecastDate: string | null;
}

function renderChart(overrides: Partial<Props> = {}) {
  return renderWithRouter(
    <ForecastChart
      history={overrides.history ?? chartHistory}
      forecast={"forecast" in overrides ? (overrides.forecast ?? null) : eligible}
      forecastDate={
        "forecastDate" in overrides ? (overrides.forecastDate ?? null) : "2025-11-06"
      }
    />
  );
}

describe("ForecastChart (recharts under jsdom)", () => {
  it("renders the accessible chart summary for real fixture history", async () => {
    renderChart();
    const chart = await screen.findByRole("img");
    const label = chart.getAttribute("aria-label") ?? "";
    const observedCount = chartHistory.filter((row) => !row.is_imputed).length;
    assert.match(label, /^Price line chart:/);
    assert.match(label, new RegExp(`${observedCount} observed daily prices`));
    assert.match(label, /View as table/);
  });

  it("switches to the data-table view with the forecast column populated", async () => {
    const user = userEvent.setup();
    renderChart();
    await screen.findByRole("img");
    await user.click(screen.getByRole("button", { name: "View as table" }));
    const tableRegion = screen.getByRole("region", { name: "Chart series as a data table" });
    assert.match(tableRegion.textContent!, /Daily prices underlying the chart/);
    const bodyRows = tableRegion.querySelectorAll("tbody tr");
    assert.ok(bodyRows.length > 0 && bodyRows.length <= 15);
    assert.match(tableRegion.textContent!, /Forecast \(INR\/qtl\)/);
    assert.match(
      tableRegion.textContent!,
      new RegExp(eligible.forecast_price_inr_qtl.toLocaleString("en-US"))
    );
  });

  it("labels imputed fills in the aria summary when history contains them", async () => {
    const withImputed: PriceHistoryRow[] = [
      ...chartHistory.slice(0, -1),
      { ...chartHistory[chartHistory.length - 1], is_imputed: true },
    ];
    renderChart({ history: withImputed });
    const chart = await screen.findByRole("img");
    assert.match(chart.getAttribute("aria-label")!, /imputed fills/);
  });

  it("renders nothing when no finite prices exist in the window", () => {
    const { container } = renderWithRouter(
      <ForecastChart history={[]} forecast={null} forecastDate={null} />
    );
    assert.equal(container.childElementCount, 0);
  });

  it("still renders from the forecast segment alone when history is empty", async () => {
    renderChart({ history: [] });
    const chart = await screen.findByRole("img");
    assert.match(chart.getAttribute("aria-label")!, /0 observed daily prices/);
  });

  it("renders without a forecast segment when forecast is absent", async () => {
    renderChart({ forecast: null, forecastDate: null });
    const chart = await screen.findByRole("img");
    assert.doesNotMatch(chart.getAttribute("aria-label")!, /forecast segment/);
  });

  it("keeps price series semantic and animations disabled", async () => {
    const { container } = renderChart();
    await screen.findByRole("img");
    await new Promise((resolve) => setTimeout(resolve, 50));
    assert.match(container.innerHTML, /--mp-ink/);
    assert.match(container.innerHTML, /--mp-accent/);
    assert.doesNotMatch(container.innerHTML, /--mp-atlas[^-]/);
  });
});
