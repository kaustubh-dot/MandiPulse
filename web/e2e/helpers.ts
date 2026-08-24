import { expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import type { Result } from "axe-core";

export const ROUTES = ["/", "/recommend/", "/forecast/", "/coverage/"] as const;

export type PageProblems = string[];

export function watchPageProblems(page: Page): PageProblems {
  const problems: PageProblems = [];
  page.on("console", (message) => {
    if (message.type() === "error") {
      problems.push(`console.error: ${message.text()}`);
    }
  });
  page.on("pageerror", (error) => {
    problems.push(`pageerror: ${error.message}`);
  });
  return problems;
}

export function expectNoPageProblems(problems: PageProblems): void {
  expect(problems, `expected no page problems, got:\n${problems.join("\n")}`).toEqual([]);
}

export async function waitForRouteReady(page: Page, route: string): Promise<void> {
  switch (route) {
    case "/":
      await expect(page.locator('[data-layout="quiet-overview"]')).toBeVisible();
      await expect(page.getByRole("article", { name: /rank 1 recommendation/i })).toBeVisible();
      break;
    case "/recommend/":
      await expect(page.locator('[data-layout="quiet-workbench"]')).toBeVisible();
      await expect(page.getByRole("article", { name: /rank 1 recommendation/i })).toBeVisible();
      break;
    case "/forecast/":
      await expect(page.locator("#forecast-mandi")).toBeVisible();
      break;
    case "/coverage/":
      await expect(
        page.getByRole("region", { name: "Per-mandi data coverage" })
      ).toBeVisible();
      break;
    default:
      throw new Error(`unknown route: ${route}`);
  }
}

export interface AxeScanOutcome {
  failures: Result[];
}

export async function scanSeriousAxeViolations(page: Page): Promise<AxeScanOutcome> {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  const failures: Result[] = [];
  for (const violation of results.violations) {
    if (violation.impact !== "critical" && violation.impact !== "serious") continue;
    failures.push(violation);
  }
  return { failures };
}

export function expectNoSeriousAxeViolations(outcome: AxeScanOutcome): void {
  expect(
    outcome.failures,
    `unexpected critical/serious axe violations:\n${JSON.stringify(outcome.failures, null, 2)}`
  ).toEqual([]);
}

export async function expectNoHorizontalScroll(page: Page): Promise<void> {
  const hasScroll = await page.evaluate(() => {
    return document.documentElement.scrollWidth > window.innerWidth;
  });
  expect(hasScroll, "expected page not to have horizontal overflow/scroll").toBe(false);
}
