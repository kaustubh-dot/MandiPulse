import { test, expect } from "@playwright/test";
import {
  watchPageProblems,
  expectNoPageProblems,
  waitForRouteReady,
  scanSeriousAxeViolations,
  expectNoSeriousAxeViolations,
} from "./helpers";

const EXPECTED_QUERY = /lat=18\.5204&lon=73\.8567&q=100&r=4&rad=500$/;

async function rankOneMandi(page: import("@playwright/test").Page): Promise<string> {
  const card = page.locator("article").filter({ hasText: "Rank 1 of" });
  await expect(card).toBeVisible();
  return (await card.locator("h3").innerText()).trim();
}

test.describe("primary decision flow", () => {
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
});
