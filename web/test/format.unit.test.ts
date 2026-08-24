// Contract locks for shared display formatters (web/src/lib/format.ts).
// Expected strings mirror src/mandipulse/app/design.py output exactly.

import { strict as assert } from "node:assert";
import { describe, it } from "node:test";

import {
  EM_DASH,
  formatDateIso,
  formatInr,
  formatInrPerQtl,
  formatInterval,
  formatKm,
  formatPct,
  formatQuantity,
} from "../src/lib/format";

describe("EM_DASH sentinel", () => {
  it("is U+2014", () => {
    assert.strictEqual(EM_DASH, "\u2014");
  });
});

describe("formatInrPerQtl", () => {
  it("groups thousands with no decimals by default", () => {
    assert.strictEqual(formatInrPerQtl(2275), "2,275 INR/qtl");
    assert.strictEqual(formatInrPerQtl(1234.567), "1,235 INR/qtl");
  });

  it("honours explicit decimals and rounds half-away-from-zero", () => {
    assert.strictEqual(formatInrPerQtl(1234.567, 2), "1,234.57 INR/qtl");
    assert.strictEqual(formatInrPerQtl(2200.5, 1), "2,200.5 INR/qtl");
  });

  it("formats zero and negatives", () => {
    assert.strictEqual(formatInrPerQtl(0), "0 INR/qtl");
    assert.strictEqual(formatInrPerQtl(-1234), "-1,234 INR/qtl");
  });

  it("renders the em dash placeholder plus unit for missing values", () => {
    assert.strictEqual(formatInrPerQtl(null), "\u2014 INR/qtl");
    assert.strictEqual(formatInrPerQtl(undefined), "\u2014 INR/qtl");
    assert.strictEqual(formatInrPerQtl(Number.NaN), "\u2014 INR/qtl");
  });
});

describe("formatInr", () => {
  it("defaults to two decimals with grouping", () => {
    assert.strictEqual(formatInr(1234.5), "1,234.50 INR");
    assert.strictEqual(formatInr(0), "0.00 INR");
  });

  it("supports custom decimals", () => {
    assert.strictEqual(formatInr(0.125, 2), "0.13 INR");
    assert.strictEqual(formatInr(1234.567, 0), "1,235 INR");
  });

  it("guards missing values", () => {
    assert.strictEqual(formatInr(null), "\u2014 INR");
    assert.strictEqual(formatInr(Number.NaN), "\u2014 INR");
  });
});

describe("formatKm", () => {
  it("defaults to one decimal", () => {
    assert.strictEqual(formatKm(0), "0.0 km");
    assert.strictEqual(formatKm(12.34), "12.3 km");
    assert.strictEqual(formatKm(1234.56), "1,234.6 km");
  });

  it("rounds up on decimal ties", () => {
    assert.strictEqual(formatKm(42.45, 1), "42.5 km");
  });

  it("guards missing values", () => {
    assert.strictEqual(formatKm(undefined), "\u2014 km");
  });
});

describe("formatPct", () => {
  it("uses toFixed semantics without grouping", () => {
    assert.strictEqual(formatPct(12.34), "12.3%");
    assert.strictEqual(formatPct(0), "0.0%");
    assert.strictEqual(formatPct(-5.25), "-5.3%");
  });

  it("locks the 99.95 rounding edge", () => {
    assert.strictEqual(formatPct(99.95), "100.0%");
  });

  it("supports custom decimals", () => {
    assert.strictEqual(formatPct(7.256, 2), "7.26%");
  });

  it("returns a bare em dash for missing values (no percent sign)", () => {
    assert.strictEqual(formatPct(null), "\u2014");
    assert.strictEqual(formatPct(undefined), "\u2014");
    assert.strictEqual(formatPct(Number.NaN), "\u2014");
  });
});

describe("formatQuantity", () => {
  it("formats quintals with one decimal by default", () => {
    assert.strictEqual(formatQuantity(100), "100.0 qtl");
    assert.strictEqual(formatQuantity(1234.56), "1,234.6 qtl");
  });

  it("honours explicit decimals", () => {
    assert.strictEqual(formatQuantity(98.76, 0), "99 qtl");
  });

  it("guards missing values", () => {
    assert.strictEqual(formatQuantity(null), "\u2014 qtl");
  });
});

describe("formatDateIso", () => {
  it("renders day, short month, year without leading zeros", () => {
    assert.strictEqual(formatDateIso("2025-10-30"), "30 Oct 2025");
    assert.strictEqual(formatDateIso("2025-01-05"), "5 Jan 2025");
    assert.strictEqual(formatDateIso("1999-12-31"), "31 Dec 1999");
    assert.strictEqual(formatDateIso("2024-02-29"), "29 Feb 2024");
  });

  it("passes through non-conforming input untouched", () => {
    assert.strictEqual(formatDateIso("not-a-date"), "not-a-date");
    assert.strictEqual(formatDateIso("30/10/2025"), "30/10/2025");
    assert.strictEqual(formatDateIso("2025-13-01"), "2025-13-01");
    assert.strictEqual(formatDateIso("2025-00-10"), "2025-00-10");
    assert.strictEqual(formatDateIso("2025-02-30"), "2025-02-30");
    assert.strictEqual(formatDateIso("2025-04-31"), "2025-04-31");
    assert.strictEqual(formatDateIso("2023-02-29"), "2023-02-29");
  });
});

describe("formatInterval", () => {
  it("joins grouped endpoints with an en dash and default unit", () => {
    assert.strictEqual(formatInterval(2200, 2400), "2,200\u20132,400 INR/qtl");
  });

  it("applies decimals to both endpoints", () => {
    assert.strictEqual(
      formatInterval(2200.5, 2400.75, "INR/qtl", 1),
      "2,200.5\u20132,400.8 INR/qtl"
    );
  });

  it("supports alternate units", () => {
    assert.strictEqual(formatInterval(1, 2.5, "INR", 2), "1.00\u20132.50 INR");
  });

  it("collapses to a bare em dash when either endpoint is missing", () => {
    assert.strictEqual(formatInterval(null, 2400), "\u2014");
    assert.strictEqual(formatInterval(2200, undefined), "\u2014");
    assert.strictEqual(formatInterval(Number.NaN, 2400), "\u2014");
    assert.strictEqual(formatInterval(2200, Number.NaN, "km", 1), "\u2014");
  });
});
