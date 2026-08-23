// Contract locks for decision URL-state encoding/decoding and input validation.
// These helpers live in web/src/components/RecommendationControls.tsx and are
// importable under tsx without jsdom (verified: no top-level DOM access).

import { strict as assert } from "node:assert";
import { describe, it } from "node:test";

import {
  DECISION_DEFAULTS,
  FARMER_PRESETS,
  parseDecisionParams,
  serializeDecisionParams,
  validateDecisionInput,
} from "../src/components/RecommendationControls";
import type { DecisionField } from "../src/components/RecommendationControls";

const FIELDS: DecisionField[] = ["lat", "lon", "quantity", "rate", "radius"];

describe("DECISION_DEFAULTS", () => {
  it("pins the default draft strings", () => {
    assert.deepStrictEqual(DECISION_DEFAULTS, {
      lat: "19.9975",
      lon: "73.78981",
      quantity: "100",
      rate: "4",
      radius: "500",
    });
  });

  it("keeps the Nashik preset in sync with the defaults", () => {
    assert.strictEqual(FARMER_PRESETS[0].lat, Number(DECISION_DEFAULTS.lat));
    assert.strictEqual(FARMER_PRESETS[0].lon, Number(DECISION_DEFAULTS.lon));
  });
});

describe("serializeDecisionParams", () => {
  it("emits compact short-name params in a fixed field order", () => {
    assert.strictEqual(
      serializeDecisionParams({ lat: 19.9975, lon: 73.78981, quantity: 100, rate: 4, radius: 500 }),
      "lat=19.9975&lon=73.78981&q=100&r=4&rad=500"
    );
  });

  it("encodes negatives, decimals and zero rate without spaces", () => {
    assert.strictEqual(
      serializeDecisionParams({ lat: -33.5, lon: 150.25, quantity: 7.5, rate: 0, radius: 12 }),
      "lat=-33.5&lon=150.25&q=7.5&r=0&rad=12"
    );
  });
});

describe("parseDecisionParams", () => {
  it("reads all five fields from a serialized state", () => {
    const drafts = parseDecisionParams(
      new URLSearchParams("lat=18.5204&lon=73.8567&q=250&r=4.5&rad=120")
    );
    assert.deepStrictEqual(drafts, {
      lat: "18.5204",
      lon: "73.8567",
      quantity: "250",
      rate: "4.5",
      radius: "120",
    });
  });

  it("round-trips serialize output into numeric-equivalent drafts", () => {
    const values = { lat: 16.705, lon: 74.2433, quantity: 42, rate: 3.75, radius: 60 };
    const qs = serializeDecisionParams(values);
    const drafts = parseDecisionParams(new URLSearchParams(qs));
    for (const field of FIELDS) {
      assert.strictEqual(drafts[field], String(values[field]));
      assert.ok(field in drafts);
      assert.strictEqual(Number(drafts[field]), values[field]);
    }
  });

  it("trims surrounding whitespace but preserves the raw literal", () => {
    const drafts = parseDecisionParams(new URLSearchParams("lat=%2019.9%20&q=1e2"));
    assert.strictEqual(drafts.lat, "19.9");
    assert.strictEqual(drafts.quantity, "1e2");
  });

  it("omits missing params instead of defaulting them", () => {
    const drafts = parseDecisionParams(new URLSearchParams("q=42"));
    assert.deepStrictEqual(Object.keys(drafts), ["quantity"]);
    assert.ok(!("radius" in drafts));
    assert.ok(!("lat" in drafts));
  });

  it("ignores unknown params", () => {
    const drafts = parseDecisionParams(new URLSearchParams("foo=bar&lat=19"));
    assert.deepStrictEqual(drafts, { lat: "19" });
  });

  it("rejects out-of-range or non-numeric values per field", () => {
    assert.deepStrictEqual(parseDecisionParams(new URLSearchParams("lat=91")), {});
    assert.deepStrictEqual(parseDecisionParams(new URLSearchParams("lat=-90.000001")), {});
    assert.deepStrictEqual(parseDecisionParams(new URLSearchParams("lon=180.1")), {});
    assert.deepStrictEqual(parseDecisionParams(new URLSearchParams("lon=-181")), {});
    assert.deepStrictEqual(parseDecisionParams(new URLSearchParams("q=0")), {});
    assert.deepStrictEqual(parseDecisionParams(new URLSearchParams("q=-5")), {});
    assert.deepStrictEqual(parseDecisionParams(new URLSearchParams("q=abc")), {});
    assert.deepStrictEqual(parseDecisionParams(new URLSearchParams("r=-0.5")), {});
    assert.deepStrictEqual(parseDecisionParams(new URLSearchParams("rad=0")), {});
    assert.deepStrictEqual(parseDecisionParams(new URLSearchParams("rad=-1")), {});
    assert.deepStrictEqual(parseDecisionParams(new URLSearchParams("lat=&lon=")), {});
  });

  it("keeps valid boundary values", () => {
    const drafts = parseDecisionParams(
      new URLSearchParams("lat=90&lon=-180&q=0.5&r=0&rad=0.1")
    );
    assert.deepStrictEqual(drafts, {
      lat: "90",
      lon: "-180",
      quantity: "0.5",
      rate: "0",
      radius: "0.1",
    });
  });

  it("drops only the offending field when mixed with valid ones", () => {
    const drafts = parseDecisionParams(
      new URLSearchParams("lat=19.9&q=not-a-number&r=2")
    );
    assert.deepStrictEqual(drafts, { lat: "19.9", rate: "2" });
  });
});

describe("validateDecisionInput", () => {
  it("requires a finite number first", () => {
    assert.strictEqual(validateDecisionInput("lat", ""), "Enter a number.");
    assert.strictEqual(validateDecisionInput("quantity", "   "), "Enter a number.");
    assert.strictEqual(validateDecisionInput("rate", "abc"), "Enter a number.");
    assert.strictEqual(validateDecisionInput("radius", "Infinity"), "Enter a number.");
  });

  it("locks exact range messages using the unicode minus", () => {
    assert.strictEqual(
      validateDecisionInput("lat", "90.0001"),
      "Latitude must be between \u221290 and 90 degrees."
    );
    assert.strictEqual(
      validateDecisionInput("lat", "-91"),
      "Latitude must be between \u221290 and 90 degrees."
    );
    assert.strictEqual(
      validateDecisionInput("lon", "-180.5"),
      "Longitude must be between \u2212180 and 180 degrees."
    );
    assert.strictEqual(
      validateDecisionInput("lon", "999"),
      "Longitude must be between \u2212180 and 180 degrees."
    );
  });

  it("locks positivity and non-negativity messages", () => {
    assert.strictEqual(
      validateDecisionInput("quantity", "0"),
      "Quantity must be greater than 0 quintals."
    );
    assert.strictEqual(
      validateDecisionInput("radius", "0"),
      "Road radius must be greater than 0 km."
    );
    assert.strictEqual(
      validateDecisionInput("rate", "-1"),
      "Transport rate cannot be negative."
    );
  });

  it("returns undefined for acceptable inputs at boundaries", () => {
    assert.strictEqual(validateDecisionInput("lat", "90"), undefined);
    assert.strictEqual(validateDecisionInput("lat", "-90"), undefined);
    assert.strictEqual(validateDecisionInput("lon", "180"), undefined);
    assert.strictEqual(validateDecisionInput("lon", "-180"), undefined);
    assert.strictEqual(validateDecisionInput("quantity", "0.001"), undefined);
    assert.strictEqual(validateDecisionInput("rate", "0"), undefined);
    assert.strictEqual(validateDecisionInput("radius", "500"), undefined);
  });
});
