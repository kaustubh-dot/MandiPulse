// Unit contract locks for pure decision logic: date helpers, staleness policy,
// interval uniformity, history filtering, ranking pipeline (web/src/lib/policy.ts),
// geometry/risk primitives (web/src/lib/transport.ts) and the strict JSON guard
// in web/src/lib/data.ts.

import { strict as assert } from "node:assert";
import { describe, it } from "node:test";

import { parseStrictJson } from "../src/lib/data";
import {
  addDaysIso,
  daysBehind,
  filterForecastHistory,
  haveUniformIntervalWidths,
  isStaleAsOf,
  rankRecommendationCandidates,
} from "../src/lib/policy";
import { haversineKm, riskLevel } from "../src/lib/transport";
import type { ForecastRow, MandiMeta, Meta, PriceHistoryRow } from "../src/lib/types";

const FARMER_LAT = 19.9975;
const FARMER_LON = 73.78981;

function forecast(
  marketId: number,
  asOfDate: string,
  centre: number,
  halfWidth = 100
): ForecastRow {
  return {
    market_id: marketId,
    mandi_id: `M${marketId}`,
    mandi: `Mandi ${marketId}`,
    as_of_date: asOfDate,
    forecast_price_inr_qtl: centre,
    lower_bound_inr_qtl: centre - halfWidth,
    upper_bound_inr_qtl: centre + halfWidth,
    confidence_level: 0.9,
    risk_level: "low",
  };
}

function metaWith(overrides: Partial<Meta> = {}): Meta {
  return {
    as_of_date: "2025-10-28",
    snapshot_date: "2025-10-30",
    forecast_horizon_days: 7,
    crop: "tomato",
    state: "Maharashtra",
    model_version: "unit",
    confidence_level: 0.9,
    empirical_coverage: 0.88,
    default_farmer: { latitude: FARMER_LAT, longitude: FARMER_LON },
    candidate_policy: {
      rule: "as_of_equals_bundle_max",
      eligible_as_of_date: "2025-10-30",
      eligible_count: 2,
      excluded_stale_count: 1,
    },
    ranking: {
      cost_per_km_per_quintal: 4,
      road_distance_factor: 1.3,
      max_transport_radius_km: 500,
      max_alternatives: 3,
      uncertainty_penalty_weight: 0.5,
      low_max_interval_pct: 0.1,
      high_min_interval_pct: 0.25,
      cost_variation_pct: 12,
    },
    ...overrides,
  };
}

function mandi(
  marketId: number,
  latitude: number,
  longitude: number
): MandiMeta {
  return {
    market_id: marketId,
    mandi_id: `M${marketId}`,
    market_name: `Market ${marketId}`,
    district_name: `District ${marketId}`,
    latitude,
    longitude,
    active_days: 100,
  };
}

describe("addDaysIso", () => {
  it("rolls over months, years and leap days in UTC", () => {
    assert.strictEqual(addDaysIso("2025-01-31", 1), "2025-02-01");
    assert.strictEqual(addDaysIso("2025-12-31", 1), "2026-01-01");
    assert.strictEqual(addDaysIso("2024-02-28", 1), "2024-02-29");
    assert.strictEqual(addDaysIso("2023-02-28", 1), "2023-03-01");
  });

  it("handles zero and negative offsets", () => {
    assert.strictEqual(addDaysIso("2025-10-30", 0), "2025-10-30");
    assert.strictEqual(addDaysIso("2025-10-30", -30), "2025-09-30");
    assert.strictEqual(addDaysIso("2025-01-01", -1), "2024-12-31");
  });

  it("rejects malformed dates instead of coercing", () => {
    assert.throws(() => addDaysIso("20250101", 1));
    assert.throws(() => addDaysIso("2025-1-1", 1));
    assert.throws(() => addDaysIso("not-a-date", 1));
  });
});

describe("daysBehind / isStaleAsOf", () => {
  it("counts whole days between ISO dates", () => {
    assert.strictEqual(daysBehind("2025-10-27", "2025-10-30"), 3);
    assert.strictEqual(daysBehind("2025-10-30", "2025-10-30"), 0);
  });

  it("clamps future dates to zero days behind", () => {
    assert.strictEqual(daysBehind("2025-10-31", "2025-10-30"), 0);
  });

  it("flags staleness strictly beyond zero days", () => {
    assert.strictEqual(isStaleAsOf("2025-10-29", "2025-10-30"), true);
    assert.strictEqual(isStaleAsOf("2025-10-30", "2025-10-30"), false);
    assert.strictEqual(isStaleAsOf("2025-10-31", "2025-10-30"), false);
  });
});

