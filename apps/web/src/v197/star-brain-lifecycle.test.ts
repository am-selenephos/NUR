import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import { applyV197StarBrainLifecycleProfile } from "../bridge/v197StarBrainLifecycle";

const repositoryRoot = resolve(process.cwd(), "../..");
const runtime = readFileSync(
  resolve(repositoryRoot, "apps/web/src/bridge/v197StarBrainRuntime.js"),
  "utf8",
);

describe("V197 exact star-brain lifecycle profile", () => {
  it("adds bounded ownership without changing anatomy or stellar rendering", () => {
    const result = applyV197StarBrainLifecycleProfile(runtime);

    expect(result.applied).toBe(true);
    expect(result.replacementCount).toBe(10);
    expect(result.source).toContain("const N_CORTEX = MOBILE ? 430 : 640");
    expect(result.source).toContain("const N_DEEP   = MOBILE ? 140 : 220");
    expect(result.source).toContain("const N_CEREB  = MOBILE ? 96  : 140");
    expect(result.source).toContain("const N_STEM   = MOBILE ? 20  : 28");
    expect(result.source).toContain("const N_CAL    = MOBILE ? 22  : 32");
    expect(result.source).toContain("starGlow(q.x,q.y,sR,baseCol");
    expect(result.source).toContain("visibilityObserver.observe(host)");
    expect(result.source).toContain("resizeObserver?.disconnect()");
    expect(result.source).toContain("lifecycleAbort.abort()");
    expect(() => new Function(result.source)).not.toThrow();
  });

  it("suspends hidden work and never captures ordinary page scrolling", () => {
    const result = applyV197StarBrainLifecycleProfile(runtime);

    expect(result.source).toContain("const canRender=()=>!disposed && !document.hidden && renderVisible");
    expect(result.source).toContain("if(!e.ctrlKey && !e.metaKey) return");
    expect(result.source).not.toContain("setInterval(");
    expect(result.source).not.toContain("requestAnimationFrame(frame);\n    if(document.hidden) return");
    expect(result.source).not.toContain("if(!REDUCED && !document.getElementById('v197-sparkfield'))");
  });

  it("fails closed when a protected runtime signature drifts", () => {
    const result = applyV197StarBrainLifecycleProfile("(() => {})();");

    expect(result.applied).toBe(false);
    expect(result.source).toBe("(() => {})();");
    expect(result.failure).toBe("missing:0");
  });
});
