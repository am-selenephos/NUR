import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const repositoryRoot = resolve(process.cwd(), "../..");
const source = (path: string) => readFileSync(resolve(repositoryRoot, path), "utf8");
const hash = (path: string) => createHash("sha256").update(readFileSync(resolve(repositoryRoot, path))).digest("hex");

describe("Phase 1 immutable V197 host", () => {
  it("keeps the canonical host and decoded documents byte-checked", () => {
    expect(hash("apps/web/public/v197/NUR_V197_CHECKBOX_TICK_RESTORED.html"))
      .toBe("252eee806ece31ef829a2dc5cd45aa8d8f8e855db1bde98b6f87193d786633c3");
    expect(hash("docs/reference/entry_decoded_v197.html"))
      .toBe("49e2e72fb3adea405428789d9235dfc5ecb122f8dc1e17205d4fa05de64ecd97");
    expect(hash("docs/reference/universe_decoded_v197.html"))
      .toBe("b80eb5198d6fd9088e999020bd1cf85e95af9a20fd4ab172cfb7d5726dbd5a3c");
  });

  it("uses a zero-visual shell rather than a React presentation root", () => {
    const host = source("apps/web/public/v197/NUR_V197_CHECKBOX_TICK_RESTORED.html");
    const entry = source("apps/web/src/main.ts");
    const viteConfig = source("apps/web/vite.config.ts");

    expect(host).toContain('id="nur-entry-stage"');
    expect(host).toContain('id="nur-universe-stage"');
    expect(host).not.toContain('id="root"');
    expect(host).not.toContain("global.css");
    expect(entry).toContain("bootstrapV197Bridge");
    expect(entry).not.toContain("ReactDOM");
    expect(entry).not.toContain("react-dom");
    expect(viteConfig).toContain("nur-v197-direct-host");
    expect(viteConfig).toContain('src="/assets/v197-bridge.js"');
  });

  it("keeps Phase 1 mutations text-only", () => {
    const mutations = source("apps/web/src/bridge/v197Mutations.ts");
    expect(mutations).not.toMatch(/appendChild|insertAdjacentHTML|innerHTML|classList|\.style\b/);
  });
});
