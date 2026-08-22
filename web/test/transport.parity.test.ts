// Parity test: TS rankMandis() must match Python score_recommendations() output
// within 0.01 INR/qtl at the default farmer location.
// Python output is committed in web/public/data/recommendations.json.
// Run: npm test (requires tsx + node >=20)

import { strict as assert } from "node:assert";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { rankRecommendationCandidates } from "../src/lib/policy";
import type { ForecastRow, MandiMeta, Meta, RankedMandi } from "../src/lib/types";

const DATA = resolve(__dirname, "../public/data");

function load<T>(name: string): T {
  return JSON.parse(readFileSync(resolve(DATA, name), "utf8")) as T;
}

const TOLERANCE = 0.01; // INR/qtl

describe("TS rankMandis parity with Python score_recommendations", () => {
  const meta = load<Meta>("meta.json");
  const mandis = load<MandiMeta[]>("mandis.json");
  const forecasts = load<ForecastRow[]>("forecasts.json");
  const pyRecs = load<RankedMandi[]>("recommendations.json");

  const { latitude, longitude } = meta.default_farmer;
  const tsRecs = rankRecommendationCandidates(
    forecasts,
    mandis,
    latitude,
    longitude,
    meta,
    meta.ranking.cost_per_km_per_quintal
  ).rows;

  it("same number of ranked mandis", () => {
    assert.strictEqual(tsRecs.length, pyRecs.length, "mandi count mismatch");
  });

  for (const pyRow of pyRecs) {
    const marketId = pyRow.market_id;
    const mandiName = pyRow.mandi;

    it(`${mandiName} (market_id=${marketId}) rank matches`, () => {
      const tsRow = tsRecs.find((r) => r.market_id === marketId);
      assert.ok(tsRow, `market_id ${marketId} missing from TS output`);
      assert.strictEqual(tsRow.rank, pyRow.rank, `rank mismatch for ${mandiName}`);
    });

    it(`${mandiName} transport_adjusted_net_price within ${TOLERANCE}`, () => {
      const tsRow = tsRecs.find((r) => r.market_id === marketId)!;
      assert.ok(
        Math.abs(
          tsRow.transport_adjusted_net_price_inr_qtl -
            pyRow.transport_adjusted_net_price_inr_qtl
        ) <= TOLERANCE,
        `transport_adjusted_net_price_inr_qtl: TS=${tsRow.transport_adjusted_net_price_inr_qtl.toFixed(4)} py=${pyRow.transport_adjusted_net_price_inr_qtl}`
      );
    });

    it(`${mandiName} estimated_transport_cost within ${TOLERANCE}`, () => {
      const tsRow = tsRecs.find((r) => r.market_id === marketId)!;
      assert.ok(
        Math.abs(
          tsRow.estimated_transport_cost_inr_qtl - pyRow.estimated_transport_cost_inr_qtl
        ) <= TOLERANCE,
        `transport: TS=${tsRow.estimated_transport_cost_inr_qtl.toFixed(4)} py=${pyRow.estimated_transport_cost_inr_qtl}`
      );
    });

    it(`${mandiName} expected_net_price within ${TOLERANCE}`, () => {
      const tsRow = tsRecs.find((r) => r.market_id === marketId)!;
      assert.ok(
        Math.abs(
          tsRow.expected_net_price_inr_qtl - pyRow.expected_net_price_inr_qtl
        ) <= TOLERANCE,
        `net price: TS=${tsRow.expected_net_price_inr_qtl.toFixed(4)} py=${pyRow.expected_net_price_inr_qtl}`
      );
    });

    it(`${mandiName} risk_level matches`, () => {
      const tsRow = tsRecs.find((r) => r.market_id === marketId)!;
      assert.strictEqual(
        tsRow.risk_level,
        pyRow.risk_level,
        `risk_level: TS=${tsRow.risk_level} py=${pyRow.risk_level}`
      );
    });
  }
});

describe("recommendation input policy", () => {
  const meta = load<Meta>("meta.json");
  const mandis = load<MandiMeta[]>("mandis.json");
  const forecasts = load<ForecastRow[]>("forecasts.json");

  it("applies a caller-selected radius and re-ranks the remaining rows", () => {
    const result = rankRecommendationCandidates(
      forecasts,
      mandis,
      meta.default_farmer.latitude,
      meta.default_farmer.longitude,
      meta,
      meta.ranking.cost_per_km_per_quintal,
      100
    );

    assert.ok(result.rows.length > 0);
    assert.ok(result.rows.every((row) => row.road_distance_km <= 100));
    assert.deepStrictEqual(
      result.rows.map((row) => row.rank),
      result.rows.map((_, index) => index + 1)
    );
    assert.strictEqual(result.excludedRadiusCount, 8);
  });
});
