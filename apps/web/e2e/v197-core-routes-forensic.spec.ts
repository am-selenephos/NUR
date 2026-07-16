import { expect, test, type FrameLocator, type Page } from "@playwright/test";

import { installNurMocks } from "./helpers/nurMocks";

const routes = ["/today", "/talk", "/journal", "/plan", "/systems"] as const;
const viewports = [{ width: 390, height: 844 }, { width: 1440, height: 900 }] as const;

async function authenticate(page: Page): Promise<void> {
  await installNurMocks(page);
  await page.context().addCookies([
    { name: "nur_session", value: "forensic-session", url: "http://localhost:4173", httpOnly: true, sameSite: "Lax" },
    { name: "nur_csrf", value: "forensic-csrf", url: "http://localhost:4173", httpOnly: false, sameSite: "Lax" },
  ]);
}

async function waitForRoute(frame: FrameLocator, route: string): Promise<void> {
  const pageName = route.slice(1);
  await expect(frame.locator(`#page-${pageName}`)).toBeVisible({ timeout: 20_000 });
}

test("core routes retain authentic controls and bounded geometry", async ({ page }) => {
  await authenticate(page);

  for (const viewport of viewports) {
    await page.setViewportSize(viewport);
    for (const route of routes) {
      await page.goto(route, { waitUntil: "load" });
      const frame = page.frameLocator("#nur-universe-stage");
      await waitForRoute(frame, route);

      const result = await frame.locator("body").evaluate(async () => {
        await new Promise<void>(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve())));
        const visible = (element: HTMLElement) => {
          const style = getComputedStyle(element);
          const rect = element.getBoundingClientRect();
          return style.display !== "none" && style.visibility !== "hidden" && Number(style.opacity) > 0
            && rect.width > 0 && rect.height > 0;
        };
        const escaped = Array.from(document.querySelectorAll<HTMLElement>("button, a, input, textarea, select"))
          .filter(element => visible(element) && !element.closest("[hidden], [aria-hidden='true']"))
          .filter(element => {
            const rect = element.getBoundingClientRect();
            return rect.left < -1 || rect.right > innerWidth + 1;
          })
          .map(element => `${element.tagName.toLowerCase()}.${element.className}`);
        const primaryControls = Array.from(document.querySelectorAll<HTMLElement>(
          ".f4-primary, .f4-submit, .thought-send-button, .universe-send",
        )).filter(visible);
        const selectedSeals = document.querySelectorAll(
          ".clean-nav-button.active > .clean-nav-glyph .nur-star-seal--state use",
        ).length;

        return {
          width: document.documentElement.scrollWidth,
          viewportWidth: innerWidth,
          escaped,
          oldMiniModules: document.querySelectorAll(".nur-star-module, .nur-v197-mini-star-lite").length,
          spriteCount: document.querySelectorAll("#nur-v197-star-seal-sprite").length,
          selectedSeals,
          primaryControls: primaryControls.length,
          primarySeals: primaryControls.filter(control => (
            control.querySelector(":scope > .nur-star-seal--control use")
          )).length,
        };
      });

      expect(result.width).toBeLessThanOrEqual(result.viewportWidth + 1);
      expect(result.escaped).toEqual([]);
      expect(result.oldMiniModules).toBe(0);
      expect(result.spriteCount).toBe(1);
      expect(result.selectedSeals).toBe(1);
      expect(result.primarySeals).toBe(result.primaryControls);
    }
  }
});

test("Systems uses small unframed stars and non-overlapping mobile rows", async ({ page }) => {
  await authenticate(page);

  for (const viewport of viewports) {
    await page.setViewportSize(viewport);
    await page.goto("/systems", { waitUntil: "load" });
    const frame = page.frameLocator("#nur-universe-stage");
    await waitForRoute(frame, "/systems");

    const result = await frame.locator("body").evaluate(async () => {
      await new Promise<void>(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve())));
      const icons = Array.from(document.querySelectorAll<HTMLElement>(
        ".universe-system-node > .nur-exact-icon-shell",
      )).map(icon => {
        const style = getComputedStyle(icon);
        const rect = icon.getBoundingClientRect();
        return {
          marker: icon.dataset.nurAuthenticStarHost,
          width: rect.width,
          height: rect.height,
          borderRadius: style.borderRadius,
          backgroundImage: style.backgroundImage,
          boxShadow: style.boxShadow,
          sealUses: icon.querySelectorAll(".nur-star-seal--24 use").length,
        };
      });
      const rows = Array.from(document.querySelectorAll<HTMLElement>(".universe-system-node"))
        .map(row => {
          const rect = row.getBoundingClientRect();
          return { top: rect.top, bottom: rect.bottom, left: rect.left, right: rect.right };
        })
        .sort((a, b) => a.top - b.top);
      return { icons, rows, mobile: innerWidth <= 430 };
    });

    expect(result.icons).toHaveLength(7);
    result.icons.forEach(icon => {
      expect(icon.marker).toBe("true");
      expect(icon.width).toBeLessThanOrEqual(34.5);
      expect(icon.height).toBeLessThanOrEqual(34.5);
      expect(icon.borderRadius).toBe("0px");
      expect(icon.backgroundImage).toBe("none");
      expect(icon.boxShadow).toBe("none");
      expect(icon.sealUses).toBe(1);
    });

    if (result.mobile) {
      for (let index = 1; index < result.rows.length; index += 1) {
        expect(result.rows[index]!.top).toBeGreaterThanOrEqual(result.rows[index - 1]!.bottom - 1);
        expect(result.rows[index]!.left).toBeGreaterThanOrEqual(-1);
        expect(result.rows[index]!.right).toBeLessThanOrEqual(viewport.width + 1);
      }
    }
  }
});

test("Entry primary action is transparent spectral glass with a real seal", async ({ page }) => {
  await installNurMocks(page);
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/", { waitUntil: "load" });
  const frame = page.frameLocator("#nur-entry-stage");
  await frame.locator("body").evaluate(() => {
    (window as unknown as { nurShowFront?: () => void }).nurShowFront?.();
  });
  const button = frame.locator("#f4-begin");
  await expect(button).toBeVisible({ timeout: 20_000 });
  await expect(button.locator(":scope > .nur-star-seal--control use")).toHaveCount(1);
  await expect(button).toHaveCSS("border-radius", "7px");
  await expect(button).toHaveCSS("background-color", "rgba(0, 0, 0, 0)");
});
