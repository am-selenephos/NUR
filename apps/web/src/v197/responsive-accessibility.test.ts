import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const repositoryRoot = resolve(process.cwd(), "../..");
const read = (path: string) => readFileSync(resolve(repositoryRoot, path), "utf8");

describe("V197 responsive and accessibility contract", () => {
  it("keeps every required viewport in the reusable geometry matrix", () => {
    const helper = read("apps/web/e2e/helpers/v197Geometry.ts");
    for (const size of [
      "360, height: 800",
      "390, height: 844",
      "430, height: 932",
      "844, height: 390",
      "768, height: 1024",
      "1024, height: 768",
      "1280, height: 720",
      "1366, height: 768",
      "1440, height: 900",
      "1920, height: 1080",
      "2560, height: 1080",
      "2560, height: 1440",
    ]) expect(helper).toContain(size);
  });

  it("defines visible focus, touch, safe-area, RTL, and reduced-motion behavior", () => {
    const core = read("apps/web/src/styles/v197-cosmic-skin.css");
    const adjunct = read("apps/web/src/styles/v197-adjunct-forensic.css");

    expect(core).toContain('[role="button"]');
    expect(core).toContain("outline: 2px solid rgba(255, 211, 90, .88)");
    expect(core).toContain("min-height: 44px");
    expect(core).toContain("env(safe-area-inset-bottom)");
    expect(core).toContain('[dir="rtl"]');
    expect(core).toContain("animation-duration: .01ms");
    expect(adjunct).toContain("min-height: 44px");
    expect(adjunct).toContain("outline: 2px solid #ffd35a");
    expect(read("apps/web/src/bridge/v197Accessibility.ts")).toContain("user-scalable");
  });
});
