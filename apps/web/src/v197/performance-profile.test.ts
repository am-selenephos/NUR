import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import {
  V197_GALAXY_STAR_PAINT,
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
    expect(result.replacementCount).toBe(13);
    expect(result.source).toContain("DPR=Math.min(devicePixelRatio||1,1.15)");
    expect(result.source).toContain("(mobile?440:760)");
    expect(result.source).toContain(".slice(0,18)");
    expect(result.source).toContain("projectionCache=[]");
    expect(result.source).toContain("project(cached.p,yaw,pitch,roll,t,cached.q)");
    expect(result.source).toContain('if(!isS&&p.kind==="galaxy")');
    expect(result.source).toContain("const minFrameGap=innerWidth<700?48:38");
    expect(canonical).toContain("(mobile?680:1140)");
  });

  it("profiles the exact decoded Universe signatures with a bounded particle cap", () => {
    const canonical = source("docs/reference/universe_decoded_v197.html");
    const result = applyV197PerformanceProfile(canonical, "universe");

    expect(result.applied).toBe(true);
    expect(result.replacementCount).toBe(13);
    expect(result.source).toContain("const PARTICLE_CAP=1120");
    expect(result.source).toContain("DPR=Math.min(devicePixelRatio||1,1)");
    expect(result.source).toContain("galaxy:640,far:330,dust:82,super:30");
    expect(result.source).toContain("const nodeBudget=innerWidth<700?10:16");
    expect(result.source).toContain("projectionCache=[]");
    expect(result.source).toContain("project(cached.p,yaw,pitch,roll,t,cached.q)");
    expect(result.source).toContain("if(false)drawNebula(t);");
    expect(result.source).toContain('if(!isS&&p.kind==="galaxy")');
    expect(result.source).toContain("const minFrameGap=innerWidth<700?48:38");
    expect(result.source).toContain("function scheduleFrame(){if(reduced||frameRAF)return;frameRAF=requestAnimationFrame(frame)}");
    expect(result.source).not.toContain("__q");
    expect(result.source).not.toContain("setTimeout(()=>{frameRAF=requestAnimationFrame(frame)},delay)");
    expect(result.source).not.toContain('?72:25');
    expect(canonical).toContain("const PARTICLE_CAP=1880");
  });

  it("publishes the exact lightweight particle paint shared by sky and brain", () => {
    expect(V197_GALAXY_STAR_PAINT).toEqual({
      minimumRadius: .52,
      radiusScale: .82,
      maximumBodyAlpha: .92,
      bodyAlphaScale: 2.35,
      flareAlphaThreshold: .24,
      flareRadiusThreshold: .82,
      maximumFlareAlpha: .2,
      flareAlphaScale: .42,
      horizontalFlareScale: 2.2,
      verticalFlareScale: 1.5,
      flareThickness: .42,
    });
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
