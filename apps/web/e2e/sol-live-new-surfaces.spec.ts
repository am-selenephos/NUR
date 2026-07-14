import { mkdir } from "node:fs/promises";
import { dirname, join } from "node:path";
import { expect, test, type Page } from "@playwright/test";

const proofRoot = process.env.NUR_SOL_LIVE_PROOF_DIR
  ?? (process.cwd().endsWith("/apps/web") ? "../../proof/sol-live-surfaces" : "proof/sol-live-surfaces");

async function shot(page: Page, name: string): Promise<void> {
  const path = join(proofRoot, name);
  await mkdir(dirname(path), { recursive: true });
  await page.screenshot({ path, fullPage: false, animations: "disabled" });
}

async function signIn(page: Page): Promise<void> {
  await page.goto("/");
  const entry = page.frameLocator("#nur-entry-stage");
  await entry.locator("body").evaluate(() => {
    (window as unknown as { nurShowFront?: () => void }).nurShowFront?.();
  });
  await entry.locator("#f4-signin").click();
  await entry.locator("#f4-signin-email").fill("owner@nur.app");
  await entry.locator("#f4-signin-password").fill("owner-demo-pass-123");
  await entry.locator("#f4-signin-form button[type='submit']").click();
  await expect(page.locator("#nur-universe-stage")).toHaveClass(/is-visible/, { timeout: 25_000 });
}

test("live seeded SOL surfaces stay V197-native and persisted", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "chromium-desktop", "One live owner journey is enough; mobile uses mocked and real WebKit boundary proof.");
  test.setTimeout(120_000);
  await signIn(page);
  await expect(page.locator("#root")).toHaveCount(0);
  await expect(page.locator('link[rel="manifest"]')).toHaveAttribute("href", "/manifest.webmanifest");
  const universe = page.frameLocator("#nur-universe-stage");

  await page.goto("/settings");
  await expect(universe.locator("#nur-v197-adjunct-root")).toContainText("OPENAI_CONFIGURED");
  await shot(page, "live-settings-openai-configured.png");

  await page.goto("/community");
  await expect(universe.locator("#nur-v197-adjunct-root")).toContainText("NUR release room");
  await expect(universe.locator("#nur-v197-adjunct-root")).toContainText("No fake people");
  await shot(page, "live-community-bounded-feed.png");

  await page.goto("/consultations");
  await expect(universe.locator("#nur-v197-adjunct-root")).toContainText("Release readiness return");
  await universe.locator('[data-adjunct-action^="consultation-open-"]').first().click();
  await expect(universe.locator("#nur-v197-adjunct-root")).toContainText("visual proof cannot replace recipient-isolation proof");
  await expect(universe.locator("#nur-v197-adjunct-root")).toContainText("RETURN");
  await shot(page, "live-consultation-return-ready.png");

  await page.goto("/projects");
  await expect(universe.locator("#nur-v197-adjunct-root")).toContainText("V197 owner-ledger release");
  await universe.locator('[data-adjunct-action^="project-open-"]').first().click();
  await expect(universe.locator("#nur-v197-adjunct-root")).toContainText("No run can pre-authorize spending");
  await shot(page, "live-am-project-cockpit.png");

  await page.goto("/glow");
  await expect(universe.locator("#nur-v197-adjunct-root")).toContainText("Source-linked ledger");
  await expect(universe.locator("#nur-v197-adjunct-root")).toContainText("Current constellation");
  await shot(page, "live-glow-ledger.png");

  await page.goto("/notifications");
  await expect(universe.locator("#nur-v197-adjunct-root")).toContainText("Return cues, under your control");
  await expect(universe.locator("#nur-v197-adjunct-root")).toContainText("Return to the V197 release proof");
  const unread = universe.locator('[data-adjunct-action^="notification-read-"]').first();
  if (await unread.count()) {
    const action = await unread.getAttribute("data-adjunct-action");
    await unread.click();
    await page.reload();
    await expect(universe.locator(`[data-adjunct-action="${action}"]`)).toHaveCount(0);
  }
  await expect(universe.locator("#nur-v197-adjunct-root")).toContainText("IN_APP_ONLY");
  await shot(page, "live-notifications-owner-ledger.png");

  await page.goto("/universe/omega");
  await expect(universe.locator("#nur-v197-adjunct-root")).toContainText("Consolidation status");
  await shot(page, "live-omega-owner-ledger.png");
});
