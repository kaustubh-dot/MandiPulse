import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const tokens = readFileSync(new URL("../src/styles/tokens.css", import.meta.url), "utf8");
const globals = readFileSync(new URL("../src/app/globals.css", import.meta.url), "utf8");
const layout = readFileSync(new URL("../src/app/layout.tsx", import.meta.url), "utf8");

describe("Quiet Exchange token contract", () => {
  it("declares the approved pure Quiet Exchange palette", () => {
    assert.match(tokens, /--mp-paper:\s*oklch\(96% 0\.012 75\)/);
    assert.match(tokens, /--mp-accent:\s*oklch\(38% 0\.13 18\)/);
    assert.doesNotMatch(tokens, /--mp-atlas(?:-soft)?:/);
    assert.match(tokens, /\[data-theme="dark"\]/);
    assert.match(tokens, /--mp-warning:\s*oklch\(76% 0\.11 70\)/);
    assert.match(tokens, /--mp-info:\s*oklch\(70% 0\.07 235\)/);
  });

  it("loads the approved three font roles", () => {
    assert.match(layout, /Cormorant_Garamond/);
    assert.match(layout, /Manrope/);
    assert.match(layout, /IBM_Plex_Mono/);
    assert.doesNotMatch(layout, /Barlow_Condensed|IBM_Plex_Sans/);
  });

  it("imports tokens and maps every public Tailwind role", () => {
    assert.match(globals, /@import "\.\.\/styles\/tokens\.css"/);
    for (const role of ["accent-soft", "focus"]) {
      assert.match(globals, new RegExp(`--color-${role}:\\s*var\\(--mp-${role}\\)`));
    }
    assert.doesNotMatch(globals, /--color-atlas(?:-soft)?:/);
  });
});
