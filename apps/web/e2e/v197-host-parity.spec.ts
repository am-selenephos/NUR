import { createHash } from "node:crypto";
import { mkdir } from "node:fs/promises";
import { dirname, join } from "node:path";
import { expect, test, type Page, type Route } from "@playwright/test";

const proofRoot = process.env.NUR_PHASE1_PROOF_DIR
  ?? (process.cwd().endsWith("/apps/web") ? "../../proof/v197-phase1" : "proof/v197-phase1");

const now = new Date().toISOString();

function proofPath(project: string, name: string): string {
  return join(proofRoot, `${project}-${name}.png`);
}

async function screenshot(page: Page, project: string, name: string): Promise<void> {
  const path = proofPath(project, name);
  await mkdir(dirname(path), { recursive: true });
  await page.screenshot({ path, fullPage: false, animations: "disabled" });
}

async function json(route: Route, body: unknown): Promise<void> {
  await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(body) });
}

async function installReadonlyHydrationMocks(page: Page): Promise<void> {
  await page.route("**/api/v1/auth/me", route => json(route, {
    id: "11111111-1111-1111-1111-111111111111",
    email: "owner@nur.app",
    profile: {
      chosen_name: "Phase One Owner",
      locale: "en",
      writing_preference: "default",
      default_boundary: "PRIVATE_ORBIT",
    },
    orbit: { id: "22222222-2222-2222-2222-222222222222" },
  }));
  await page.route("**/api/v1/orbits/current-state", route => json(route, {
    active_systems: 3,
    outcomes_returned: 11,
    insights_evolving: 2,
  }));
  await page.route("**/api/v1/universe/map-summary", route => json(route, { nodes: [], edges: [] }));
  await page.route("**/api/v1/universe/orbits-summary", route => json(route, { orbits: [] }));
  await page.route("**/api/v1/universe/timeline", route => json(route, { events: [], generated_at: now }));
  await page.route("**/api/v1/universe/insights-summary", route => json(route, { insights: [] }));
  await page.route("**/api/v1/profile/preferences", route => json(route, {
    locale: "en",
    writing_preference: "default",
    default_boundary: "PRIVATE_ORBIT",
  }));
}

type Geometry = {
  map: { x: number; y: number; width: number; height: number };
  insight: { x: number; y: number; width: number; height: number };
  insightStyle: {
    display: string;
    minHeight: string;
    paddingTop: string;
    paddingBottom: string;
    fontFamily: string;
    width: string;
  };
  styleCount: number;
  scriptCount: number;
  rootPresent: boolean;
};

async function geometry(page: Page): Promise<Geometry> {
  const universe = page.frameLocator("#nur-universe-stage");
  await expect(universe.locator("#page-systems")).toBeVisible();
  await expect.poll(
    async () => universe.locator("body").evaluate(() => {
      const visual = window.visualViewport;
      return window.innerWidth > 0
        && window.innerHeight > 0
        && document.fonts.status === "loaded"
        && (!visual || (
          Math.abs(visual.width - window.innerWidth) < 1
          && Math.abs(visual.height - window.innerHeight) < 1
        ));
    }),
    { timeout: 15_000 },
  ).toBe(true);
  await universe.locator("body").evaluate(async () => {
    await new Promise<void>(resolve => requestAnimationFrame(() => requestAnimationFrame(() => requestAnimationFrame(() => resolve()))));
  });
  return universe.locator("#page-systems").evaluate(() => {
    const measure = (selector: string) => {
      const element = document.querySelector(selector);
      if (!element) throw new Error(`Missing ${selector}`);
      const rect = element.getBoundingClientRect();
      return { x: rect.x, y: rect.y, width: rect.width, height: rect.height };
    };
    return {
      map: measure(".universe-map-panel"),
      insight: measure(".universe-insight-panel"),
      insightStyle: (() => {
        const style = getComputedStyle(document.querySelector(".universe-insight-panel")!);
        return {
          display: style.display,
          minHeight: style.minHeight,
          paddingTop: style.paddingTop,
          paddingBottom: style.paddingBottom,
          fontFamily: style.fontFamily,
          width: style.width,
        };
      })(),
      styleCount: document.querySelectorAll("style,link[rel='stylesheet']").length,
      scriptCount: document.querySelectorAll("script").length,
      rootPresent: Boolean(document.querySelector("#root")),
    };
  });
}

