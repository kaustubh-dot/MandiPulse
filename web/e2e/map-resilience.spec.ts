import { expect, test } from "@playwright/test";
import { waitForRouteReady } from "./helpers";

test("coverage keeps geographic evidence understandable when map tiles fail", async ({ page }) => {
  await page.route("https://*.tile.openstreetmap.org/**", (route) => route.abort("failed"));
  await page.goto("/coverage/");
  await waitForRouteReady(page, "/coverage/");

  await expect(page.getByRole("status", { name: "Map background unavailable" })).toBeVisible();
  await expect(page.getByText(/candidate locations remain plotted/i)).toBeVisible();
});
