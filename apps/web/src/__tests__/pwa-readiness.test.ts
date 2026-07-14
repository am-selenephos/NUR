import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const pub = (path: string) => readFileSync(resolve(process.cwd(), "public", path), "utf8");

describe("PWA readiness", () => {
  it("ships a real manifest with install shell metadata and maskable icon", () => {
    const manifest = JSON.parse(pub("manifest.webmanifest"));
    expect(manifest.name).toBe("NUR");
    expect(manifest.start_url).toBe("/today");
    expect(manifest.display).toBe("standalone");
    expect(manifest.icons.some((icon: { purpose?: string }) => icon.purpose?.includes("maskable"))).toBe(true);
  });

  it("does not cache API responses or secrets in the service worker", () => {
    const sw = pub("service-worker.js");
    expect(sw).toContain('url.pathname.startsWith("/api/")');
    expect(sw).toContain("offline.html");
    expect(sw).not.toMatch(/OPENAI_API_KEY|sk-[A-Za-z0-9_-]{20,}|Authorization/i);
  });

  it("boots the service worker from the nonvisual V197 bridge entry", () => {
    const entry = readFileSync(resolve(process.cwd(), "src", "main.ts"), "utf8");
    expect(entry).toContain('serviceWorker.register("/service-worker.js"');
    expect(entry).not.toMatch(/OPENAI_API_KEY|VITE_OPENAI/i);
  });

  it("keeps offline copy honest about local-only drafts", () => {
    const offline = pub("offline.html");
    expect(offline).toContain("The shell is cached");
    expect(offline).toContain("queued locally");
  });
});
