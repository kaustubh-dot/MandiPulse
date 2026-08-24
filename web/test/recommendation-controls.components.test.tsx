import { describe, it, afterEach } from "node:test";
import assert from "node:assert/strict";
import { useState } from "react";
import "./dom.setup";
import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import RecommendationControls, {
  DECISION_DEFAULTS,
  FARMER_PRESETS,
  validateDecisionInput,
  type DecisionDrafts,
} from "../src/components/RecommendationControls";
import { loadFixture } from "./dom.setup";
import type { Meta } from "../src/lib/types";
import { renderWithRouter } from "./router-stub";

afterEach(() => {
  cleanup();
});

const meta = loadFixture<Meta>("meta.json");

function drafts(overrides: Partial<DecisionDrafts> = {}): DecisionDrafts {
  return { ...DECISION_DEFAULTS, ...overrides };
}

interface HarnessProps {
  drafts: DecisionDrafts;
  errors?: Partial<DecisionDrafts>;
  copyState?: "idle" | "copied" | "failed";
}

function Harness({ drafts: value, errors = {}, copyState = "idle" }: HarnessProps) {
  return (
    <RecommendationControls
      meta={meta}
      drafts={value}
      errors={errors}
      copyState={copyState}
      horizonDays={meta.forecast_horizon_days}
      onChange={() => {}}
      onBlurField={() => {}}
      onCompare={() => {}}
      onCopyLink={() => {}}
    />
  );
}

function LiveValidationHarness() {
  const [value, setValue] = useState<DecisionDrafts>(drafts());
  const [errors, setErrors] = useState<Partial<Record<keyof DecisionDrafts, string>>>({});
  return (
    <RecommendationControls
      meta={meta}
      drafts={value}
      errors={errors}
      copyState="idle"
      horizonDays={7}
      onChange={(field, next) =>
        setValue((current) => ({ ...current, [field]: next }))
      }
      onBlurField={(field) => {
        const message = validateDecisionInput(field, value[field]);
        setErrors((current) => ({ ...current, [field]: message }));
      }}
      onCompare={() => {}}
      onCopyLink={() => {}}
    />
  );
}

describe("validateDecisionInput", () => {
  it("rejects empty and non-numeric input", () => {
    assert.match(validateDecisionInput("lat", "") ?? "", /Enter a number/);
    assert.match(validateDecisionInput("lat", "   ") ?? "", /Enter a number/);
    assert.match(validateDecisionInput("lat", "abc") ?? "", /Enter a number/);
  });

  it("enforces coordinate ranges", () => {
    assert.match(validateDecisionInput("lat", "-90.1") ?? "", /between .+ and 90/);
    assert.equal(validateDecisionInput("lat", "-90"), undefined);
    assert.equal(validateDecisionInput("lat", "90"), undefined);
    assert.match(validateDecisionInput("lon", "181") ?? "", /between .+ and 180/);
    assert.equal(validateDecisionInput("lon", "180"), undefined);
  });

  it("enforces positive quantity/radius and non-negative rate", () => {
    assert.match(validateDecisionInput("quantity", "0") ?? "", /greater than 0 quintals/);
    assert.match(validateDecisionInput("radius", "-5") ?? "", /greater than 0 km/);
    assert.match(validateDecisionInput("rate", "-1") ?? "", /cannot be negative/);
    assert.equal(validateDecisionInput("rate", "0"), undefined);
  });
});

describe("RecommendationControls rendering and interaction", () => {
  it("renders all five decision fields with artifact-driven transport facts", () => {
    renderWithRouter(<Harness drafts={drafts()} />);
    for (const label of [
      "Latitude",
      "Longitude",
      "Quantity (quintals)",
      "Transport rate (INR/km/quintal)",
      "Maximum road radius (km)",
    ]) {
      assert.ok(screen.getByLabelText(label), `missing field ${label}`);
    }
    const assumptions = screen.getByText("Transport assumptions").parentElement!;
    assert.match(
      assumptions.textContent!,
      new RegExp(String(meta.ranking.road_distance_factor))
    );
    assert.match(
      assumptions.textContent!,
      new RegExp(`Up to ${meta.ranking.max_alternatives}`)
    );
  });

  it("preserves the entered value when input is invalid and shows the stable message slot", async () => {
    const user = userEvent.setup();
    renderWithRouter(<LiveValidationHarness />);
    const lat = screen.getByLabelText("Latitude") as HTMLInputElement;
    await user.clear(lat);
    await user.type(lat, "123.9");
    fireEvent.blur(lat);
    await waitFor(() => {
      const slot = document.getElementById("wb-lat-message-slot");
      assert.ok(slot);
      assert.match(slot!.textContent!, /between .+ and 90 degrees/);
    });
    assert.equal(lat.value, "123.9");
    assert.equal(lat.getAttribute("aria-invalid"), "true");
  });

  it("restores helper text without removing the message slot", async () => {
    const user = userEvent.setup();
    renderWithRouter(<LiveValidationHarness />);
    const lat = screen.getByLabelText("Latitude") as HTMLInputElement;
    await user.clear(lat);
    await user.type(lat, "9999");
    fireEvent.blur(lat);
    await waitFor(() => assert.ok(document.getElementById("wb-lat-message-slot")));
    const slot = document.getElementById("wb-lat-message-slot")!;
    await user.clear(lat);
    await user.type(lat, "19.99");
    fireEvent.blur(lat);
    await waitFor(() => assert.equal(document.getElementById("wb-lat-message-slot"), slot));
    assert.match(slot.textContent ?? "", /Decimal degrees/);
    assert.equal(lat.value, "19.99");
  });

  it("applies a farmer preset to both coordinate fields via onChange", async () => {
    const user = userEvent.setup();
    const changed: Array<[string, string]> = [];
    function PresetHarness() {
      const [value, setValue] = useState(drafts());
      return (
        <RecommendationControls
          meta={meta}
          drafts={value}
          errors={{}}
          copyState="idle"
          horizonDays={7}
          onChange={(field, next) => {
            changed.push([field, next]);
            setValue((current) => ({ ...current, [field]: next }));
          }}
          onBlurField={() => {}}
          onCompare={() => {}}
          onCopyLink={() => {}}
        />
      );
    }
    renderWithRouter(<PresetHarness />);
    const pune = FARMER_PRESETS[1];
    await user.selectOptions(screen.getByLabelText("Example locations"), "1");
    assert.deepEqual(changed, [
      ["lat", String(pune.lat)],
      ["lon", String(pune.lon)],
    ]);
    assert.equal(
      (screen.getByLabelText("Latitude") as HTMLInputElement).value,
      String(pune.lat)
    );
  });

  it("announces copy success and failure states in the live region", () => {
    const { rerender } = renderWithRouter(
      <Harness drafts={drafts()} copyState="copied" />
    );
    const live = screen.getByText("Link copied");
    assert.equal(live.className.includes("text-success"), true);
    rerender(<Harness drafts={drafts()} copyState="failed" />);
    assert.match(screen.getByText(/Copying failed/).textContent!, /Copy the address/);
  });
});