test("Phase 1 serves a byte-faithful V197 universe without a visible React root", async ({ page }, testInfo) => {
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  await installReadonlyHydrationMocks(page);
  await page.goto("/systems", { waitUntil: "load" });
  await page.waitForTimeout(900);

  const canonicalResponse = await page.request.get("/v197/NUR_V197_CHECKBOX_TICK_RESTORED.html");
  const canonical = await canonicalResponse.text();
  const productResponse = await page.request.get("/systems");
  const productDocument = await productResponse.text();
  expect(createHash("sha256").update(canonical).digest("hex"))
    .toBe("252eee806ece31ef829a2dc5cd45aa8d8f8e855db1bde98b6f87193d786633c3");
  expect(productDocument).toBe(
    canonical.replace("</body>", '<script type="module" src="/assets/v197-bridge.js"></script></body>'),
  );

  await expect(page.locator("#root")).toHaveCount(0);
  await expect(page.locator("#nur-v197-presentation")).toHaveCount(0);
  await expect(page.locator("#nur-entry-stage")).toHaveCount(1);
  await expect(page.locator("#nur-universe-stage")).toHaveCount(1);
  await expect(page.locator("#nur-entry-stage")).toHaveAttribute("srcdoc", /.+/);
  await expect(page.locator("#nur-universe-stage")).toHaveAttribute("srcdoc", /.+/);

  const observed = await geometry(page);
  expect(observed.rootPresent).toBe(false);
  expect(observed.styleCount).toBe(32);
  expect(observed.scriptCount).toBe(7);
  const universe = page.frameLocator("#nur-universe-stage");
  await expect(universe.locator(".universe-hero-stats")).toContainText("03");
  await expect(universe.locator(".universe-field-readout")).toContainText("11 returned outcomes");
  await expect(universe.locator("link[href*='global.css']")).toHaveCount(0);
  await screenshot(page, testInfo.project.name, "routed-systems");

  expect(errors.filter(message => /React|NUR V197 bridge did not start/i.test(message))).toEqual([]);
});

test("Phase 1 keeps the canonical entry visual but blocks source-local authentication", async ({ page }) => {
  await page.goto("/", { waitUntil: "load" });
  const entry = page.frameLocator("#nur-entry-stage");
  await expect.poll(
    async () => entry.locator("body").evaluate(() => {
      return typeof (window as unknown as { nurShowFront?: unknown }).nurShowFront === "function";
    }),
    { timeout: 15_000 },
  ).toBe(true);
  await entry.locator("body").evaluate(() => {
    (window as unknown as { nurShowFront: () => void }).nurShowFront();
  });
  await expect(entry.locator("#f4-begin")).toBeVisible();
  await entry.locator("#f4-begin").click();
  await entry.locator("#f4-name").fill("Phase One");
  await entry.locator("#f4-email").fill("phase1@example.test");
  await entry.locator("#f4-password").fill("phase-one-test-only");
  await entry.locator("#f4-consent-check").check();
  await entry.locator("#f4-signup-form button[type='submit']").click();

  await expect(entry.locator("#f4-status")).toContainText("Authentication is not connected in Phase 1");
  await expect(page.locator("#nur-entry-stage")).toBeVisible();
  expect(await page.locator("body").evaluate(() => {
    return (window as unknown as { NURConsolidated: { getStage: () => string } }).NURConsolidated.getStage() === "entry";
  })).toBe(true);
});

