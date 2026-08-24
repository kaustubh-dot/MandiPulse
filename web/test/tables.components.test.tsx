import { describe, it, afterEach } from "node:test";
import assert from "node:assert/strict";
import "./dom.setup";
import { cleanup, screen } from "@testing-library/react";
import TopRecommendations from "../src/components/TopRecommendations";
import RecommendTable from "../src/components/RecommendTable";
import HonestResultsTable from "../src/components/HonestResultsTable";
import { loadFixture } from "./dom.setup";
import { rankRecommendationCandidates } from "../src/lib/policy";
import { formatDateIso, formatInrPerQtl, formatKm } from "../src/lib/format";
import type {
  ForecastRow,
  MandiMeta,
  Meta,
  RankedMandi,
} from "../src/lib/types";
import { renderWithRouter } from "./router-stub";

afterEach(() => {
  cleanup();
});

const meta = loadFixture<Meta>("meta.json");
const mandis = loadFixture<MandiMeta[]>("mandis.json");
const forecasts = loadFixture<ForecastRow[]>("forecasts.json");

const ranked = rankRecommendationCandidates(
  forecasts,
  mandis,
  meta.default_farmer.latitude,
  meta.default_farmer.longitude,
  meta,
  meta.ranking.cost_per_km_per_quintal
).rows;

describe("TopRecommendations with real artifact ranking", () => {
  it("renders the rank-1 mandi card and both alternates from the fixture", () => {
    renderWithRouter(
      <TopRecommendations
        rows={ranked}
        forecastHorizonDays={meta.forecast_horizon_days}
        confidenceLevel={meta.confidence_level}
        quantityQtl={100}
      />
    );
    const top = ranked[0];
    assert.match(screen.getByText(`Rank 1 of ${ranked.length}`).textContent!, /Rank 1/);
    assert.equal(screen.getByRole("heading", { name: top.mandi }).textContent, top.mandi);
    const article = screen.getByRole("article");
    assert.match(article.textContent!, new RegExp(formatInrPerQtl(top.transport_adjusted_net_price_inr_qtl)));
    const lotNet = top.transport_adjusted_net_price_inr_qtl * 100;
    assert.match(article.textContent!, new RegExp(lotNet.toLocaleString("en-US", { maximumFractionDigits: 0 })));
    for (const alt of ranked.slice(1, 3)) {
      assert.ok(screen.getByText(alt.mandi), `missing alternate ${alt.mandi}`);
    }
    assert.equal(screen.getAllByText(/ risk/).length >= 3, true);
  });

  it("shows the staleness banner when the as-of date lags the snapshot window", () => {
    const staleRows: RankedMandi[] = [
      {
        ...ranked[0],
        staleness_days: 3,
      },
      ...ranked.slice(1),
    ];
    renderWithRouter(
      <TopRecommendations
        rows={staleRows}
        forecastHorizonDays={7}
        confidenceLevel={0.9}
        quantityQtl={100}
      />
    );
    assert.match(
      screen.getByText(/3 days behind/).textContent!,
      /forecast is 3 days behind/
    );
  });

  it("renders nothing when there are no ranked rows (empty state)", () => {
    const { container } = renderWithRouter(
      <TopRecommendations rows={[]} forecastHorizonDays={7} confidenceLevel={0.9} quantityQtl={100} />
    );
    assert.equal(container.childElementCount, 0);
  });

  it("renders one editorial primary result and a separate alternatives list", () => {
    renderWithRouter(
      <TopRecommendations
        rows={ranked}
        forecastHorizonDays={meta.forecast_horizon_days}
        confidenceLevel={meta.confidence_level}
        quantityQtl={100}
      />
    );
    const primary = screen.getByRole("article", { name: /rank 1 recommendation/i });
    assert.equal(primary.querySelectorAll("h3").length, 1);
    assert.ok(screen.getByRole("list", { name: "Alternative recommendations" }));
    assert.equal(primary.className.includes("border-l-4"), false);
  });
});

