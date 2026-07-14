import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import {
  applyV197PerformanceProfile,
  buildV197PerformanceBootstrap,
} from "../bridge/v197PerformanceProfile";

const repositoryRoot = resolve(process.cwd(), "../..");
const source = (path: string) => readFileSync(resolve(repositoryRoot, path), "utf8");

describe("V197 deterministic runtime performance profile", () => {
  it("profiles the exact decoded Entry signatures without touching its source file", () => {
    const canonical = source("docs/reference/entry_decoded_v197.html");
    const result = applyV197PerformanceProfile(canonical, "entry");

    expect(result.applied).toBe(true);
    expect(result.replacementCount).toBe(6);
    expect(result.source).toContain("DPR=Math.min(devicePixelRatio||1,1.2)");
    expect(result.source).toContain("(mobile?120:150)");
    expect(result.source).toContain(".slice(0,18)");
    expect(canonical).toContain("(mobile?680:1140)");
  });

  it("profiles the exact decoded Universe signatures with a bounded particle cap", () => {
    const canonical = source("docs/reference/universe_decoded_v197.html");
    const result = applyV197PerformanceProfile(canonical, "universe");

    expect(result.applied).toBe(true);
    expect(result.replacementCount).toBe(7);
    expect(result.source).toContain("const PARTICLE_CAP=240");
    expect(result.source).toContain("DPR=Math.min(devicePixelRatio||1,.82)");
    expect(result.source).toContain("galaxy:90,far:45,dust:12,super:6");
    expect(result.source).toContain("const nodeBudget=innerWidth<700?12:18");
    expect(result.source).toContain('if(!isS&&p.kind==="galaxy")');
    expect(result.source).toContain('dataset.nurInteractionActive==="true"?72:25');
    expect(canonical).toContain("const PARTICLE_CAP=1880");
  });

  it("fails closed on signature drift and keeps an explicit canonical rollback", () => {
    const drifted = applyV197PerformanceProfile("<html>unknown</html>", "entry");
    const bootstrap = buildV197PerformanceBootstrap();

    expect(drifted.applied).toBe(false);
    expect(drifted.source).toBe("<html>unknown</html>");
    expect(bootstrap).toContain('requested === "canonical"');
    expect(bootstrap).toContain('nurRuntimeProfile = "canonical-fallback"');
  });
});
