import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const runtimePath = resolve(process.cwd(), "src/bridge/v43StarBrainRuntime.js");
const bridgePath = resolve(process.cwd(), "src/bridge/v197StarBrain.ts");
const runtime = readFileSync(runtimePath, "utf8");
const bridge = readFileSync(bridgePath, "utf8");

describe("V43-derived NUR star-brain source", () => {
  it("keeps the supplied V43 anatomy and adds the approved sparkle/stem extension", () => {
    expect(createHash("sha256").update(runtime).digest("hex"))
      .toBe("24a367425765e493600d3ea5e98510e433a973ecea24a8e884c98b14fc472903");
    expect(runtime).toContain("canvas.id = 'nur-brain-canvas';");
    expect(runtime).toContain("const N_CORTEX = MOBILE ? 430 : 640;");
    expect(runtime).toContain("const N_CEREB  = MOBILE ? 90  : 130;");
    expect(runtime).toContain("const N_STEM   = MOBILE ? 56  : 84;");
    expect(runtime).toContain("host.dataset.nurSparkleProfile='galaxy-starburst';");
    expect(runtime).toContain("host.dataset.nurAnatomy='cortex-cerebellum-brainstem';");
    expect(runtime).toContain("const glint=REDUCED?0:Math.pow(.5+.5*Math.sin(p.gl),18);");
    expect(runtime).toContain("window.nurStarBrain={ storm, absorb, shatter, firePulse };");
    expect(runtime).not.toContain("nur-brain-canvas-v197");
    expect(() => new Function(runtime)).not.toThrow();
  });

  it("mounts the extended renderer directly without a source-transform profile", () => {
    expect(bridge).toContain('import V43_STAR_BRAIN_RUNTIME from "./v43StarBrainRuntime.js?raw";');
    expect(bridge).toContain("script.textContent = V43_STAR_BRAIN_RUNTIME;");
    expect(bridge).toContain('brainHost.dataset.nurDispersal = "radial-circle";');
    expect(bridge).not.toContain("applyV197StarBrainVisualProfile");
    expect(bridge).not.toContain("applyV197StarBrainLifecycleProfile");
  });
});
