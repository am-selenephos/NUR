import { expect, test, type Page } from "@playwright/test";

import { installNurMocks } from "./helpers/nurMocks";

const lenses = [
  { route: "/universe/map", testId: "universe-map-page" },
  { route: "/universe/orbits", testId: "universe-orbits-page" },
  { route: "/universe/timeline", testId: "universe-timeline-page" },
  { route: "/universe/insights", testId: "universe-insights-page" },
  { route: "/universe/research", testId: "universe-research-page" },
  { route: "/universe/community", testId: "universe-community-page" },
  { route: "/universe/web-signals", testId: "universe-web-signals-page" },
] as const;

async function authenticate(page: Page): Promise<void> {
  await installNurMocks(page);
  await page.context().addCookies([
    { name: "nur_session", value: "forensic-session", url: "http://localhost:4173", httpOnly: true, sameSite: "Lax" },
    { name: "nur_csrf", value: "forensic-csrf", url: "http://localhost:4173", httpOnly: false, sameSite: "Lax" },
  ]);
}

test("all seven Universe lenses share bounded black-glass laws", async ({ page }) => {
  await authenticate(page);

  for (const viewport of [{ width: 390, height: 844 }, { width: 1440, height: 900 }] as const) {
    await page.setViewportSize(viewport);
    for (const lens of lenses) {
      await page.goto(lens.route, { waitUntil: "load" });
      const root = page.getByTestId(lens.testId);
      await expect(root).toBeVisible({ timeout: 20_000 });
      const result = await root.evaluate(async element => {
        await new Promise<void>(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve())));
        const visible = (node: HTMLElement) => {
          const style = getComputedStyle(node);
          const rect = node.getBoundingClientRect();
          return style.display !== "none" && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0;
        };
        const controls = Array.from(element.querySelectorAll<HTMLElement>("button, input, textarea, select")).filter(visible);
        const excessiveRadii = controls.map(control => ({
          name: `${control.tagName.toLowerCase()}.${control.className}`,
          radius: Number.parseFloat(getComputedStyle(control).borderTopLeftRadius),
        })).filter(control => control.radius > 7.5);
        const bounds = element.getBoundingClientRect();
        return {
          left: bounds.left,
          right: bounds.right,
          scrollWidth: document.documentElement.scrollWidth,
          viewportWidth: innerWidth,
          excessiveRadii,
          fakeGlyphs: (element.textContent?.match(/[✦✧★☆]/g) ?? []).length,
        };
      });

      expect(result.left).toBeGreaterThanOrEqual(-1);
      expect(result.right).toBeLessThanOrEqual(viewport.width + 1);
      expect(result.scrollWidth).toBeLessThanOrEqual(result.viewportWidth + 1);
      expect(result.excessiveRadii).toEqual([]);
      expect(result.fakeGlyphs).toBe(0);
    }
  }
});

test("Map owns the exact brain and seven authentic node seals", async ({ page }) => {
  await authenticate(page);

  for (const viewport of [{ width: 390, height: 844 }, { width: 1440, height: 900 }] as const) {
    await page.setViewportSize(viewport);
    await page.goto("/universe/map", { waitUntil: "load" });
    const root = page.getByTestId("universe-map-page");
    await expect(root).toBeVisible({ timeout: 20_000 });
    await expect(root.locator(".lens-map-master > #front-nur-star[data-nur-surface='map']")).toBeVisible();
    await expect(root.locator("#nur-brain-canvas-v197")).toBeVisible();
    await expect(root.locator(".lens-map-master > .spark, .lens-map-master > .f4-master-star")).toHaveCount(0);
    await expect(root.locator(".lens-map-node [data-nur-authentic-star-host='true'] .nur-star-seal--16 use")).toHaveCount(7);

    const rows = await root.locator(".lens-map-node").evaluateAll(nodes => nodes
      .map(node => {
        const rect = node.getBoundingClientRect();
        return { top: rect.top, bottom: rect.bottom, left: rect.left, right: rect.right };
      })
      .sort((a, b) => a.top - b.top));
    rows.forEach(row => {
      expect(row.left).toBeGreaterThanOrEqual(-1);
      expect(row.right).toBeLessThanOrEqual(viewport.width + 1);
    });
    if (viewport.width <= 600) {
      for (let index = 1; index < rows.length; index += 1) {
        expect(rows[index]!.top).toBeGreaterThanOrEqual(rows[index - 1]!.bottom - 1);
      }
    }
  }
});
