// Scenario C (release gate RG-09): cross-surface parity at a far-haul farmer
// location. The Python engine ordering for this scenario is committed in
// tests/golden/recommendation_outputs_7d_nagpur.csv (farmer 21.1458, 79.0882,
// 60 qtl, 4 INR/km/quintal). The TS ranking path must reproduce it.
// Run: npm test (requires tsx + node >=20)

import { strict as assert } from "node:assert";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { rankRecommendationCandidates } from "../src/lib/policy";
import type { ForecastRow, MandiMeta, Meta } from "../src/lib/types";

const DATA = resolve(__dirname, "../public/data");
const GOLDEN_CSV = resolve(
  __dirname,
  "../../tests/golden/recommendation_outputs_7d_nagpur.csv"
);

const TOLERANCE = 0.01; // INR/qtl

function load<T>(name: string): T {
  return JSON.parse(readFileSync(resolve(DATA, name), "utf8")) as T;
}

interface GoldenScenarioCRow {
  rank: number;
  market_id: number;
  mandi_id: string;
  mandi: string;
  expected_net_price_inr_qtl: number;
  estimated_transport_cost_inr_qtl: number;
}

function parseCsv(text: string): string[][] {
  // Minimal RFC-4180 parser: quoted fields may contain commas/quotes.
  const rows: string[][] = [];
  let row: string[] = [];
  let field = "";
  let inQuotes = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (inQuotes) {
      if (ch === '"') {
        if (text[i + 1] === '"') {
          field += '"';
          i++;
        } else {
          inQuotes = false;
        }
      } else {
        field += ch;
      }
    } else if (ch === '"') {
      inQuotes = true;
    } else if (ch === ",") {
      row.push(field);
      field = "";
    } else if (ch === "\n" || ch === "\r") {
      if (ch === "\r" && text[i + 1] === "\n") i++;
      row.push(field);
      field = "";
      rows.push(row);
      row = [];
    } else {
      field += ch;
    }
  }
  if (field.length > 0 || row.length > 0) {
    row.push(field);
    rows.push(row);
  }
  return rows.filter((r) => r.length > 1 || r[0] !== "");
}

function loadGoldenScenarioC(): GoldenScenarioCRow[] {
  const rows = parseCsv(readFileSync(GOLDEN_CSV, "utf8"));
  const header = rows[0];
  const idx = (name: string): number => {
    const i = header.indexOf(name);
    assert.ok(i >= 0, `fixture column missing: ${name}`);
    return i;
  };
  const c = {
    rank: idx("rank"),
    market_id: idx("market_id"),
    mandi_id: idx("mandi_id"),
    mandi: idx("mandi"),
    net: idx("expected_net_price_inr_qtl"),
    transport: idx("estimated_transport_cost_inr_qtl"),
  };
  return rows.slice(1).map((r) => ({
    rank: Number(r[c.rank]),
    market_id: Number(r[c.market_id]),
    mandi_id: r[c.mandi_id],
    mandi: r[c.mandi],
    expected_net_price_inr_qtl: Number(r[c.net]),
    estimated_transport_cost_inr_qtl: Number(r[c.transport]),
  }));
}

describe("scenario C parity: TS ranking vs committed Nagpur golden", () => {
  const meta = load<Meta>("meta.json");
  const mandis = load<MandiMeta[]>("mandis.json");
  const forecasts = load<ForecastRow[]>("forecasts.json");

  const SCENARIO_C_LATITUDE = 21.1458;
  const SCENARIO_C_LONGITUDE = 79.0882;

  const golden = loadGoldenScenarioC();

  // Every scenario C candidate sits beyond the default 500 km display radius
  // (closest is ~542 km road), so the radius cap is lifted here to compare the
  // underlying engine ordering — exactly what the radius-free Python engine
  // records in the fixture.
  const tsRecs = rankRecommendationCandidates(
    forecasts,
    mandis,
    SCENARIO_C_LATITUDE,
    SCENARIO_C_LONGITUDE,
    meta,
    meta.ranking.cost_per_km_per_quintal,
    Number.POSITIVE_INFINITY
  ).rows;

  it("same number of ranked candidates as the fixture", () => {
    assert.strictEqual(tsRecs.length, golden.length, "candidate count mismatch");
    assert.strictEqual(golden.length, 10);
  });

  it("top-1 mandi id and net price match the fixture", () => {
    assert.strictEqual(tsRecs[0].market_id, golden[0].market_id);
    assert.strictEqual(tsRecs[0].mandi_id, "maharashtra__chattrapati_sambhajinagar");
    assert.strictEqual(tsRecs[0].mandi_id, golden[0].mandi_id);
    assert.ok(
      Math.abs(
        tsRecs[0].expected_net_price_inr_qtl - golden[0].expected_net_price_inr_qtl
      ) <= TOLERANCE,
      `net price: TS=${tsRecs[0].expected_net_price_inr_qtl.toFixed(4)} golden=${golden[0].expected_net_price_inr_qtl}`
    );
  });

  it("sequential ranks match the fixture order", () => {
    assert.deepStrictEqual(
      tsRecs.map((row) => row.rank),
      golden.map((row) => row.rank)
    );
    assert.deepStrictEqual(
      tsRecs.map((row) => row.market_id),
      golden.map((row) => row.market_id)
    );
  });

  for (const goldenRow of golden) {
    it(`${goldenRow.mandi} (market_id=${goldenRow.market_id}) net price within ${TOLERANCE}`, () => {
      const tsRow = tsRecs.find((r) => r.market_id === goldenRow.market_id);
      assert.ok(tsRow, `market_id ${goldenRow.market_id} missing from TS output`);
      assert.ok(
        Math.abs(
          tsRow.expected_net_price_inr_qtl - goldenRow.expected_net_price_inr_qtl
        ) <= TOLERANCE,
        `net price: TS=${tsRow.expected_net_price_inr_qtl.toFixed(4)} golden=${goldenRow.expected_net_price_inr_qtl}`
      );
    });

    it(`${goldenRow.mandi} transport cost within ${TOLERANCE}`, () => {
      const tsRow = tsRecs.find((r) => r.market_id === goldenRow.market_id)!;
      assert.ok(
        Math.abs(
          tsRow.estimated_transport_cost_inr_qtl -
            goldenRow.estimated_transport_cost_inr_qtl
        ) <= TOLERANCE,
        `transport: TS=${tsRow.estimated_transport_cost_inr_qtl.toFixed(4)} golden=${goldenRow.estimated_transport_cost_inr_qtl}`
      );
    });
  }

  it("default 500 km radius policy excludes every scenario C candidate", () => {
    const capped = rankRecommendationCandidates(
      forecasts,
      mandis,
      SCENARIO_C_LATITUDE,
      SCENARIO_C_LONGITUDE,
      meta,
      meta.ranking.cost_per_km_per_quintal
    );
    assert.strictEqual(capped.rows.length, 0);
    assert.strictEqual(capped.excludedRadiusCount, 10);
  });
});
