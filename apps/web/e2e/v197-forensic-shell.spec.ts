import { expect, test, type Page } from "@playwright/test";

import { installNurMocks } from "./helpers/nurMocks";

const targetViewports = [
  { width: 360, height: 800 },
  { width: 390, height: 844 },
  { width: 430, height: 932 },
  { width: 844, height: 390 },
  { width: 768, height: 1024 },
  { width: 1024, height: 768 },
  { width: 1280, height: 720 },
  { width: 1366, height: 768 },
  { width: 1440, height: 900 },
  { width: 1920, height: 1080 },
  { width: 2560, height: 1080 },
  { width: 2560, height: 1440 },
] as const;

async function installAuthenticatedMocks(page: Page): Promise<void> {
  await installNurMocks(page);
  await page.context().addCookies([
    { name: "nur_session", value: "forensic-session", url: "http://localhost:4173", httpOnly: true, sameSite: "Lax" },
    { name: "nur_csrf", value: "forensic-csrf", url: "http://localhost:4173", httpOnly: false, sameSite: "Lax" },
  ]);
}

test("shared shell stays inside every required viewport", async ({ page }) => {
  await installAuthenticatedMocks(page);

  for (const viewport of targetViewports) {
    await page.setViewportSize(viewport);
    await page.goto("/systems", { waitUntil: "load" });
    const frame = page.frameLocator("#nur-universe-stage");
    await expect(frame.locator("#page-systems")).toBeVisible({ timeout: 20_000 });

    const geometry = await frame.locator("body").evaluate(async () => {
      await new Promise<void>(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve())));
      const rect = (selector: string) => {
        const element = document.querySelector<HTMLElement>(selector);
        if (!element || getComputedStyle(element).display === "none") return null;
        const bounds = element.getBoundingClientRect();
        return {
          left: bounds.left,
          right: bounds.right,
          top: bounds.top,
          bottom: bounds.bottom,
          width: bounds.width,
          height: bounds.height,
        };
      };
      const escapedControls = Array.from(document.querySelectorAll<HTMLElement>("button, a, input, textarea, select"))
        .filter(element => {
          const style = getComputedStyle(element);
          if (
            style.display === "none"
            || style.visibility === "hidden"
            || style.opacity === "0"
            || element.closest("[hidden], [aria-hidden='true']")
          ) return false;
          const bounds = element.getBoundingClientRect();
          return bounds.width > 0
            && bounds.height > 0
            && (bounds.left < -1 || bounds.right > innerWidth + 1);
        })
        .map(element => `${element.tagName.toLowerCase()}.${element.className}`);

      return {
        shell: rect(".nur-shell"),
        leftRail: rect(".clean-left-rail"),
        rightRail: rect(".clean-right-rail"),
        topbar: rect(".nur-topbar"),
        viewport: rect(".nur-viewport"),
        composer: rect(".global-composer"),
        mobileTabs: rect(".mobile-tabs"),
        documentWidth: document.documentElement.scrollWidth,
        viewportWidth: innerWidth,
        escapedControls,
        brainHosts: document.querySelectorAll("#front-nur-star").length,
        brainCanvases: document.querySelectorAll("#nur-brain-canvas-v197").length,
      };
    });

    expect(geometry.shell).not.toBeNull();
    expect(Math.abs((geometry.shell?.width ?? 0) - viewport.width)).toBeLessThanOrEqual(1);
    expect(Math.abs((geometry.shell?.height ?? 0) - viewport.height)).toBeLessThanOrEqual(1);
    expect(geometry.documentWidth).toBeLessThanOrEqual(geometry.viewportWidth + 1);
    expect(geometry.escapedControls).toEqual([]);
    expect(geometry.brainHosts).toBe(1);
    expect(geometry.brainCanvases).toBe(1);

    if (viewport.width <= 900) {
      expect(geometry.leftRail).toBeNull();
      expect(geometry.rightRail).toBeNull();
      expect(geometry.composer).not.toBeNull();
      expect(geometry.mobileTabs).not.toBeNull();
      expect(Math.abs((geometry.mobileTabs?.bottom ?? 0) - viewport.height)).toBeLessThanOrEqual(1);
      expect(Math.abs((geometry.composer?.bottom ?? 0) - (geometry.mobileTabs?.top ?? 0))).toBeLessThanOrEqual(1);
    } else {
      expect(geometry.leftRail).not.toBeNull();
      expect(geometry.composer).toBeNull();
      expect(geometry.mobileTabs).toBeNull();
      expect(geometry.rightRail === null).toBe(viewport.width < 1600);
    }

    expect(Math.abs((geometry.topbar?.bottom ?? 0) - (geometry.viewport?.top ?? 0))).toBeLessThanOrEqual(1);
  }
});

test("Today owns one visible exact V197 brain renderer", async ({ page }) => {
  await installAuthenticatedMocks(page);

  for (const viewport of [{ width: 390, height: 844 }, { width: 1440, height: 900 }] as const) {
    await page.setViewportSize(viewport);
    await page.goto("/today", { waitUntil: "load" });
    const frame = page.frameLocator("#nur-universe-stage");
    await expect(frame.locator("#page-today")).toBeVisible({ timeout: 20_000 });
    await expect(frame.locator("#page-today .orbit-star-zone > .f4-core > #front-nur-star")).toBeVisible();
    await expect(frame.locator("#nur-brain-canvas-v197")).toBeVisible();

    const brain = await frame.locator("body").evaluate(() => {
      const canvas = document.querySelector<HTMLCanvasElement>("#nur-brain-canvas-v197");
      const context = canvas?.getContext("2d");
      const runtime = (window as unknown as {
        __nurV197?: { version: string; points: number; edges: number; mode: string };
      }).__nurV197;
      let paintedSamples = 0;
      if (canvas && context) {
        const pixels = context.getImageData(0, 0, canvas.width, canvas.height).data;
        const stride = Math.max(4, Math.floor(pixels.length / 6000 / 4) * 4);
        for (let index = 3; index < pixels.length; index += stride) {
          if (pixels[index] > 8) paintedSamples += 1;
        }
      }
      return {
        hosts: document.querySelectorAll("#front-nur-star").length,
        canvases: document.querySelectorAll("#nur-brain-canvas-v197").length,
        surface: document.querySelector<HTMLElement>("#front-nur-star")?.dataset.nurSurface,
        paintedSamples,
        runtime,
      };
    });

    const expectedPoints = viewport.width < 700 ? 708 : 1060;
    expect(brain.hosts).toBe(1);
    expect(brain.canvases).toBe(1);
    expect(brain.surface).toBe("today");
    expect(brain.paintedSamples).toBeGreaterThan(100);
    expect(brain.runtime).toMatchObject({ version: "V197", points: expectedPoints, mode: "live" });
    expect(brain.runtime?.edges ?? 0).toBeGreaterThan(expectedPoints * .86);
  }
});
