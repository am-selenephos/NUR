import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const read = (path: string) => readFileSync(resolve(process.cwd(), path), "utf8");

describe("Gate 5 Context Capsule visual law", () => {
  it("uses the dedicated capture button class instead of generic soft buttons", () => {
    const shareSheet = read("src/routes/universe/shell/ShareOrbitSheet.tsx");
    const captureButtons = shareSheet.match(/className="share-capture-btn"/g) ?? [];

    expect(captureButtons).toHaveLength(2);
    expect(shareSheet).not.toMatch(/<button\s+className="soft-btn"[^>]*>\s*keep (decision|reference)\s*<\/button>/);
  });

  it("locks the capture buttons to V197-native scoped CSS", () => {
    const scopedCss = read("src/styles/v197-universe-scoped.css");

    expect(scopedCss).toContain("body.universe-edition .scope-modal .share-capture-btn");
    expect(scopedCss).toContain("body.universe-edition .scope-modal .task-add-row > button");
    expect(scopedCss).toContain("body.universe-edition .scope-modal .task-add-row .soft-btn");
    expect(scopedCss).toContain("linear-gradient(135deg,rgba(58,29,10,.72)");
    expect(scopedCss).toContain("font:italic 500 15px/1 \"Crimson Pro\",serif");
    expect(scopedCss).toContain("@media (max-width:620px)");
  });

  it("does not restore native checkbox appearance for share-source checks", () => {
    const shareSheet = read("src/routes/universe/shell/ShareOrbitSheet.tsx");
    const globalCss = read("src/styles/global.css");
    const scopedCss = read("src/styles/v197-universe-scoped.css");
    const shareSourceCss = [globalCss, scopedCss]
      .flatMap(css => css.match(/share-source-check[^}]+}/g) ?? [])
      .join("\n");

    expect(shareSheet).not.toMatch(/appearance\s*:\s*["']auto["']/);
    expect(shareSheet).not.toMatch(/style=\{\{[^}]*flex:\s*["']none["']/);
    expect(shareSourceCss).not.toMatch(/appearance\s*:\s*auto/);
    expect(shareSourceCss).toMatch(/appearance\s*:\s*none/);
  });

  it("keeps modal opacity and viewport spacing in scoped CSS", () => {
    const shareSheet = read("src/routes/universe/shell/ShareOrbitSheet.tsx");
    const scopedCss = read("src/styles/v197-universe-scoped.css");

    expect(shareSheet).toContain('className="scope-modal share-orbit-modal"');
    expect(shareSheet).not.toMatch(/maxHeight:\s*["']86vh["']/);
    expect(scopedCss).toContain("body.universe-edition .modal-backdrop.open[aria-hidden=\"false\"]");
    expect(scopedCss).toContain("padding-top:clamp(24px,5vh,54px)");
    expect(scopedCss).toContain("max-height:calc(100dvh - 72px)");
  });

  it("uses the shared NUR wordmark and removes fake Systems metrics", () => {
    const systems = read("src/routes/universe/Systems.tsx");

    expect(systems).toContain("NURWordmark");
    expect(systems).toContain('variant="map"');
    expect(systems).not.toContain("<b className=\"nur-holo-word\">NUR</b>");
    for (const fake of ["<b>07</b>", "<b>19</b>", "<b>04</b>", "1,284", "89</b>", "78%", "LIVE</span>"]) {
      expect(systems).not.toContain(fake);
    }
  });

  it("restores the V197 Today master-star hero in the React runtime bridge", () => {
    const today = read("src/routes/universe/Today.tsx");
    const globalCss = read("src/styles/global.css");
    const scopedCss = read("src/styles/v197-universe-scoped.css");

    expect(today).toContain('className="orbit-star-zone"');
    expect(today).toContain('data-testid="today-orbit"');
    expect(today).toContain('<MasterStar variant="hero" />');
    expect(scopedCss).toContain("#page-today .orbit-star-zone{display:none!important}");
    expect(globalCss).toContain("restore the V197 Today orbit hero");
    expect(globalCss).toContain("body.universe-edition #page-today .orbit-star-zone,");
    expect(globalCss).toContain("display:grid!important");
    expect(globalCss).toContain("body.universe-edition #page-today .orbit-star-zone .f4-core");
    expect(globalCss).toContain("body.universe-edition #page-today .orbit-star-zone .f4-master-star");
  });

  it("does not let the universe global composer cover V197 personal pages", () => {
    const contract = read("src/v197/contract.ts");
    const layout = read("src/routes/universe/UniverseLayout.tsx");
    const routeBlock = contract.slice(
      contract.indexOf("export const V197_GLOBAL_COMPOSER_ROUTES"),
      contract.indexOf("export const V197_TALK_THREAD_ACTIONS"),
    );

    expect(routeBlock).toContain("V197_GLOBAL_COMPOSER_ROUTES");
    expect(routeBlock).not.toContain("\"/systems\"");
    expect(routeBlock).not.toContain("\"/universe\",");
    expect(routeBlock).not.toContain("\"/universe/map\"");
    expect(routeBlock).not.toContain("\"/universe/timeline\"");
    expect(routeBlock).not.toContain("\"/today\"");
    expect(routeBlock).not.toContain("\"/talk\"");
    expect(routeBlock).not.toContain("\"/journal\"");
    expect(routeBlock).not.toContain("\"/plan\"");
    expect(layout).toContain("showGlobalComposer ? <GlobalComposer /> : null");
    expect(layout).toContain('document.querySelector<HTMLElement>(".nur-viewport")?.scrollTo(0, 0)');
  });

  it("keeps capsule e2e honest: no forced clicks", () => {
    const capsuleSpec = read("e2e/capsule.spec.ts");

    expect(capsuleSpec).not.toMatch(/force\s*:\s*true/);
  });

  it("keeps RTL from mirroring the NUR star/wordmark/canvas objects", () => {
    const globalCss = read("src/styles/global.css");

    expect(globalCss).toContain('html[dir="rtl"] body.universe-edition :is(.nur-holo-word,.universe-map-title,.f4-core,#space3d,.master-star,.universe-master-star)');
    expect(globalCss).toContain("unicode-bidi:isolate");
  });
});