describe("RecommendTable with real artifact ranking", () => {
  it("renders one row per eligible candidate with a shaded rank-1 row", () => {
    renderWithRouter(
      <RecommendTable rows={ranked} canonicalAsOfDate={meta.candidate_policy.eligible_as_of_date} />
    );
    const region = screen.getByRole("region", { name: "All eligible mandis, ranked comparison" });
    const rows = region.querySelectorAll("tbody tr");
    assert.equal(rows.length, ranked.length);
    assert.match(region.querySelector("caption")!.textContent!, new RegExp(formatDateIso(meta.candidate_policy.eligible_as_of_date)));
    const firstRowCells = rows[0]!.querySelectorAll("td");
    assert.equal(firstRowCells[0]!.textContent, "1");
    assert.equal(firstRowCells[1]!.textContent, ranked[0].mandi);
    assert.equal(
      rows[0]!.className.includes("bg-paper-2"),
      true,
      "rank-1 row must be shaded"
    );
    assert.equal(rows[rows.length - 1]!.className.includes("bg-paper-2"), false);
    const netCell = firstRowCells[6]!;
    assert.equal(netCell.textContent, formatInrPerQtl(ranked[0].transport_adjusted_net_price_inr_qtl));
    const distanceCell = firstRowCells[7]!;
    assert.equal(distanceCell.textContent, formatKm(ranked[0].road_distance_km, 0));
  });

  it("keeps ranks contiguous after a radius cut re-ranks candidates", () => {
    const narrowed = rankRecommendationCandidates(
      forecasts,
      mandis,
      meta.default_farmer.latitude,
      meta.default_farmer.longitude,
      meta,
      meta.ranking.cost_per_km_per_quintal,
      100
    ).rows;
    renderWithRouter(
      <RecommendTable rows={narrowed} canonicalAsOfDate={meta.candidate_policy.eligible_as_of_date} />
    );
    const region = screen.getByRole("region", { name: "All eligible mandis, ranked comparison" });
    const ranks = Array.from(region.querySelectorAll("tbody tr td:first-child")).map(
      (cell) => Number(cell.textContent)
    );
    assert.deepEqual(ranks, narrowed.map((_, index) => index + 1));
    assert.ok(narrowed.every((row) => row.road_distance_km <= 100));
    assert.ok(narrowed.length > 0 && narrowed.length < ranked.length);
  });

  it("provides a mobile record list and a desktop comparison table", () => {
    renderWithRouter(
      <RecommendTable rows={ranked} canonicalAsOfDate={meta.candidate_policy.eligible_as_of_date} />
    );
    assert.ok(screen.getByRole("list", { name: "Eligible mandis as records" }));
    assert.ok(screen.getByRole("region", { name: "All eligible mandis, ranked comparison" }));
  });
});

describe("HonestResultsTable with real artifact", () => {
  it("renders model rows with MAE formatting and ship badges", () => {
    const results = loadFixture<Array<{ model: string; test_mae: number; ships: boolean }>>(
      "honest_results.json"
    );
    renderWithRouter(<HonestResultsTable results={results} />);
    const region = screen.getByRole("region", { name: "Held-out model comparison" });
    const rows = region.querySelectorAll("tbody tr");
    assert.equal(rows.length, results.length);
    const shipped = results.find((row) => row.ships)!;
    const shippedRow = Array.from(rows).find((row) =>
      row.textContent!.includes(shipped.model)
    )!;
    assert.match(
      shippedRow.textContent!,
      new RegExp(shipped.test_mae.toLocaleString("en-US", { minimumFractionDigits: 2 }))
    );
    assert.match(shippedRow.textContent!, /Ships/);
    const unshipped = results.find((row) => !row.ships)!;
    const unshippedRow = Array.from(rows).find((row) =>
      row.textContent!.includes(unshipped.model)
    )!;
    assert.match(unshippedRow.textContent!, /Not shipped/);
  });
});
