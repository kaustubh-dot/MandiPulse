import { afterEach, describe, it } from "node:test";
import assert from "node:assert/strict";
import "./dom.setup";
import { cleanup, screen } from "@testing-library/react";
import {
  EvidenceBlock,
  PageHeader,
  Panel,
  StatusNotice,
  TextField,
} from "../src/components/ui/primitives";
import { renderWithRouter } from "./router-stub";

afterEach(() => cleanup());

describe("Quiet Exchange primitives", () => {
  it("renders a restrained page header without forced uppercase", () => {
    renderWithRouter(
      <PageHeader
        eyebrow="Frozen snapshot"
        title="One recommendation"
        intro="Every assumption visible."
      />
    );
    assert.equal(screen.getByRole("heading", { level: 1 }).textContent, "One recommendation");
    assert.equal(screen.getByText("Frozen snapshot").className.includes("uppercase"), false);
  });

  it("uses open ruled containment instead of a generic rounded card", () => {
    const { container } = renderWithRouter(<Panel>Evidence</Panel>);
    const panel = container.querySelector("section")!;
    assert.equal(panel.className.includes("border-y"), true);
    assert.equal(panel.className.includes("shadow"), false);
  });

  it("reserves field message space and exposes valid and disabled states", () => {
    renderWithRouter(
      <TextField id="quantity" label="Quantity" value="100" onChange={() => {}} valid disabled />
    );
    const input = screen.getByLabelText("Quantity");
    assert.equal(input.hasAttribute("disabled"), true);
    assert.equal(input.getAttribute("data-state"), "success");
    assert.ok(document.querySelector("#quantity-message"));
  });

  it("keeps status and evidence regions semantically distinct", () => {
    renderWithRouter(
      <>
        <StatusNotice tone="warning" title="Stale">
          Three days behind.
        </StatusNotice>
        <EvidenceBlock
          title="Price evidence"
          rows={[{ label: "Net", value: "1,296 INR/qtl" }]}
        />
      </>
    );
    assert.ok(screen.getByRole("status"));
    assert.match(screen.getByText("Price evidence").parentElement!.className, /border-y/);
  });
});
