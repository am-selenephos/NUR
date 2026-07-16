import { expect, test, type Page } from "@playwright/test";

import {
  auditV197Viewport,
  overlappingV197Pairs,
  settleV197Layout,
  V197_REQUIRED_VIEWPORTS,
  visibleV197Rects,
  v197CenterDelta,
} from "./helpers/v197Geometry";
import { installNurMocks } from "./helpers/nurMocks";

async function authenticate(page: Page): Promise<void> {
  await installNurMocks(page);
  await page.context().addCookies([
    { name: "nur_session", value: "responsive-accessibility-session", url: "http://localhost:4173", httpOnly: true, sameSite: "Lax" },
    { name: "nur_csrf", value: "responsive-accessibility-csrf", url: "http://localhost:4173", httpOnly: false, sameSite: "Lax" },
  ]);
}

test("required viewport matrix preserves overflow, touch, node, and center contracts", async ({ page }) => {
  await authenticate(page);

  for (const viewport of V197_REQUIRED_VIEWPORTS) {
    await page.setViewportSize(viewport);
    await page.goto("/systems", { waitUntil: "load" });
    const frame = page.frameLocator("#nur-universe-stage");
    const body = frame.locator("body");
    await expect(frame.locator("#page-systems")).toBeVisible({ timeout: 20_000 });
    await settleV197Layout(body);

    const audit = await auditV197Viewport(body);
    expect(audit.documentWidth).toBeLessThanOrEqual(audit.viewportWidth + 1);
    expect(audit.escapedControls).toEqual([]);
    expect(audit.undersizedTouchTargets).toEqual([]);

    const nodeRects = await visibleV197Rects(body, ".universe-system-node");
    const brainAndNodes = await visibleV197Rects(
      body,
      ".universe-master-star, .universe-system-node",
    );
    const topbarGroups = await visibleV197Rects(
      body,
      ".nur-topbar > .universe-top-left, .nur-topbar > .universe-top-tools",
    );
    expect(overlappingV197Pairs(nodeRects)).toEqual([]);
    expect(overlappingV197Pairs(brainAndNodes)).toEqual([]);
    expect(overlappingV197Pairs(topbarGroups)).toEqual([]);

    const centerDelta = await v197CenterDelta(
      body,
      ".universe-map-title",
      ".universe-master-star",
    );
    expect(centerDelta).toBeLessThanOrEqual(1);
  }
});

test("RTL and deliberately long labels keep controls reachable", async ({ page }) => {
  await authenticate(page);

  for (const viewport of [{ width: 390, height: 844 }, { width: 1440, height: 900 }] as const) {
    await page.setViewportSize(viewport);
    await page.goto("/systems", { waitUntil: "load" });
    const frame = page.frameLocator("#nur-universe-stage");
    const body = frame.locator("body");
    await expect(frame.locator("#page-systems")).toBeVisible({ timeout: 20_000 });
    await body.evaluate(() => {
      document.documentElement.dir = "rtl";
      document.documentElement.lang = "ur";
      document.querySelectorAll<HTMLElement>(".clean-nav-title, .universe-system-node b")
        .forEach(element => {
          element.dataset.originalLabel = element.textContent ?? "";
          element.textContent = `${element.textContent} - a deliberately long translated interface label`;
        });
    });
    await settleV197Layout(body);

    const audit = await auditV197Viewport(body);
    expect(audit.documentWidth).toBeLessThanOrEqual(audit.viewportWidth + 1);
    expect(audit.escapedControls).toEqual([]);
    expect(overlappingV197Pairs(await visibleV197Rects(body, ".universe-system-node"))).toEqual([]);
  }
});

test("scope modal traps focus, closes with Escape, and restores its trigger", async ({ page }) => {
  await authenticate(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/systems", { waitUntil: "load" });
  const frame = page.frameLocator("#nur-universe-stage");
  const trigger = frame.locator("#scope-open");
  const modal = frame.locator("#scope-modal");
  await expect(trigger).toBeVisible({ timeout: 20_000 });
  await trigger.focus();
  await trigger.press("Enter");
  await expect(modal).toHaveClass(/open/);
  await expect(modal).toHaveAttribute("aria-hidden", "false");
  await expect.poll(() => modal.evaluate(element => element.contains(document.activeElement))).toBe(true);

  await modal.press("Escape");
  await expect(modal).not.toHaveClass(/open/);
  await expect(modal).toHaveAttribute("aria-hidden", "true");
  await expect(trigger).toBeFocused();
});

test("reduced motion leaves the exact brain intact and collapses decorative timing", async ({ page }) => {
  await authenticate(page);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/today", { waitUntil: "load" });
  const frame = page.frameLocator("#nur-universe-stage");
  await expect(frame.locator("#page-today")).toBeVisible({ timeout: 20_000 });

  const result = await frame.locator("body").evaluate(() => {
    const control = document.querySelector<HTMLElement>(".clean-nav-button");
    const runtime = (window as unknown as { __nurV197?: { points: number } }).__nurV197;
    const style = control ? getComputedStyle(control) : null;
    return {
      points: runtime?.points,
      animationDuration: style?.animationDuration,
      transitionDuration: style?.transitionDuration,
      sparkfield: document.querySelectorAll("#v197-sparkfield").length,
    };
  });
  expect([708, 1060]).toContain(result.points);
  expect(result.animationDuration).toBe("0.00001s");
  expect(result.transitionDuration).toBe("0.00001s");
  expect(result.sparkfield).toBe(0);
});
