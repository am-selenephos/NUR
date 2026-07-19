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
      .toBe("ee34405b119b8f2d7b6a5b4b7fdedff2e6875f9bd7d472aff6ab5b8473b8d347");
    expect(runtime).toContain("canvas.id = 'nur-brain-canvas';");
    expect(runtime).toContain("const N_CORTEX = MOBILE ? 529 : 794;");
    expect(runtime).toContain("const N_CEREB  = MOBILE ? 110 : 161;");
    expect(runtime).toContain("const N_STEM   = MOBILE ? 69  : 105;");
    expect(runtime).toContain("host.dataset.nurSparkleProfile='exact-galaxy-rig-star';");
    expect(runtime).toContain("host.dataset.nurGalaxyPaint='v197-simple-galaxy-particle-v1';");
    expect(runtime).toContain("host.dataset.nurAnatomy='cortex-cerebellum-brainstem';");
    expect(runtime).toContain("const glint=REDUCED?0:Math.pow(.5+.5*Math.sin(p.gl),18);");
    expect(runtime).toContain("const simpleR=Math.max(.52,rad*.82);");
    expect(runtime).toContain("c.fillRect(x-simpleR*2.2,y-.21,simpleR*4.4,.42);");
    expect(runtime).toContain("c.fillRect(x-.21,y-simpleR*1.5,.42,simpleR*3);");
    expect(runtime).not.toContain("starSprites");
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
