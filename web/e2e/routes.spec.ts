import { test, expect } from "@playwright/test";
import {
  ROUTES,
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

test.describe("stable routes at both viewports", () => {
  for (const route of ROUTES) {
    test(`${route} hydrates with zero console errors and no unexpected critical/serious axe violations`, async ({
      page,
    }) => {
      const problems = watchPageProblems(page);
      await page.goto(route);
      await waitForRouteReady(page, route);
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
      expectNoPageProblems(problems);
      expectNoSeriousAxeViolations(await scanSeriousAxeViolations(page));
    });
  }
});

test.describe("shell navigation", () => {
  test("skip link targets the main content landmark", async ({ page }) => {
    const problems = watchPageProblems(page);
    await page.goto("/");
    const skip = page.getByRole("link", { name: /skip to main content/i }).first();
    await skip.focus();
    await expect(skip).toBeVisible();
    await expect(skip).toHaveAttribute("href", "#main-content");
    expectNoPageProblems(problems);
  });

  test("rail navigation reaches every route from the desktop shell", async ({
    page,
  }) => {
    test.skip(
      test.info().project.name !== "desktop",
      "the fixed rail is desktop-only; mobile uses the sheet (mobile-nav.spec.ts)"
    );
    const problems = watchPageProblems(page);
    await page.goto("/");
    const nav = page
      .locator('aside nav[aria-label="Primary"]')
      .getByRole("link", { name: "Overview" });
    await expect(nav.first()).toBeVisible();
    await expect(nav.first()).toHaveAttribute("aria-current", "page");
    for (const [label, route] of [
      ["Forecast", "/forecast/"],
      ["Coverage", "/coverage/"],
      ["Decision", "/recommend/"],
    ] as const) {
      await page
        .locator('aside nav[aria-label="Primary"]')
        .getByRole("link", { name: label })
        .click();
      await waitForRouteReady(page, route);
      await expect(page).toHaveURL(new RegExp(`${route.replace(/\//g, "\\/")}$`));
      const railLink = page
        .locator('aside nav[aria-label="Primary"]')
        .getByRole("link", { name: label });
      await expect(railLink).toHaveAttribute("aria-current", "page");
    }
    await page
      .locator('aside nav[aria-label="Primary"]')
      .getByRole("link", { name: "Overview" })
      .click();
    await waitForRouteReady(page, "/");
    expectNoPageProblems(problems);
  });
});
