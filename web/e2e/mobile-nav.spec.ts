import { test, expect } from "@playwright/test";
import {
  watchPageProblems,
  expectNoPageProblems,
  scanSeriousAxeViolations,
  expectNoSeriousAxeViolations,
  mockMapTiles,
} from "./helpers";

test.beforeEach(async ({ page }) => {
  await mockMapTiles(page);
});

const SHEET_LINKS = ["Overview", "Decision", "Forecast", "Coverage"] as const;

test.describe("mobile navigation sheet", () => {
  test("opens as an accessible dialog, passes axe, and closes on Escape", async ({
    page,
  }) => {
    test.skip(
      test.info().project.name !== "mobile",
      "the sheet only exists at mobile widths"
    );
    const problems = watchPageProblems(page);
    await page.goto("/recommend/");

    const menu = page.getByRole("button", { name: "Menu", exact: true });
    await expect(menu).toBeVisible();
    await expect(menu).toHaveAttribute("aria-expanded", "false");
    await expect(menu).toHaveAttribute("aria-controls", "mobile-nav-sheet");

    await menu.click();
    const sheet = page.getByRole("dialog", { name: "Navigation" });
    await expect(sheet).toBeVisible();
    await expect(sheet).toHaveAttribute("aria-modal", "true");
    await expect(menu).toHaveAttribute("aria-expanded", "true");
    await expect
      .poll(async () => page.evaluate(() => document.body.style.overflow))
      .toBe("hidden");
    for (const label of SHEET_LINKS) {
      await expect(sheet.getByRole("link", { name: label })).toBeVisible();
    }

    const violations = await scanSeriousAxeViolations(page);
    expectNoSeriousAxeViolations(violations);

    await page.keyboard.press("Escape");
    await expect(sheet).toBeHidden();
    await expect(menu).toHaveAttribute("aria-expanded", "false");
    await expect(menu).toBeFocused();
    await expect
      .poll(async () => page.evaluate(() => document.body.style.overflow))
      .toBe("");

    expectNoPageProblems(problems);
  });

  test("closing via a sheet link navigates and dismisses the dialog", async ({
    page,
  }) => {
    test.skip(
      test.info().project.name !== "mobile",
      "the sheet only exists at mobile widths"
    );
    const problems = watchPageProblems(page);
    await page.goto("/");
    await menuFlow(page, "Forecast");
    await expect(page.locator("#forecast-mandi")).toBeVisible();
    expectNoPageProblems(problems);
  });
});

async function menuFlow(page: import("@playwright/test").Page, label: string) {
  await page.getByRole("button", { name: "Menu", exact: true }).click();
  const sheet = page.getByRole("dialog", { name: "Navigation" });
  await expect(sheet).toBeVisible();
  await sheet.getByRole("link", { name: label }).click();
  await expect(sheet).toBeHidden();
}
