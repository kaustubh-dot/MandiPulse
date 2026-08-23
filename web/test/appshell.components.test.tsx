import { describe, it, beforeEach, afterEach } from "node:test";
import assert from "node:assert/strict";
import "./dom.setup";
import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import AppShell from "../src/components/shell/AppShell";
import { renderWithRouter } from "./router-stub";

beforeEach(() => {
  document.documentElement.removeAttribute("data-theme");
  window.localStorage.clear();
});

afterEach(() => {
  cleanup();
});

const NAV_ROUTES = [
  { href: "/", label: "Overview" },
  { href: "/recommend", label: "Decision" },
  { href: "/forecast", label: "Forecast" },
  { href: "/coverage", label: "Coverage" },
];

describe("AppShell navigation", () => {
  it("renders links to every route", () => {
    renderWithRouter(<AppShell><p>body</p></AppShell>, { pathname: "/" });
    for (const item of NAV_ROUTES) {
      const link = screen.getByRole("link", { name: item.label });
      assert.equal(link.getAttribute("href"), item.href);
    }
    assert.equal(screen.getAllByRole("link", { name: "MandiPulse" }).length >= 1, true);
  });

  it("marks the active route with aria-current=page", () => {
    renderWithRouter(<AppShell><p>body</p></AppShell>, { pathname: "/recommend" });
    const active = screen.getByRole("link", { name: "Decision" });
    assert.equal(active.getAttribute("aria-current"), "page");
    const inactive = screen.getByRole("link", { name: "Forecast" });
    assert.equal(inactive.getAttribute("aria-current"), null);
  });

  it("exposes a primary navigation landmark and the main-content anchor", () => {
    renderWithRouter(<AppShell><p>body</p></AppShell>, { pathname: "/" });
    assert.ok(screen.getByRole("navigation", { name: "Primary" }));
    assert.equal(document.getElementById("main-content")?.tagName, "MAIN");
  });
});

describe("AppShell mobile sheet", () => {
  function renderShell() {
    return renderWithRouter(<AppShell><p>body</p></AppShell>, { pathname: "/" });
  }

  it("opens an accessible dialog with all nav links via the Menu button", async () => {
    const user = userEvent.setup();
    renderShell();
    const menu = screen.getByRole("button", { name: "Menu" });
    assert.equal(menu.getAttribute("aria-expanded"), "false");
    assert.equal(menu.getAttribute("aria-controls"), "mobile-nav-sheet");
    await user.click(menu);
    const dialog = screen.getByRole("dialog", { name: "Navigation" });
    assert.equal(dialog.getAttribute("aria-modal"), "true");
    for (const item of NAV_ROUTES) {
      assert.ok(
        screen.getAllByRole("link", { name: item.label }).length >= 1,
        `missing ${item.label}`
      );
    }
    assert.equal(menu.getAttribute("aria-expanded"), "true");
  });

  it("closes on Escape and returns focus to the Menu button", async () => {
    const user = userEvent.setup();
    renderShell();
    const menu = screen.getByRole("button", { name: "Menu" });
    await user.click(menu);
    await waitFor(() => assert.ok(screen.getByRole("dialog")));
    fireEvent.keyDown(document, { key: "Escape" });
    await waitFor(() => assert.equal(screen.queryByRole("dialog"), null));
    assert.equal(document.activeElement, menu);
  });

  it("closes when a nav link inside the sheet is clicked", async () => {
    const user = userEvent.setup();
    renderShell();
    await user.click(screen.getByRole("button", { name: "Menu" }));
    const dialogLinks = screen
      .getByRole("dialog", { name: "Navigation" })
      .querySelectorAll("a[href='/forecast']");
    assert.equal(dialogLinks.length > 0, true);
    await user.click(dialogLinks[0]!);
    await waitFor(() => assert.equal(screen.queryByRole("dialog"), null));
  });
});

describe("AppShell theme toggle", () => {
  it("toggles data-theme and aria-pressed, persisting to localStorage", async () => {
    const user = userEvent.setup();
    renderWithRouter(<AppShell><p>body</p></AppShell>, { pathname: "/" });
    const toggle = screen.getAllByRole("button", { name: /theme/i })[0]!;
    assert.equal(toggle.getAttribute("aria-pressed"), "false");
    await user.click(toggle);
    assert.equal(document.documentElement.getAttribute("data-theme"), "dark");
    assert.equal(toggle.getAttribute("aria-pressed"), "true");
    assert.equal(window.localStorage.getItem("mp-theme"), "dark");
    await user.click(toggle);
    assert.equal(document.documentElement.getAttribute("data-theme"), "light");
    assert.equal(window.localStorage.getItem("mp-theme"), "light");
  });
});
