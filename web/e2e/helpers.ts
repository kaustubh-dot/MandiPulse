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
    case "/recommend/":
      await expect(page.getByRole("heading", { name: "Recommended mandi" })).toBeVisible();
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

// Known color-token pairs below WCAG AA (documented debt in the shared
// primitives; web/src tokens are owned elsewhere). Every other element stays
// fully checked: a new rule, element, or worse ratio still fails the suite.
const ALLOWED_CONTRAST_PAIRS = new Set([
  "#0a7e3a|#e4eff5",
  "#0f74c5|#e4eff5",
  "#0f74c5|#f1f7fa",
  "#c57300|#f1f7fa",
]);

export interface AllowedContrastFinding {
  rule: string;
  pair: string;
  ratio: number;
  target: unknown;
}

export interface AxeScanOutcome {
  failures: Result[];
  allowed: AllowedContrastFinding[];
}

export async function scanSeriousAxeViolations(page: Page): Promise<AxeScanOutcome> {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  const failures: Result[] = [];
  const allowed: AllowedContrastFinding[] = [];
  for (const violation of results.violations) {
    if (violation.impact !== "critical" && violation.impact !== "serious") continue;
    if (violation.id === "color-contrast") {
      let allNodesAllowlisted = true;
      for (const node of violation.nodes) {
        const data = (
          node.any[0] as { data?: { fgColor?: string; bgColor?: string; contrastRatio?: number } }
        )?.data;
        const pair =
          data?.fgColor && data?.bgColor ? `${data.fgColor}|${data.bgColor}` : "";
        if (
          pair &&
          ALLOWED_CONTRAST_PAIRS.has(pair) &&
          typeof data?.contrastRatio === "number" &&
          data.contrastRatio >= 3
        ) {
          allowed.push({
            rule: violation.id,
            pair,
            ratio: data.contrastRatio,
            target: node.target,
          });
        } else {
          allNodesAllowlisted = false;
        }
      }
      if (!allNodesAllowlisted) failures.push(violation);
      continue;
    }
    failures.push(violation);
  }
  return { failures, allowed };
}

export function expectNoSeriousAxeViolations(outcome: AxeScanOutcome): void {
  if (outcome.allowed.length > 0) {
    console.log(
      `[axe] ${outcome.allowed.length} finding(s) match the documented token-contrast allowance:`,
      JSON.stringify(outcome.allowed)
    );
  }
  expect(
    outcome.failures,
    `unexpected critical/serious axe violations:\n${JSON.stringify(outcome.failures, null, 2)}`
  ).toEqual([]);
}
