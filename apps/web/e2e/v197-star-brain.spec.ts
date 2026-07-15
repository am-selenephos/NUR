import { expect, test, type Locator } from "@playwright/test";

import { installNurMocks } from "./helpers/nurMocks";

type LockupGeometry = {
  word: { element: number; text: number };
  subtitle: { element: number; text: number };
};

async function lockupGeometry(
  root: Locator,
  wordSelector: string,
  subtitleSelector: string,
): Promise<LockupGeometry> {
  return root.evaluate((element, selectors) => {
    const center = (selector: string) => {
      const target = element.querySelector<HTMLElement>(selector);
      if (!target) throw new Error(`Missing lockup element: ${selector}`);
      const rect = target.getBoundingClientRect();
      const range = document.createRange();
      range.selectNodeContents(target);
      const textRect = range.getBoundingClientRect();
      return {
        element: rect.left + rect.width / 2,
        text: textRect.left + textRect.width / 2,
      };
    };
    return {
      word: center(selectors.wordSelector),
      subtitle: center(selectors.subtitleSelector),
    };
  }, { wordSelector, subtitleSelector });
}

function expectSameCenter(geometry: LockupGeometry): void {
  expect(Math.abs(geometry.word.element - geometry.subtitle.element)).toBeLessThanOrEqual(.25);
  expect(Math.abs(geometry.word.text - geometry.subtitle.text)).toBeLessThanOrEqual(.25);
}

test("Entry replaces the center MasterStar with the exact interactive V197 brain", async ({ page }, testInfo) => {
  await page.goto("/", { waitUntil: "load" });
  const entry = page.frameLocator("#nur-entry-stage");
  await expect.poll(() => entry.locator("body").evaluate(() => (
    typeof (window as unknown as { nurShowFront?: unknown }).nurShowFront
  ))).toBe("function");
  await entry.locator("body").evaluate(() => {
    (window as unknown as { nurShowFront: () => void }).nurShowFront();
    return document.fonts.ready;
  });

  const brain = entry.locator("#f4-core > #front-nur-star");
  await expect(brain).toBeVisible();
  await expect(entry.locator("#f4-core > .spark, #f4-core > .f4-master-star")).toHaveCount(0);
  await expect(entry.locator("#f4-core")).toHaveAttribute("data-nur-legacy-master-star", "removed");
  await expect(brain).toHaveAttribute("data-nur-source", "exact-v197-star-brain-galaxy-port");
  await expect(brain).toHaveAttribute("title", /drag to spin the mind.+double-click: neural storm.+scroll to zoom/);

  const expectedPoints = testInfo.project.name.includes("mobile") ? 708 : 1060;
  await expect.poll(() => entry.locator("body").evaluate(() => {
    const runtime = (window as unknown as {
      __nurV197?: { version: string; points: number; edges: number; mode: string };
    }).__nurV197;
    return runtime && {
      version: runtime.version,
      points: runtime.points,
      edges: runtime.edges,
      mode: runtime.mode,
    };
  })).toMatchObject({ version: "V197", points: expectedPoints, mode: "live" });

  const geometry = await lockupGeometry(
    entry.locator(".f4-brand-copy"),
    ".f4-brand-word",
    ".f4-brand-sub",
  );
  expectSameCenter(geometry);

  await brain.locator("#nur-brain-canvas-v197").click();
  await expect.poll(() => entry.locator("body").evaluate(() => (
    window as unknown as { __nurV197?: { mode: string } }
  ).__nurV197?.mode)).toBe("shatter");
});

test("Systems map mounts only the exact brain and keeps the NUR lockup on one axis", async ({ page }, testInfo) => {
  await installNurMocks(page);
  await page.context().addCookies([
    { name: "nur_session", value: "star-brain-session", url: "http://localhost:4173", httpOnly: true, sameSite: "Lax" },
    { name: "nur_csrf", value: "star-brain-csrf", url: "http://localhost:4173", httpOnly: false, sameSite: "Lax" },
  ]);
  await page.goto("/systems", { waitUntil: "load" });
  const universe = page.frameLocator("#nur-universe-stage");
  await expect(universe.locator("#page-systems")).toBeVisible({ timeout: 15_000 });
  await universe.locator("body").evaluate(() => document.fonts.ready);

  const host = universe.locator(".universe-master-star");
  const brain = host.locator(":scope > #front-nur-star");
  await expect(brain).toBeVisible();
  await expect(host.locator(":scope > .f4-core")).toHaveCount(0);
  await expect(host).toHaveAttribute("data-nur-legacy-master-star", "removed");
  await expect(brain.locator("#nur-brain-canvas-v197")).toBeVisible();

  const expectedPoints = testInfo.project.name.includes("mobile") ? 708 : 1060;
  await expect.poll(() => universe.locator("body").evaluate(() => {
    const runtime = (window as unknown as {
      __nurV197?: { version: string; points: number; edges: number; mode: string };
    }).__nurV197;
    return runtime && {
      version: runtime.version,
      points: runtime.points,
      edges: runtime.edges,
      mode: runtime.mode,
    };
  })).toMatchObject({ version: "V197", points: expectedPoints, mode: "live" });
  const edges = await universe.locator("body").evaluate(() => (
    window as unknown as { __nurV197?: { edges: number } }
  ).__nurV197?.edges ?? 0);
  expect(edges).toBeGreaterThan(expectedPoints * .86);

  const geometry = await lockupGeometry(
    universe.locator(".universe-map-title"),
    ".nur-v197-stable-wordmark",
    ".nur-master-subtitle",
  );
  expectSameCenter(geometry);

  await brain.locator("#nur-brain-canvas-v197").click();
  await expect.poll(() => universe.locator("body").evaluate(() => (
    window as unknown as { __nurV197?: { mode: string } }
  ).__nurV197?.mode)).toBe("shatter");
});
