import { test, expect } from "@playwright/test";
import { waitForRouteReady } from "./helpers";

test.describe("forecast mandi selection", () => {
  test("falls back to the canonical forecast when the URL mandi is invalid", async ({
    page,
  }) => {
    await page.goto("/forecast/?mandi=not-a-market");
    await waitForRouteReady(page, "/forecast/");
    await expect(page.locator("#forecast-mandi")).toHaveValue("581");
  });

  test("derives the selected mandi from the URL and follows browser back", async ({
    page,
  }) => {
    await page.goto("/forecast/?mandi=2484");
    await waitForRouteReady(page, "/forecast/");
    await expect(page.locator("#forecast-mandi")).toHaveValue("2484");

    await page.goto("/forecast/?mandi=575");
    await waitForRouteReady(page, "/forecast/");
    await expect(page.locator("#forecast-mandi")).toHaveValue("575");

    await page.goBack();
    await waitForRouteReady(page, "/forecast/");
    await expect(page).toHaveURL(/\/forecast\/\?mandi=2484$/);
    await expect(page.locator("#forecast-mandi")).toHaveValue("2484");
  });
});
