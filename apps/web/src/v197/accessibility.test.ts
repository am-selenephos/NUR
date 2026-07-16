import { describe, expect, it } from "vitest";

import { ensureV197AccessibleViewport } from "../bridge/v197Accessibility";

describe("V197 accessibility bridge", () => {
  it("keeps responsive viewport sizing and restores browser zoom", () => {
    document.head.innerHTML = '<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">';

    const viewport = ensureV197AccessibleViewport(document);

    expect(viewport?.content).toBe("width=device-width, initial-scale=1.0");
    expect(viewport?.dataset.nurAccessibleViewport).toBe("true");
    expect(ensureV197AccessibleViewport(document)).toBe(viewport);
  });

  it("adds missing responsive defaults without duplicating directives", () => {
    document.head.innerHTML = '<meta name="viewport" content="viewport-fit=cover">';

    const viewport = ensureV197AccessibleViewport(document);

    expect(viewport?.content).toBe("width=device-width, viewport-fit=cover, initial-scale=1.0");
  });
});
