import { test, expect } from "@playwright/test";
import {
  expectNoHorizontalScroll,
  expectNoPageProblems,
  expectNoSeriousAxeViolations,
  scanSeriousAxeViolations,
  watchPageProblems,
} from "./helpers";

const VIEWPORTS = [
  { name: "se", width: 320, height: 568 },
  { name: "mobile", width: 375, height: 667 },
  { name: "plus", width: 414, height: 896 },
  { name: "tablet", width: 768, height: 1024 },
  { name: "desktop", width: 1024, height: 768 },
  { name: "wide", width: 1440, height: 900 },
];

const ROUTES = ["/", "/recommend/", "/forecast/", "/coverage/"];

for (const viewport of VIEWPORTS) {
  for (const route of ROUTES) {
    test(`${route} satisfies responsive contract at ${viewport.name} (${viewport.width}px)`, async ({ page }) => {
      const problems = watchPageProblems(page);
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.goto(route);
      await expect(page.locator("main")).toBeVisible();
      await expectNoHorizontalScroll(page);
      expectNoSeriousAxeViolations(await scanSeriousAxeViolations(page));
      expectNoPageProblems(problems);
    });
  }
}
