import { mkdir } from "node:fs/promises";
import { join } from "node:path";

import { expect, test, type FrameLocator, type Page } from "@playwright/test";

const proofRoot = process.env.NUR_SOL_PROOF_DIR
  ?? (process.cwd().endsWith("/apps/web") ? "../../proof/sol-living-v197" : "proof/sol-living-v197");

async function signIn(page: Page): Promise<FrameLocator> {
  await page.goto("/", { waitUntil: "load" });
  const entry = page.frameLocator("#nur-entry-stage");
  await entry.locator("body").evaluate(() => {
    (window as unknown as { nurShowFront?: () => void }).nurShowFront?.();
  });
  await entry.locator("#f4-signin").click();
  await entry.locator("#f4-signin-email").fill("owner@nur.app");
  await entry.locator("#f4-signin-password").fill("owner-demo-pass-123");
  await entry.locator("#f4-signin-form button[type='submit']").click();
  await expect(page.locator("#nur-universe-stage")).toHaveClass(/is-visible/, { timeout: 20_000 });
  const universe = page.frameLocator("#nur-universe-stage");
  await expect(universe.locator("#page-systems")).toBeVisible({ timeout: 20_000 });
  return universe;
}

test("V197 keeps Bodoni holographic NUR motion and dark native language controls", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "chromium-desktop", "Desktop visual lock runs once.");
  test.setTimeout(60_000);
  await page.setViewportSize({ width: 1440, height: 900 });
  const universe = await signIn(page);
  await expect(page.locator("#root")).toHaveCount(0);

  const wordmark = universe.locator(".nur-v197-stable-wordmark");
  await expect(wordmark).toBeVisible();
  const before = await wordmark.evaluate(node => {
    const style = getComputedStyle(node);
    return {
      fontFamily: style.fontFamily,
      backgroundImage: style.backgroundImage,
      backgroundPosition: style.backgroundPosition,
      animationName: style.animationName,
      textFill: style.getPropertyValue("-webkit-text-fill-color"),
    };
  });
  expect(before.fontFamily).toContain("Bodoni Moda");
  expect(before.backgroundImage).toContain("linear-gradient");
  expect(before.backgroundImage).toContain("rgb(84, 234, 255)");
  expect(before.backgroundImage).toContain("rgb(234, 130, 255)");
  expect(before.animationName).toContain("nurV197StableWordmarkFlow");
  expect(before.animationName).toContain("nurV197StableWordmarkGlow");
  expect(before.textFill).toMatch(/^(transparent|rgba\(0, 0, 0, 0\))$/);
  await page.waitForTimeout(1_200);
  const afterPosition = await wordmark.evaluate(node => getComputedStyle(node).backgroundPosition);
  expect(afterPosition).not.toBe(before.backgroundPosition);

  await mkdir(proofRoot, { recursive: true });
  await page.screenshot({
    path: join(proofRoot, "00g-v197-bodoni-holographic-rainbow-wordmark.png"),
    fullPage: false,
  });

  await universe.locator("#nur-v197-language-open").click();
  await expect(universe.locator("#scope-modal")).toHaveClass(/open/);
  await expect(universe.locator("#nur-v197-locale option")).toHaveCount(35);
  const selectVisuals = await universe.locator("#nur-v197-locale").evaluate(node => {
    const selectStyle = getComputedStyle(node);
    const shellStyle = getComputedStyle(node.parentElement as HTMLElement);
    return {
      appearance: selectStyle.appearance,
      colorScheme: selectStyle.colorScheme,
      textColor: selectStyle.color,
      shellBackground: shellStyle.backgroundImage,
      shellColor: shellStyle.backgroundColor,
      shellBorder: shellStyle.borderColor,
    };
  });
  expect(selectVisuals.appearance).toBe("none");
  expect(selectVisuals.colorScheme).toBe("dark");
  expect(selectVisuals.shellBackground).toContain("linear-gradient");
  expect(selectVisuals.shellColor).not.toBe("rgb(255, 255, 255)");
  expect(selectVisuals.textColor).not.toBe("rgb(0, 0, 0)");
  expect(selectVisuals.shellBorder).not.toBe("rgb(255, 255, 255)");
  await page.screenshot({
    path: join(proofRoot, "00h-v197-dark-glass-language-dropdown.png"),
    fullPage: false,
    animations: "disabled",
  });
});
