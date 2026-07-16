import { expect, test } from "@playwright/test";

import { installNurMocks } from "./helpers/nurMocks";

test("exact star brain owns one adaptive runtime and releases it cleanly", async ({ page }, testInfo) => {
  await installNurMocks(page);
  await page.context().addCookies([
    { name: "nur_session", value: "runtime-lifecycle-session", url: "http://localhost:4173", httpOnly: true, sameSite: "Lax" },
    { name: "nur_csrf", value: "runtime-lifecycle-csrf", url: "http://localhost:4173", httpOnly: false, sameSite: "Lax" },
  ]);
  await page.goto("/systems", { waitUntil: "load" });

  const universe = page.frameLocator("#nur-universe-stage");
  await expect(universe.locator("#page-systems")).toBeVisible({ timeout: 15_000 });
  const host = universe.locator("#front-nur-star");
  const canvas = host.locator("#nur-brain-canvas-v197");
  await expect(canvas).toHaveCount(1);
  await expect(universe.locator("#nur-v197-exact-star-brain-runtime"))
    .toHaveAttribute("data-nur-lifecycle-profile", "adaptive-lifecycle-v1");
  await expect(universe.locator("#v197-sparkfield")).toHaveCount(0);

  const expectedPoints = testInfo.project.name.includes("mobile") ? 708 : 1060;
  await expect.poll(() => universe.locator("body").evaluate(() => (
    window as unknown as { __nurV197?: { points: number; frameTime: number } }
  ).__nurV197)).toMatchObject({ points: expectedPoints });

  const wheelOwnership = await canvas.evaluate(element => {
    const ordinary = new WheelEvent("wheel", { bubbles: true, cancelable: true, deltaY: 80 });
    const intentional = new WheelEvent("wheel", {
      bubbles: true,
      cancelable: true,
      ctrlKey: true,
      deltaY: -80,
    });
    element.dispatchEvent(ordinary);
    element.dispatchEvent(intentional);
    return {
      ordinaryPrevented: ordinary.defaultPrevented,
      intentionalPrevented: intentional.defaultPrevented,
    };
  });
  expect(wheelOwnership).toEqual({ ordinaryPrevented: false, intentionalPrevented: true });

  const disposed = await universe.locator("body").evaluate(() => {
    const runtime = (window as unknown as {
      __nurV197?: { dispose: () => void; running: boolean };
    }).__nurV197;
    runtime?.dispose();
    return {
      globalReleased: !(window as unknown as { __nurV197?: unknown }).__nurV197,
      running: runtime?.running ?? false,
    };
  });
  expect(disposed).toEqual({ globalReleased: true, running: false });
});
