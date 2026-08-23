import { describe, it, afterEach } from "node:test";
import assert from "node:assert/strict";
import "./dom.setup";
import { cleanup, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ErrorState, EmptyState, LoadingState } from "../src/components/DataState";
import HomePage from "../src/app/page";
import { installFetchRoutes, loadFixture } from "./dom.setup";
import type {
  BacktestSummary,
  ForecastRow,
  HonestResult,
  MandiMeta,
  Meta,
} from "../src/lib/types";
import { renderWithRouter } from "./router-stub";

afterEach(() => {
  cleanup();
});

describe("LoadingState", () => {
  it("announces loading via a polite status region with aria-busy", () => {
    renderWithRouter(<LoadingState label="Loading the overview snapshot…" />);
    const status = screen.getByRole("status");
    assert.equal(status.getAttribute("aria-live"), "polite");
    assert.equal(status.getAttribute("aria-busy"), "true");
    assert.match(status.textContent!, /Loading the overview snapshot/);
  });
});

describe("ErrorState", () => {
  it("renders the failure message and a Try again affordance that retries", async () => {
    const user = userEvent.setup();
    let retries = 0;
    renderWithRouter(
      <ErrorState
        message="Failed to fetch /data/meta.json: 404"
        onRetry={() => {
          retries += 1;
        }}
      />
    );
    const alert = screen.getByRole("alert");
    assert.match(alert.textContent!, /Data could not be loaded/);
    assert.match(alert.textContent!, /\/data\/meta\.json: 404/);
    await user.click(screen.getByRole("button", { name: "Try again" }));
    assert.equal(retries, 1);
  });

  it("omits the retry button when no retry is possible", () => {
    renderWithRouter(<ErrorState message="Snapshot unavailable" />);
    assert.equal(screen.queryByRole("button", { name: "Try again" }), null);
    assert.match(screen.getByRole("alert").textContent!, /Snapshot unavailable/);
  });
});

describe("EmptyState", () => {
  it("reports absence with title, detail, and next action", () => {
    renderWithRouter(
      <EmptyState
        title="No coverage data is available in this snapshot"
        detail="The bundle loaded, but it contains no finite historical price observations."
        nextAction={<a href="#method">Read the method summary</a>}
      />
    );
    const status = screen.getByRole("status");
    assert.match(status.textContent!, /Nothing to show/);
    assert.match(status.textContent!, /No coverage data is available/);
    assert.match(status.textContent!, /no finite historical price observations/);
    const link = screen.getByRole("link", { name: "Read the method summary" });
    assert.equal(link.getAttribute("href"), "#method");
  });
});

const FIXTURE_ROUTES: Record<string, { body: unknown }> = {
  "/data/meta.json": { body: loadFixture<Meta>("meta.json") },
  "/data/mandis.json": { body: loadFixture<MandiMeta[]>("mandis.json") },
  "/data/forecasts.json": { body: loadFixture<ForecastRow[]>("forecasts.json") },
  "/data/backtest.json": { body: loadFixture<BacktestSummary>("backtest.json") },
  "/data/honest_results.json": {
    body: loadFixture<HonestResult[]>("honest_results.json"),
  },
};

describe("Home page data-state integration over mocked fetch", () => {
  it("renders the loading skeleton first, then the loaded decision preview", async () => {
    const calls = installFetchRoutes(FIXTURE_ROUTES);
    renderWithRouter(<HomePage />);
    await waitFor(() =>
      assert.match(
        screen.getByRole("status").textContent!,
        /Loading the overview snapshot/
      )
    );
    await waitFor(() =>
      assert.ok(screen.getByRole("heading", { name: "Recommended mandi" }))
    );
    assert.match(document.body.textContent!, /Pimpalgaon/);
    assert.match(document.body.textContent!, /Eligible forecasts: 10/);
    assert.match(document.body.textContent!, /stale excluded: 5/);
    assert.ok(calls.includes("/data/meta.json"));
    assert.ok(calls.includes("/data/honest_results.json"));
  });

  it("shows the missing-artifact error state when an artifact 404s and recovers on retry", async () => {
    const user = userEvent.setup();
    let metaFails = true;
    installFetchRoutes(FIXTURE_ROUTES);
    const servingFetch = globalThis.fetch;
    let metaCalls = 0;
    globalThis.fetch = (async (input: RequestInfo | URL) => {
      const path = String(input).replace(/^https?:\/\/[^/]+/, "");
      if (path === "/data/meta.json") {
        metaCalls += 1;
        if (metaFails) {
          return { ok: false, status: 404, text: async () => "Not Found" } as Response;
        }
      }
      return servingFetch(input);
    }) as typeof fetch;

    renderWithRouter(<HomePage />);
    await waitFor(() =>
      assert.match(screen.getByRole("alert").textContent!, /Data could not be loaded/)
    );
    assert.match(screen.getByRole("alert").textContent!, /meta\.json: 404/);
    assert.ok(screen.getByText(/Expected artifacts are read from/));
    metaFails = false;
    await user.click(screen.getByRole("button", { name: "Try again" }));
    await waitFor(() =>
      assert.ok(screen.getByRole("heading", { name: "Recommended mandi" }))
    );
    assert.ok(metaCalls >= 2);
    globalThis.fetch = servingFetch;
  });

  it("surfaces an empty-source warning instead of rankings when artifacts are hollow", async () => {
    installFetchRoutes({
      ...FIXTURE_ROUTES,
      "/data/mandis.json": { body: [] },
      "/data/honest_results.json": { body: [] },
    });
    renderWithRouter(<HomePage />);
    await waitFor(() =>
      assert.ok(screen.getByText("No source rows"))
    );
    assert.match(
      document.body.textContent!,
      /no mandi or forecast rows/
    );
    assert.equal(screen.queryByRole("heading", { name: "Recommended mandi" }), null);
  });
});
