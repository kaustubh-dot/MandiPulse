import { afterEach, describe, it } from "node:test";
import assert from "node:assert/strict";
import "./dom.setup";
import { cleanup, render } from "@testing-library/react";
import { ContourField } from "../src/components/visual/ContourField";

afterEach(() => cleanup());

describe("ContourField", () => {
  it("is decorative, finite, token-driven, and non-focusable", () => {
    const { container } = render(<ContourField className="test-field" />);
    const svg = container.querySelector("svg")!;
    assert.equal(svg.getAttribute("aria-hidden"), "true");
    assert.equal(svg.getAttribute("focusable"), "false");
    assert.equal(svg.classList.contains("test-field"), true);
    assert.equal(svg.querySelectorAll("path").length, 5);
    assert.equal(svg.innerHTML.includes("#"), false);
  });
});
