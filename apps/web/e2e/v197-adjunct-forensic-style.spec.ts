import { expect, test, type Page } from "@playwright/test";

import { installNurMocks } from "./helpers/nurMocks";

const routes = [
  "/settings",
  "/capsule/cap-active",
  "/consultations",
  "/community",
  "/projects",
  "/glow",
  "/notifications",
  "/universe/omega",
] as const;

async function authenticate(page: Page): Promise<void> {
  await installNurMocks(page);
  await page.context().addCookies([
    { name: "nur_session", value: "forensic-session", url: "http://localhost:4173", httpOnly: true, sameSite: "Lax" },
    { name: "nur_csrf", value: "forensic-csrf", url: "http://localhost:4173", httpOnly: false, sameSite: "Lax" },
  ]);
}

test("adjunct routes use one bounded black-glass material system", async ({ page }) => {
  await authenticate(page);

  for (const viewport of [{ width: 390, height: 844 }, { width: 1440, height: 900 }] as const) {
    await page.setViewportSize(viewport);
    for (const route of routes) {
      await page.goto(route, { waitUntil: "load" });
      const frame = page.frameLocator("#nur-universe-stage");
      const root = frame.locator("#nur-v197-adjunct-root");
      await expect(root).toBeVisible({ timeout: 20_000 });
      await expect(root).toHaveAttribute("data-v197-native-adjunct", "true");

      const result = await root.evaluate(async element => {
        await new Promise<void>(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve())));
        const rootStyle = getComputedStyle(element);
        const before = getComputedStyle(element, "::before");
        const panels = Array.from(element.querySelectorAll<HTMLElement>(".nur-adjunct-panel"));
        const controls = Array.from(element.querySelectorAll<HTMLElement>(
          ".nur-adjunct-back, .nur-adjunct-button, .nur-adjunct-input, .nur-adjunct-select, .nur-adjunct-textarea",
        ));
        return {
          zIndex: Number(rootStyle.zIndex),
          rootBackground: rootStyle.backgroundImage,
          fakeWallpaper: before.content,
          scrollWidth: element.scrollWidth,
          clientWidth: element.clientWidth,
          panelRadii: panels.map(panel => Number.parseFloat(getComputedStyle(panel).borderTopLeftRadius)),
          controlRadii: controls.map(control => Number.parseFloat(getComputedStyle(control).borderTopLeftRadius)),
          oldBrown: controls.some(control => getComputedStyle(control).backgroundImage.includes("201, 105, 42")),
          brandSeals: element.querySelectorAll(".nur-adjunct-brand > .nur-adjunct-brand-seal use").length,
          primaryCount: element.querySelectorAll(".nur-adjunct-button.is-primary").length,
          primarySeals: element.querySelectorAll(".nur-adjunct-button.is-primary > .nur-star-seal--control use").length,
        };
      });

      expect(result.zIndex).toBeGreaterThan(0);
      expect(result.zIndex).toBeLessThan(1000);
      expect(result.fakeWallpaper).toBe("none");
      expect(result.scrollWidth).toBeLessThanOrEqual(result.clientWidth + 1);
      expect(result.panelRadii.every(radius => radius <= 7.5)).toBe(true);
      expect(result.controlRadii.every(radius => radius <= 7.5)).toBe(true);
      expect(result.oldBrown).toBe(false);
      expect(result.brandSeals).toBe(1);
      expect(result.primarySeals).toBe(result.primaryCount);
    }
  }
});