describe("haveUniformIntervalWidths", () => {
  const rows = [forecast(1, "2025-10-30", 2400), forecast(2, "2025-10-30", 2200)];

  it("requires at least two rows", () => {
    assert.strictEqual(haveUniformIntervalWidths([]), false);
    assert.strictEqual(haveUniformIntervalWidths([rows[0]]), false);
  });

  it("accepts equal widths and near-equal widths within tolerance", () => {
    assert.strictEqual(haveUniformIntervalWidths(rows), true);
    const near = [
      forecast(1, "2025-10-30", 100, 100),
      forecast(2, "2025-10-30", 200, 100.0045),
    ];
    assert.strictEqual(haveUniformIntervalWidths(near), true);
  });

  it("rejects widths outside tolerance or with custom tolerance", () => {
    const wider = [
      forecast(1, "2025-10-30", 100, 100),
      forecast(2, "2025-10-30", 200, 100.02),
    ];
    assert.strictEqual(haveUniformIntervalWidths(wider), false);
    const slightlyOff = [
      forecast(1, "2025-10-30", 100, 100),
      forecast(2, "2025-10-30", 200, 100.009),
    ];
    assert.strictEqual(haveUniformIntervalWidths(slightlyOff, 0.001), false);
  });
});

describe("filterForecastHistory", () => {
  const rows: PriceHistoryRow[] = [
    historyRow(1, "2025-08-02", 100),
    historyRow(1, "2025-08-01", 99),
    historyRow(1, "2025-10-30", 150),
    historyRow(2, "2025-09-15", 120),
    historyRow(1, "2025-09-16", null),
    historyRow(1, "2025-09-17", Number.NaN),
    historyRow(1, "2025-10-31", 160),
  ];

  it("keeps only the requested market inside the inclusive window with finite prices", () => {
    const kept = filterForecastHistory(rows, 1, "2025-10-30");
    assert.deepStrictEqual(
      kept.map((row) => row.date),
      ["2025-08-02", "2025-10-30"]
    );
  });

  it("honours a custom window length", () => {
    const kept = filterForecastHistory(rows, 1, "2025-10-30", 7);
    assert.deepStrictEqual(
      kept.map((row) => row.date),
      ["2025-10-30"]
    );
  });
});

function historyRow(
  marketId: number,
  date: string,
  modalPrice: number | null
): PriceHistoryRow {
  return {
    market_id: marketId,
    market_name: `Market ${marketId}`,
    date,
    modal_price_inr_qtl: modalPrice,
    is_imputed: false,
  };
}

