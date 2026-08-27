import { test, expect } from "@playwright/test";
import {
  watchPageProblems,
  expectNoPageProblems,
  waitForRouteReady,
  scanSeriousAxeViolations,
  expectNoSeriousAxeViolations,
  mockMapTiles,
} from "./helpers";

test.beforeEach(async ({ page }) => {
  await mockMapTiles(page);
});

const EXPECTED_QUERY = /lat=18\.5204&lon=73\.8567&q=100&r=4&rad=500$/;

async function rankOneMandi(page: import("@playwright/test").Page): Promise<string> {
  const card = page.locator("article").filter({ hasText: "Rank 1 of" });
  await expect(card).toBeVisible();
  return (await card.locator("h3").innerText()).trim();
}

test.describe("primary decision flow", () => {
  test("copies a trailing-slash recommendation URL", async ({ page }) => {
    await page.goto("/recommend/");
    await waitForRouteReady(page, "/recommend/");
    await page.getByRole("button", { name: "Copy link" }).click();
    const clipboard = await page.evaluate(() => navigator.clipboard.readText());
    expect(clipboard).toMatch(/\/recommend\/\?lat=.*&rad=.*$/);
  });

  test("restores non-default artifact transport config on browser back", async ({
    page,
  }) => {
    await page.route("**/data/meta.json", async (route) => {
      const response = await route.fetch();
      const meta = await response.json();
      meta.ranking.cost_per_km_per_quintal = 6;
      meta.ranking.max_transport_radius_km = 640;
      await route.fulfill({ response, json: meta });
    });
    await page.goto("/recommend/");
    await waitForRouteReady(page, "/recommend/");
    await expect(page.getByLabel("Transport rate (INR/km/quintal)")).toHaveValue("6");
    await expect(page.getByLabel("Maximum road radius (km)")).toHaveValue("640");

    await page.getByLabel("Example locations").selectOption({ label: "Pune" });
    await page.getByRole("button", { name: "Compare mandis" }).click();
    await expect(page).toHaveURL(/\/recommend\/\?lat=.*&r=6&rad=640$/);
    await page.goBack();
    await expect(page).toHaveURL(/\/recommend\/$/);
    await expect(page.getByLabel("Transport rate (INR/km/quintal)")).toHaveValue("6");
    await expect(page.getByLabel("Maximum road radius (km)")).toHaveValue("640");
  });

  test("preserves URL transport overrides and keeps them editable after loading", async ({
    page,
  }) => {
    await page.goto("/recommend/?r=7.5&rad=120");
    await waitForRouteReady(page, "/recommend/");

    const rate = page.getByLabel("Transport rate (INR/km/quintal)");
    const radius = page.getByLabel("Maximum road radius (km)");
    await expect(rate).toHaveValue("7.5");
    await expect(radius).toHaveValue("120");

    await rate.fill("8");
    await radius.fill("140");
    await expect(rate).toHaveValue("8");
    await expect(radius).toHaveValue("140");
  });

  test("changing the mandi location re-ranks results and produces a reproducible shareable link", async ({
    page,
  }) => {
    const problems = watchPageProblems(page);
    await page.goto("/recommend/");
    await waitForRouteReady(page, "/recommend/");

    const initialTop = await rankOneMandi(page);

    await page.getByLabel("Example locations").selectOption({ label: "Pune" });
    await expect(page.getByLabel("Latitude")).toHaveValue("18.5204");
    await expect(page.getByLabel("Longitude")).toHaveValue("73.8567");

    await page.getByRole("button", { name: "Compare mandis" }).click();
    await expect(page).toHaveURL(EXPECTED_QUERY);
    await waitForRouteReady(page, "/recommend/");

    const rerankedTop = await rankOneMandi(page);
    expect(rerankedTop).not.toBe(initialTop);
    expect(rerankedTop).toContain("Pune");

    await page.reload();
    await waitForRouteReady(page, "/recommend/");
    expect(await rankOneMandi(page)).toBe(rerankedTop);
    await expect(page.getByLabel("Latitude")).toHaveValue("18.5204");
    await expect(page.getByLabel("Longitude")).toHaveValue("73.8567");

    await page.getByRole("button", { name: "Copy link" }).click();
    await expect(page.getByText("Link copied")).toBeVisible();
    const clipboard = await page.evaluate(() => navigator.clipboard.readText());
    expect(clipboard).toBe(page.url());

    expectNoSeriousAxeViolations(await scanSeriousAxeViolations(page));
    expectNoPageProblems(problems);
  });

  test("invalid decision input is preserved with an inline error and blocks compare", async ({
    page,
  }) => {
    const problems = watchPageProblems(page);
    await page.goto("/recommend/");
    await waitForRouteReady(page, "/recommend/");

    const lat = page.getByLabel("Latitude");
    await lat.fill("999");
    await lat.blur();
    const alert = page.locator("#wb-lat-message");
    await expect(alert).toContainText(/between .+ and 90 degrees/);
    await expect(alert).toHaveAttribute("role", "alert");
    await expect(lat).toHaveValue("999");
    await expect(lat).toHaveAttribute("aria-invalid", "true");

    await lat.fill("19.99");
    await lat.blur();
    await expect(alert).toContainText(/Decimal degrees/);
    expect(await alert.getAttribute("role")).toBeNull();
    await expect(lat).toHaveValue("19.99");
    expectNoPageProblems(problems);
  });

  test("adds one browser-history entry after Compare mandis", async ({ page }) => {
    await page.goto("/recommend/");
    await waitForRouteReady(page, "/recommend/");

    await page.getByLabel("Example locations").selectOption({ label: "Pune" });
    await page.getByRole("button", { name: "Compare mandis" }).click();
    await expect(page).toHaveURL(EXPECTED_QUERY);

    await page.goBack();
    await expect(page).toHaveURL(/\/recommend\/$/);
    await expect(page.getByLabel("Latitude")).toHaveValue("19.9975");
  });

  test("keeps Leaflet zoom controls touch-safe on narrow screens", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto("/recommend/");
    await waitForRouteReady(page, "/recommend/");
    await expect(page.locator(".leaflet-container")).toBeVisible();
    await expect(page.locator(".leaflet-control-zoom a").first()).toBeVisible();

    const sizes = await page.locator(".leaflet-control-zoom a").evaluateAll((links) =>
      links.map((link) => {
        const rect = link.getBoundingClientRect();
        return { width: rect.width, height: rect.height };
      })
    );

    expect(sizes.length).toBe(2);
    for (const size of sizes) {
      expect(size.width).toBeGreaterThanOrEqual(44);
      expect(size.height).toBeGreaterThanOrEqual(44);
    }
  });
});
