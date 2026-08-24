import { test, expect } from "@playwright/test";
import {
  expectNoPageProblems,
  expectNoSeriousAxeViolations,
  scanSeriousAxeViolations,
  watchPageProblems,
} from "./helpers";

test("overview exposes the selected quiet composition", async ({ page }) => {
  const problems = watchPageProblems(page);
  await page.goto("/");
  await expect(page.locator('[data-layout="quiet-overview"]')).toBeVisible();
  await expect(page.locator('svg[data-visual="contour-field"]')).toHaveCount(1);
  await expect(page.getByRole("article", { name: /rank 1 recommendation/i })).toBeVisible();
  expectNoSeriousAxeViolations(await scanSeriousAxeViolations(page));
  expectNoPageProblems(problems);
});

test("decision keeps controls before one dominant result", async ({ page }) => {
  const problems = watchPageProblems(page);
  await page.goto("/recommend/");
  const layout = page.locator('[data-layout="quiet-workbench"]');
  await expect(layout).toBeVisible();
  const controls = layout.getByRole("button", { name: "Compare mandis" });
  const result = layout.getByRole("article", { name: /rank 1 recommendation/i });
  await expect(controls).toBeVisible();
  await expect(result).toBeVisible();
  expect(
    await controls.evaluate(
      (node, res) => !!(node.compareDocumentPosition(res) & Node.DOCUMENT_POSITION_FOLLOWING),
      await result.elementHandle()
    )
  ).toBeTruthy();
  expectNoPageProblems(problems);
});

for (const [route, layout] of [
  ["/forecast/", "quiet-forecast"],
  ["/coverage/", "quiet-coverage"],
] as const) {
  test(`${layout} renders without generic metric-card rows`, async ({ page }) => {
    const problems = watchPageProblems(page);
    await page.goto(route);
    await expect(page.locator(`[data-layout="${layout}"]`)).toBeVisible();
    await expect(page.locator('svg[data-visual="contour-field"]')).toHaveCount(1);
    expectNoSeriousAxeViolations(await scanSeriousAxeViolations(page));
    expectNoPageProblems(problems);
  });
}