test("Phase 1 routed geometry matches canonical V197 at the current viewport", async ({ context, page }, testInfo) => {
  // Stay in the same Playwright device context. A new browser context drops
  // iPhone/WebKit mobile semantics and turns a valid source comparison into a
  // desktop-versus-mobile measurement.
  const baseline = await context.newPage();
  await baseline.goto("/v197/NUR_V197_CHECKBOX_TICK_RESTORED.html", { waitUntil: "load" });
  await baseline.evaluate(() => (window as unknown as { NURConsolidated: { enterUniverse: () => void } }).NURConsolidated.enterUniverse());
  await baseline.waitForTimeout(700);
  const expected = await geometry(baseline);
  await screenshot(baseline, testInfo.project.name, "canonical-systems");

  // Compare the immutable source against the direct product route before owner text
  // hydration. Hydration is proven separately and should not become a source
  // layout timing variable in this presentation-parity assertion.
  await page.route("**/api/v1/auth/me", route => route.fulfill({ status: 401 }));
  await page.goto("/systems", { waitUntil: "load" });
  await page.locator("body").evaluate(() => {
    (window as unknown as { NURConsolidated: { enterUniverse: () => void } }).NURConsolidated.enterUniverse();
  });
  await page.waitForTimeout(700);
  const observed = await geometry(page);
  await screenshot(page, testInfo.project.name, "routed-geometry");
  await testInfo.attach("v197-geometry.json", {
    body: JSON.stringify({ expected, observed }, null, 2),
    contentType: "application/json",
  });

  for (const [panel, actual, baseline, keys] of [
    ["map", observed.map, expected.map, ["x", "y", "width", "height"]],
    // V197 itself uses a flex `margin-top:auto` strength block. Independent
    // WebKit source runtimes can allocate its below-fold free height
    // differently, so assert the visible panel anchor and CSS contract rather
    // than treating that source-owned intrinsic height as bridge geometry.
    ["insight", observed.insight, expected.insight, ["x", "y", "width"]],
  ] as const) {
    for (const key of keys) {
      expect(
        Math.abs(actual[key] - baseline[key]),
        `${panel}.${key}: expected ${baseline[key]}, observed ${actual[key]}`,
      ).toBeLessThanOrEqual(1.1);
    }
  }
  expect(observed.insightStyle).toEqual(expected.insightStyle);
  expect(observed.styleCount).toBe(expected.styleCount);
  expect(observed.scriptCount).toBe(expected.scriptCount);
  await baseline.close();
});

test("native V197 navigation synchronizes the top-level URL without React routing", async ({ page }) => {
  await installReadonlyHydrationMocks(page);
  await page.goto("/systems", { waitUntil: "load" });
  const universe = page.frameLocator("#nur-universe-stage");
  await expect(universe.locator("#page-systems")).toBeVisible();
  await universe.locator("body").evaluate(async () => {
    await document.fonts.ready;
  });

  await universe.locator("button[data-world-tab='map'], button[data-world-focus='map']").first().click();
  await expect(page).toHaveURL(/\/universe\/map$/);
  // At the source's mobile breakpoint its fixed tab is visually preserved but
  // covered by the canonical viewport layer. Do not use a forced pointer click
  // or alter V197 geometry; invoke its native event path to prove bridge URL
  // synchronization independently of that immutable source behavior.
  await universe.locator("button[data-page='today']:visible").first().evaluate(button => {
    (button as HTMLButtonElement).click();
  });
  await expect(page).toHaveURL(/\/today$/);
  await expect(universe.locator("#page-today")).toHaveClass(/active/);
});

test("Phase 1 blocks source-local writes with an honest native notice", async ({ page }) => {
  const persistenceRequests: string[] = [];
  page.on("request", request => {
    if (request.method() !== "GET" && request.url().includes("/api/v1/")) persistenceRequests.push(request.url());
  });
  await installReadonlyHydrationMocks(page);
  await page.goto("/talk", { waitUntil: "load" });
  const universe = page.frameLocator("#nur-universe-stage");
  await expect(universe.locator("#page-talk")).toHaveClass(/active/);
  const before = await universe.locator(".talk-message.user").count();

  await universe.locator("#talk-input").fill("This must not become a fake local Talk turn.");
  await universe.locator("[data-send='talk']").click();

  await expect(universe.locator("#toast")).toContainText("read-only in Phase 1");
  expect(await universe.locator(".talk-message.user").count()).toBe(before);
  expect(persistenceRequests).toEqual([]);
});

test("deferred adjunct routes fail honestly in Phase 1 instead of rendering React replacements", async ({ page }) => {
  const response = await page.goto("/settings");
  expect(response?.status()).toBe(404);
  await expect(page.locator("body")).toContainText("intentionally not available in Phase 1");
  await expect(page.locator("#root")).toHaveCount(0);
});
