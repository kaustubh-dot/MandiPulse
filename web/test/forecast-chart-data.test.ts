import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  buildForecastChartModel,
  formatForecastDateTick,
  formatForecastPriceTick,
} from "../src/lib/forecastChart";
import type { ForecastRow, PriceHistoryRow } from "../src/lib/types";

const history: PriceHistoryRow[] = [
  {
    market_id: 2484,
    market_name: "Lasalgaon(Niphad)",
    date: "2025-01-01",
    modal_price_inr_qtl: 1000,
    is_imputed: false,
  },
  {
    market_id: 2484,
    market_name: "Lasalgaon(Niphad)",
    date: "2025-01-02",
    modal_price_inr_qtl: 1010,
    is_imputed: true,
  },
  {
    market_id: 2484,
    market_name: "Lasalgaon(Niphad)",
    date: "2025-01-03",
    modal_price_inr_qtl: 1020,
    is_imputed: false,
  },
];

const forecast: ForecastRow = {
  market_id: 2484,
  mandi_id: "maharashtra__lasalgaonniphad",
  mandi: "Lasalgaon(Niphad)",
  as_of_date: "2025-01-03",
  forecast_price_inr_qtl: 1050,
  lower_bound_inr_qtl: 830,
  upper_bound_inr_qtl: 1340,
  confidence_level: 0.9,
  risk_level: "high",
};

describe("buildForecastChartModel", () => {
  it("keeps imputed prices on the continuous history series", () => {
    const model = buildForecastChartModel(history, forecast, "2025-01-10");

    assert.deepEqual(
      model.historyPoints.map((point) => point.price),
      [1000, 1010, 1020]
    );
    assert.equal(model.historyPoints[1].imputed, 1010);
    assert.equal(model.historyPoints[0].imputed, undefined);
  });

  it("keeps the forecast at the target date instead of drawing a horizon band", () => {
    const model = buildForecastChartModel(history, forecast, "2025-01-10");

    assert.deepEqual(model.endpoint, {
      date: "2025-01-10",
      forecast: 1050,
      lower: 830,
      upper: 1340,
      confidenceLevel: 0.9,
    });
    assert.equal(
      model.tablePoints.filter((point) => point.forecast !== undefined).length,
      1
    );
  });

  it("derives a shared finite domain that contains history and interval bounds", () => {
    const model = buildForecastChartModel(history, forecast, "2025-01-10");

    assert.ok(model.yDomain[0] < 830);
    assert.ok(model.yDomain[1] > 1340);
    assert.ok(model.yDomain.every(Number.isFinite));
  });
});

describe("forecast chart axis labels", () => {
  it("keeps date ticks short enough for the mobile history plot", () => {
    assert.equal(formatForecastDateTick("2025-07-21"), "21 Jul");
  });

  it("rounds padded-domain price ticks to readable whole rupees", () => {
    assert.equal(formatForecastPriceTick(1714.32), "1,714");
  });
});