describe("rankRecommendationCandidates", () => {
  const forecasts = [
    forecast(1, "2025-10-30", 2400),
    forecast(2, "2025-10-30", 2200),
    forecast(3, "2025-10-28", 3000),
    forecast(4, "2025-10-30", 2600),
  ];
  const mandis = [
    mandi(1, FARMER_LAT, FARMER_LON + 0.1),
    mandi(2, FARMER_LAT, FARMER_LON),
    mandi(3, FARMER_LAT, FARMER_LON + 5),
    mandi(4, FARMER_LAT, FARMER_LON + 5),
  ];
  const meta = metaWith({ candidate_policy: { rule: "as_of_equals_bundle_max", eligible_as_of_date: "2025-10-30", eligible_count: 3, excluded_stale_count: 1 } });

  it("uses the policy as-of date, drops stale forecasts, applies the radius cap and re-ranks", () => {
    const result = rankRecommendationCandidates(
      forecasts,
      mandis,
      FARMER_LAT,
      FARMER_LON,
      meta,
      4
    );

    assert.strictEqual(result.canonicalAsOfDate, "2025-10-30");
    assert.strictEqual(result.eligibleAsOfCount, 3);
    assert.strictEqual(result.excludedStaleCount, 1);
    assert.strictEqual(result.excludedRadiusCount, 1);
    assert.deepStrictEqual(
      result.rows.map((row) => row.market_id),
      [1, 2]
    );
    assert.deepStrictEqual(
      result.rows.map((row) => row.rank),
      [1, 2]
    );
    assert.ok(result.rows.every((row) => row.road_distance_km <= 500));
    assert.ok(result.rows.every((row) => row.staleness_days === 0));
  });

  it("derives transport cost and net price from the caller-supplied rate", () => {
    const result = rankRecommendationCandidates(
      forecasts,
      mandis,
      FARMER_LAT,
      FARMER_LON,
      meta,
      4
    );
    const top = result.rows[0];
    assert.ok(Math.abs(top.air_distance_km - 10.449070979748178) < 1e-9);
    assert.ok(Math.abs(top.road_distance_km - 13.583792273672632) < 1e-9);
    assert.ok(Math.abs(top.estimated_transport_cost_inr_qtl - 54.33516909469053) < 1e-9);
    assert.ok(Math.abs(top.expected_net_price_inr_qtl - 2345.6648309053095) < 1e-9);

    const cheaper = rankRecommendationCandidates(
      forecasts,
      mandis,
      FARMER_LAT,
      FARMER_LON,
      meta,
      2
    );
    assert.ok(
      Math.abs(
        cheaper.rows[0].estimated_transport_cost_inr_qtl - 27.167584547345264
      ) < 1e-9
    );
  });

  it("falls back to meta.as_of_date when the policy date is empty", () => {
    const result = rankRecommendationCandidates(
      forecasts,
      mandis,
      FARMER_LAT,
      FARMER_LON,
      metaWith({ candidate_policy: { rule: "as_of_equals_bundle_max", eligible_as_of_date: "", eligible_count: 0, excluded_stale_count: 0 } }),
      4
    );
    assert.strictEqual(result.canonicalAsOfDate, "2025-10-28");
    assert.strictEqual(result.eligibleAsOfCount, 1);
    assert.deepStrictEqual(
      result.rows.map((row) => row.market_id),
      []
    );
  });

  it("always keeps at least one alternative regardless of max_alternatives", () => {
    const ranking = { ...meta.ranking, max_alternatives: 0 };
    const result = rankRecommendationCandidates(
      forecasts,
      mandis,
      FARMER_LAT,
      FARMER_LON,
      metaWith({ ranking }),
      4
    );
    assert.strictEqual(result.rows.length, 1);
    assert.strictEqual(result.rows[0].rank, 1);
  });
});

describe("haversineKm", () => {
  it("returns zero for identical points and is symmetric", () => {
    assert.strictEqual(haversineKm(FARMER_LAT, FARMER_LON, FARMER_LAT, FARMER_LON), 0);
    const ab = haversineKm(FARMER_LAT, FARMER_LON, 18.5204, 73.8567);
    assert.ok(Math.abs(ab - haversineKm(18.5204, 73.8567, FARMER_LAT, FARMER_LON)) < 1e-12);
  });

  it("matches the quarter great-circle length for a 180-degree span", () => {
    const halfWorld = haversineKm(0, 0, 0, 180);
    assert.ok(Math.abs(halfWorld - Math.PI * 6371) < 1e-6);
  });

  it("reproduces the engine constant for a known short leg", () => {
    const air = haversineKm(FARMER_LAT, FARMER_LON, FARMER_LAT, FARMER_LON + 0.1);
    assert.ok(Math.abs(air - 10.449070979748178) < 1e-9);
  });
});

describe("riskLevel thresholds", () => {
  it("classifies relWidth against ratio bounds inclusively", () => {
    assert.strictEqual(riskLevel(0.1, 0.1, 0.25), "low");
    assert.strictEqual(riskLevel(0.1000001, 0.1, 0.25), "medium");
    assert.strictEqual(riskLevel(0.2499, 0.1, 0.25), "medium");
    assert.strictEqual(riskLevel(0.25, 0.1, 0.25), "high");
    assert.strictEqual(riskLevel(0.9, 0.1, 0.25), "high");
  });
});

describe("parseStrictJson schema guard", () => {
  it("parses valid payloads unchanged", () => {
    assert.deepStrictEqual(parseStrictJson('{"schema_version":"v2"}'), {
      schema_version: "v2",
    });
    assert.deepStrictEqual(parseStrictJson<number[]>("[1,2]"), [1, 2]);
  });

  it("wraps syntax errors with the payload path", () => {
    assert.throws(() => parseStrictJson('{"a":', "meta.json"), /Invalid strict JSON in meta\.json:/);
    assert.throws(() => parseStrictJson("{bad}"), /Invalid strict JSON in JSON payload:/);
  });
});
