import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const read = (path: string) => readFileSync(resolve(process.cwd(), path), "utf8");

describe("V197 adjunct forensic style", () => {
  it("keeps the route renderer structural and moves appearance to a dedicated module", () => {
    const source = read("src/bridge/v197Adjuncts.ts");
    expect(source).toContain('import V197_ADJUNCT_FORENSIC_CSS from "../styles/v197-adjunct-forensic.css?raw"');
    expect(source).toContain("style.textContent = V197_ADJUNCT_FORENSIC_CSS");
    expect(source).not.toContain("2147483000");
    expect(source).not.toContain("background-size: 173px 191px");
    expect(source).not.toContain("rgba(201,105,42,.64)");
  });

  it("uses bounded black glass, exact palette accents, and no fake star wallpaper", () => {
    const css = read("src/styles/v197-adjunct-forensic.css");
    expect(css).toContain("z-index: var(--nur-layer-modal, 70)");
    expect(css).toContain("#000");
    expect(css).toContain("#ffd35a");
    expect(css).toContain("#ff3a9e");
    expect(css).toContain("#21e8ff");
    expect(css).toContain("#843dff");
    expect(css).not.toContain("2147483000");
    expect(css).not.toContain("background-size: 173px");
    expect(css).not.toContain("rgba(30,16,30,.72)");
  });
});
