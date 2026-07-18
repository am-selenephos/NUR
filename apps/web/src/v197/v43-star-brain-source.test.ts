import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const runtimePath = resolve(process.cwd(), "src/bridge/v43StarBrainRuntime.js");
const bridgePath = resolve(process.cwd(), "src/bridge/v197StarBrain.ts");
const runtime = readFileSync(runtimePath, "utf8");
const bridge = readFileSync(bridgePath, "utf8");

describe("exact V43 star-brain source", () => {
  it("is a byte-identical copy of the supplied V43 V7 renderer", () => {
    expect(createHash("sha256").update(runtime).digest("hex"))
      .toBe("d83705cc9cca27c42dd89fdea1f1b9fc057200351f67eda995d0ee2e4683c4e6");
    expect(runtime).toContain("canvas.id = 'nur-brain-canvas';");
    expect(runtime).toContain("const N_CORTEX = MOBILE ? 430 : 640;");
    expect(runtime).toContain("const N_CEREB  = MOBILE ? 90  : 130;");
    expect(runtime).toContain("const N_STEM   = MOBILE ? 18  : 26;");
    expect(runtime).toContain("window.nurStarBrain={ storm, absorb, shatter, firePulse };");
    expect(runtime).not.toContain("nur-brain-canvas-v197");
    expect(() => new Function(runtime)).not.toThrow();
  });

  it("mounts the V43 source directly without a source-transform profile", () => {
    expect(bridge).toContain('import V43_STAR_BRAIN_RUNTIME from "./v43StarBrainRuntime.js?raw";');
    expect(bridge).toContain("script.textContent = V43_STAR_BRAIN_RUNTIME;");
    expect(bridge).toContain('brainHost.dataset.nurDispersal = "radial-circle";');
    expect(bridge).not.toContain("applyV197StarBrainVisualProfile");
    expect(bridge).not.toContain("applyV197StarBrainLifecycleProfile");
  });
});
