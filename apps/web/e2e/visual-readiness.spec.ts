import { mkdir } from "node:fs/promises";
import { dirname, join } from "node:path";
import { expect, test, type FrameLocator, type Locator, type Page, type Route } from "@playwright/test";

const now = new Date().toISOString();
const baseUser = {
  id: "11111111-1111-1111-1111-111111111111",
  email: "selene@nurapp.dev",
  email_verified: true,
  profile: { chosen_name: "Selene", timezone: null, locale: "en", sound_enabled: false, reduced_effects: true },
  orbit: { id: "99999999-9999-9999-9999-999999999999", current_arrival_state: null, active_focus_area: null },
};
const orbit = {
  id: "22222222-2222-2222-2222-222222222222",
  title: "Quiet Ambition",
  kind: "PROJECT",
  description: "Build without noise",
  status: "ACTIVE",
  created_at: now,
};
const decision = {
  id: "decision-1",
  orbit_id: orbit.id,
  statement: "Postgres RLS is the trust boundary.",
  rationale: "Recipient access must stay grant-scoped.",
  created_at: now,
};
const reference = {
  id: "reference-1",
  orbit_id: orbit.id,
  title: "Capsule spectrum palette",
  body: "Mango 26E through pearl FFF2D3.",
  created_at: now,
};
const source = {
  id: "source-decision-1",
  orbit_id: orbit.id,
  source_kind: "DECISION",
  source_id: decision.id,
  created_at: now,
};

function proofPath(name: string) {
  const configured = process.env.NUR_PROOF_DIR;
  return join(configured ?? (process.cwd().endsWith("/apps/web") ? "../../proof/100-delta" : "proof/100-delta"), name);
}

async function screenshot(page: Page, name: string) {
  const path = proofPath(name);
  await mkdir(dirname(path), { recursive: true });
  await page.screenshot({ path, fullPage: false, animations: "disabled" });
}

async function locatorScreenshot(locator: Locator, name: string) {
  const path = proofPath(name);
  await mkdir(dirname(path), { recursive: true });
  await locator.screenshot({ path, animations: "disabled" });
}

async function json(route: Route, body: unknown, status = 200) {
  await route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
}

async function installVisualMocks(page: Page, locale = "en") {
  await page.context().addCookies([{
    name: "nur_csrf",
    value: "visual-readiness-csrf",
    url: "http://localhost:4173",
    httpOnly: false,
    sameSite: "Lax",
  }]);
  await page.addInitScript(language => {
    Object.defineProperty(navigator, "language", { get: () => language });
    Object.defineProperty(navigator, "languages", { get: () => [language, "en"] });
  }, locale);
  await page.route("**/api/v1/auth/me", route => json(route, {
    ...baseUser,
    profile: { ...baseUser.profile, locale },
  }));
  await page.route("**/api/v1/profile/preferences", route => json(route, {
    locale,
    sound_enabled: false,
    reduced_effects: true,
    default_boundary: "PRIVATE_ORBIT",
    active_orbit_id: orbit.id,
    omega_enabled: true,
    writing_preference: "default",
    timezone: "UTC",
  }));
  await page.route("**/healthz", route => json(route, { status: "ok" }));
  await page.route("**/api/v1/universe/live", route => json(route, null));
  await page.route("**/api/v1/universe/map-summary", route => json(route, null));
  await page.route("**/api/v1/universe/orbits-summary", route => json(route, null));
  await page.route("**/api/v1/universe/timeline", route => json(route, null));
  await page.route("**/api/v1/universe/insights-summary", route => json(route, null));
  await page.route("**/api/v1/map", route => json(route, null));
  await page.route("**/api/v1/glow/scoreboard", route => json(route, null));
  await page.route("**/api/v1/glow/summary", route => json(route, {
    balance: 0,
    lifetime_points: 0,
    today_points: 0,
    weekly_points: 0,
    level: 1,
    rank: "Orbit Seed",
    next_unlock: null,
    recent_transactions: [],
    streaks: [],
    achievements: [],
    daily_quest: {},
    weekly_mission: {},
  }));
  await page.route("**/api/v1/research/briefs", route => json(route, []));
  await page.route("**/api/v1/projects/summary", route => json(route, null));
  await page.route("**/api/v1/community/rooms", route => json(route, []));
  await page.route("**/api/v1/orbits/current-state", route => json(route, {
    active_systems: 1,
    outcomes_returned: 2,
    insights_evolving: 3,
    open_questions: 1,
    research_staged: 1,
    plans_active: 1,
    live_status: "owner_ledger",
  }));
  await page.route("**/api/v1/orbits", route => json(route, [orbit]));
  await page.route(`**/api/v1/orbits/${orbit.id}/decisions`, route => json(route, [decision]));
  await page.route(`**/api/v1/orbits/${orbit.id}/references`, route => json(route, [reference]));
  await page.route(`**/api/v1/orbits/${orbit.id}/sources`, route => json(route, [source]));
  await page.route("**/api/v1/capsules", route => json(route, [{
    id: "cap-existing",
    orbit_id: orbit.id,
    title: "Quiet Ambition shared context",
    purpose: "Get a designer useful in 20 minutes",
    capability: "ASK_SCOPED_QUESTIONS",
    expires_at: null,
    revoked_at: null,
    created_at: now,
  }]));
  await page.route("**/api/v1/journal", route => json(route, []));
  await page.route("**/api/v1/plans", route => json(route, []));
  await page.route("**/api/v1/research-drafts", route => json(route, [{
    id: "research-1",
    question: "What signal belongs here?",
    status: "STAGED",
    created_at: now,
  }]));
  await page.route("**/api/v1/cognition/talk-thread**", route => json(route, []));
  await page.route("**/api/v1/capsules/cap-active/view", route => json(route, {
    capsule_id: "cap-active",
    state: "ACTIVE",
    title: "Quiet Ambition",
    purpose: "Get a designer useful in 20 minutes",
    owner_display: "Selene",
    capability: "ASK_SCOPED_QUESTIONS",
    expires_at: null,
    recipient_instructions: "Stay inside the approved boundary.",
    safety_copy: "This does not speak for Selene. It answers only from approved context.",
    included: [{
      source_id: "decision-1",
      source_kind: "DECISION",
      representation: "FULL",
      title: "Postgres RLS is the trust boundary.",
      body: "Recipient access must stay grant-scoped.",
    }],
    excluded_summary: [{ source_kind: "REFERENCE", count: 1, note: "withheld by the owner" }],
    grant_id: "grant-1",
  }));
}

async function box(name: string, locator: Locator) {
  await expect(locator, `${name} is visible`).toBeVisible();
  const value = await locator.boundingBox();
  expect(value, `${name} has a DOM box`).not.toBeNull();
  return value!;
}

async function canvasContentBox(name: string, locator: Locator) {
  await expect(locator, `${name} canvas is visible`).toBeVisible();
  let value: { x: number; y: number; width: number; height: number } | null = null;
  await expect.poll(async () => {
    value = await locator.evaluate((element: HTMLCanvasElement) => {
      const context = element.getContext("2d");
      if (!context || element.width < 2 || element.height < 2) return null;
      const pixels = context.getImageData(0, 0, element.width, element.height).data;
      const columns = new Uint32Array(element.width);
      const rows = new Uint32Array(element.height);
      let lit = 0;
      for (let y = 0; y < element.height; y += 1) {
        for (let x = 0; x < element.width; x += 1) {
          const index = (y * element.width + x) * 4;
          const alpha = pixels[index + 3] ?? 0;
          const brightness = (pixels[index] ?? 0) + (pixels[index + 1] ?? 0) + (pixels[index + 2] ?? 0);
          if (alpha <= 20 || brightness <= 120) continue;
          columns[x] += 1;
          rows[y] += 1;
          lit += 1;
        }
      }
      if (lit < 70) return null;
      const quantile = (counts: Uint32Array, fraction: number) => {
        const target = lit * fraction;
        let seen = 0;
        for (let index = 0; index < counts.length; index += 1) {
          seen += counts[index];
          if (seen >= target) return index;
        }
        return counts.length - 1;
      };
      const left = quantile(columns, .01);
      const right = quantile(columns, .99);
      const top = quantile(rows, .01);
      const bottom = quantile(rows, .99);
      const canvas = element.getBoundingClientRect();
      const scaleX = canvas.width / element.width;
      const scaleY = canvas.height / element.height;
      return {
        x: canvas.left + left * scaleX,
        y: canvas.top + top * scaleY,
        width: Math.max(scaleX, (right - left + 1) * scaleX),
        height: Math.max(scaleY, (bottom - top + 1) * scaleY),
      };
    });
    return value;
  }, { message: `${name} has a lit pixel envelope` }).not.toBeNull();
  return value!;
}

function universeFrame(page: Page): FrameLocator {
  return page.frameLocator("#nur-universe-stage");
}

function overlaps(a: Awaited<ReturnType<typeof box>>, b: Awaited<ReturnType<typeof box>>, pad = 0) {
  return !(
    a.x + a.width + pad <= b.x ||
    b.x + b.width + pad <= a.x ||
    a.y + a.height + pad <= b.y ||
    b.y + b.height + pad <= a.y
  );
}

function assertNoOverlap(label: string, a: Awaited<ReturnType<typeof box>>, b: Awaited<ReturnType<typeof box>>, pad = 0) {
  expect(overlaps(a, b, pad), `${label}: ${JSON.stringify({ a, b, pad })}`).toBe(false);
}

async function assertNoHorizontalOverflow(frame: FrameLocator) {
  const overflow = await frame.locator("html").evaluate(() => ({
    documentScrollWidth: document.documentElement.scrollWidth,
    documentClientWidth: document.documentElement.clientWidth,
    bodyScrollWidth: document.body.scrollWidth,
    bodyClientWidth: document.body.clientWidth,
  }));
  expect(overflow.documentScrollWidth, "document has no horizontal overflow").toBeLessThanOrEqual(overflow.documentClientWidth + 1);
  expect(overflow.bodyScrollWidth, "body has no horizontal overflow").toBeLessThanOrEqual(overflow.bodyClientWidth + 1);
}

async function assertMetricReadable(metric: Locator, label: string, expected: RegExp) {
  await expect(metric).toBeVisible();
  await expect(metric).toContainText(expected);
  const fit = await metric.evaluate(el => {
    const rect = el.getBoundingClientRect();
    return {
      text: el.textContent ?? "",
      width: rect.width,
      scrollWidth: el.scrollWidth,
      height: rect.height,
      scrollHeight: el.scrollHeight,
      whiteSpace: getComputedStyle(el).whiteSpace,
    };
  });
  expect(fit.text).not.toMatch(/ev\.\.\.|insights ev\.\.\./i);
  expect(fit.scrollWidth, `${label} does not clip horizontally`).toBeLessThanOrEqual(fit.width + 3);
  expect(fit.scrollHeight, `${label} does not clip vertically`).toBeLessThanOrEqual(fit.height + 3);
}

async function assertBoundaryControlsStyled(frame: FrameLocator) {
  const modal = frame.locator("#scope-modal .scope-modal");
  await expect(modal).toBeVisible();
  const modalStyle = await modal.evaluate(el => ({
    backgroundColor: getComputedStyle(el).backgroundColor,
    backgroundImage: getComputedStyle(el).backgroundImage,
    borderRadius: getComputedStyle(el).borderRadius,
  }));
  expect(modalStyle.backgroundColor, "boundary modal is not native white").not.toBe("rgb(255, 255, 255)");
  expect(modalStyle.backgroundImage, "boundary modal has NUR material styling").not.toBe("none");
  expect(Number.parseFloat(modalStyle.borderRadius), "boundary modal keeps the approved V197 radius").toBe(8);

  const allControls = frame.locator("#scope-modal .scope-option");
  await expect(allControls).toHaveCount(7);
  const boundaryOptions = frame.locator("#scope-modal .scope-option[data-scope]");
  await expect(boundaryOptions).toHaveCount(4);
  for (let index = 0; index < 4; index += 1) {
    const button = boundaryOptions.nth(index);
    await expect(button).toBeVisible();
    const style = await button.evaluate(el => {
      const cs = getComputedStyle(el);
      return {
        backgroundColor: cs.backgroundColor,
        borderRadius: cs.borderRadius,
        color: cs.color,
      };
    });
    expect(style.backgroundColor, `boundary option ${index} is not native white`).not.toBe("rgb(255, 255, 255)");
    expect(Number.parseFloat(style.borderRadius), `boundary option ${index} has softened edges`).toBeGreaterThanOrEqual(8);
  }

  const languageControls = frame.locator("#nur-v197-locale, #nur-v197-writing-preference, #nur-v197-language-save");
  await expect(languageControls).toHaveCount(3);
  for (let index = 0; index < 3; index += 1) {
    const control = languageControls.nth(index);
    await expect(control).toBeVisible();
    await expect(control, `language control ${index} is not native white`).not.toHaveCSS("background-color", "rgb(255, 255, 255)");
  }
}

async function assertRtlDirection(frame: FrameLocator) {
  const root = frame.locator("html");
  await expect(root).toHaveAttribute("lang", "ur");
  await expect(root).toHaveAttribute("dir", "rtl");
  const direction = await root.evaluate(el => ({
    direction: getComputedStyle(el).direction,
    writingPreference: document.body.dataset.nurWritingPreference,
  }));
  expect(direction.direction).toBe("rtl");
  expect(direction.writingPreference).toBe("default");
}

async function assertSystemsMapGeometry(page: Page, viewportLabel: string) {
  const frame = universeFrame(page);
  await expect(frame.locator("#page-systems")).toBeVisible();
  const viewport = page.viewportSize();
  const title = await box(`${viewportLabel} NUR wordmark`, frame.locator(".universe-map-title .nur-v197-stable-wordmark"));
  const subtitle = await box(`${viewportLabel} map subtitle`, frame.locator(".universe-map-title small"));
  await expect(frame.locator(".universe-master-star")).toBeVisible();
  const brain = frame.locator(".universe-master-star > #front-nur-star");
  await expect(brain).toBeVisible();
  const master = await canvasContentBox(`${viewportLabel} master star`, brain.locator("#nur-brain-canvas"));
  const addControl = frame.locator(".universe-add-system");
  const addIsVisible = await addControl.isVisible();
  const add = addIsVisible
    ? await box(`${viewportLabel} add system`, addControl)
    : { x: -1000, y: -1000, width: 1, height: 1 };
  const visibleNodes = frame.locator(".universe-system-node:visible");
  const nodeCount = await visibleNodes.count();

  assertNoOverlap(`${viewportLabel}: System Field/title collision`, title, await maybeBox(frame.locator(".universe-field-readout")), 6);
  assertNoOverlap(`${viewportLabel}: NUR title/master star collision`, title, master);
  assertNoOverlap(`${viewportLabel}: Neural subtitle/master star collision`, subtitle, master);
  assertNoOverlap(`${viewportLabel}: Add System/title collision`, add, title, 8);
  assertNoOverlap(`${viewportLabel}: Add System/master star collision`, add, master, 8);

  for (let i = 0; i < nodeCount; i += 1) {
    const node = await box(`${viewportLabel} map node ${i}`, visibleNodes.nth(i));
    assertNoOverlap(`${viewportLabel}: Add System covers node label ${i}`, add, node, 4);
  }

  if (viewport?.width === 1280) {
    const quiet = await box("1280 Quiet Ambition label", frame.locator(".universe-system-node.quiet"));
    const embodied = await box("1280 Embodied Edge label", frame.locator(".universe-system-node.embodied"));
    const relational = await box("1280 Relational Gravity label", frame.locator(".universe-system-node.relational"));
    assertNoOverlap("1280: Quiet Ambition and Embodied Edge have horizontal air", quiet, embodied, 18);
    assertNoOverlap("1280: Quiet Ambition and Relational Gravity have diagonal air", quiet, relational, 18);
    assertNoOverlap("1280: Embodied Edge and Relational Gravity have vertical air", embodied, relational, 18);
    await expect(frame.locator(".universe-system-node.quiet b")).toBeVisible();
    await expect(frame.locator(".universe-system-node.embodied b")).toBeVisible();
    await expect(frame.locator(".universe-system-node.relational b")).toBeVisible();
    for (const node of [
      frame.locator(".universe-system-node.quiet"),
      frame.locator(".universe-system-node.embodied"),
      frame.locator(".universe-system-node.relational"),
    ]) {
      const fit = await node.evaluate(el => ({
        width: el.clientWidth,
        scrollWidth: el.scrollWidth,
        height: el.clientHeight,
        scrollHeight: el.scrollHeight,
      }));
      expect(fit.scrollWidth, "1280 selected label text does not clip horizontally").toBeLessThanOrEqual(fit.width + 2);
      expect(fit.scrollHeight, "1280 selected label text does not clip vertically").toBeLessThanOrEqual(fit.height + 2);
    }
  }

  if (viewport && viewport.width <= 620) {
    const topbar = await box("mobile top nav", frame.locator(".nur-topbar"));
    expect(topbar.y, "mobile top nav is not clipped at the top").toBeGreaterThanOrEqual(0);
    expect(topbar.y + topbar.height, "mobile top nav stays inside its own opening area").toBeLessThanOrEqual(92);

    const commandRow = frame.locator(".universe-command-row");
    const command = await box("mobile chips row", commandRow);
    const commandFlow = await commandRow.evaluate(el => ({
      display: getComputedStyle(el).display,
      gridTemplateColumns: getComputedStyle(el).gridTemplateColumns,
      scrollWidth: el.scrollWidth,
      clientWidth: el.clientWidth,
      scrollHeight: el.scrollHeight,
      clientHeight: el.clientHeight,
      controls: [...el.querySelectorAll<HTMLElement>(".world-command")].map(control => {
        const row = el.getBoundingClientRect();
        const rect = control.getBoundingClientRect();
        return {
          inside: rect.left >= row.left - 1 && rect.right <= row.right + 1,
          height: rect.height,
        };
      }),
    }));
    expect(commandFlow.display, "mobile commands use the approved wrapped grid").toBe("grid");
    expect(commandFlow.gridTemplateColumns.split(" ")).toHaveLength(2);
    expect(commandFlow.scrollWidth, "mobile commands do not clip horizontally").toBeLessThanOrEqual(commandFlow.clientWidth + 1);
    expect(commandFlow.scrollHeight, "mobile commands do not clip vertically").toBeLessThanOrEqual(commandFlow.clientHeight + 1);
    expect(commandFlow.controls).toHaveLength(5);
    expect(commandFlow.controls.every(control => control.inside), "all mobile commands stay inside their grid").toBe(true);
    expect(Math.min(...commandFlow.controls.map(control => control.height)), "mobile commands keep a 44px hit height").toBeGreaterThanOrEqual(44);
    expect(command.height, "mobile command grid has a visible layout box").toBeGreaterThanOrEqual(44);

    const metrics = frame.locator(".universe-hero-stats > span");
    await assertMetricReadable(metrics.nth(1), "outcomes returned metric", /outcomes returned/i);
    await assertMetricReadable(metrics.nth(2), "insights evolving metric", /insights evolving/i);
    await expect(addControl, "mobile intentionally removes the desktop-only Add System control").toBeHidden();
    const mapPanel = await box("mobile systems map", frame.locator(".universe-map-panel"));
    expect(master.y, "master star begins inside the mobile map").toBeGreaterThanOrEqual(mapPanel.y - 1);
    expect(master.y + master.height, "master star is not cut by the mobile map").toBeLessThanOrEqual(mapPanel.y + mapPanel.height + 1);
  }

  await assertNoHorizontalOverflow(frame);
}

async function maybeBox(locator: Locator) {
  if (await locator.count() === 0 || !(await locator.first().isVisible())) {
    return { x: -1000, y: -1000, width: 1, height: 1 };
  }
  return box("optional system field", locator.first());
}

test("systems map has DOM anti-overlap proof at 1440, 1280, and mobile", async ({ page }, testInfo) => {
  await installVisualMocks(page);

  if (testInfo.project.name.endsWith("-mobile")) {
    await page.setViewportSize({ width: 393, height: 852 });
    await page.goto("/systems");
    await assertSystemsMapGeometry(page, "393x852");
    await screenshot(page, "systems-overlap-proof-393x852.png");
    await screenshot(page, "systems-mobile-clean-393x852.png");
    return;
  }

  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/systems");
  await assertSystemsMapGeometry(page, "1440x900");
  await screenshot(page, "systems-overlap-proof-1440x900.png");

  await page.setViewportSize({ width: 1280, height: 720 });
  await assertSystemsMapGeometry(page, "1280x720");
  await screenshot(page, "systems-overlap-proof-1280x720.png");
  await screenshot(page, "systems-1280-label-breathing.png");
});

test("RTL screenshots cover Talk, Systems, Share Orbit, and Capsule", async ({ page }, testInfo) => {
  await installVisualMocks(page, "ur");
  const mobileProject = testInfo.project.name.endsWith("-mobile");
  const viewport = mobileProject ? { width: 393, height: 852 } : { width: 1280, height: 720 };
  const suffix = mobileProject ? "mobile-393x852" : "1280x720";
  await page.setViewportSize(viewport);
  const frame = universeFrame(page);

  await page.goto("/talk");
  await expect(frame.locator("#page-talk")).toBeVisible();
  await assertRtlDirection(frame);
  await screenshot(page, `rtl-talk-${suffix}.png`);

  await page.goto("/systems");
  await expect(frame.locator("#page-systems")).toBeVisible();
  await screenshot(page, `rtl-systems-${suffix}.png`);
  await frame.locator("#scope-open").click();
  const sheet = frame.locator("#scope-modal .scope-modal");
  await expect(sheet).toBeVisible();
  await sheet.evaluate(el => { el.scrollTop = 0; });
  await assertBoundaryControlsStyled(frame);
  await sheet.evaluate(el => { el.scrollTop = 0; });
  await screenshot(page, `rtl-share-orbit-${suffix}.png`);
  await locatorScreenshot(sheet, `rtl-share-orbit-full-modal-top-${suffix}.png`);

  await page.goto("/capsule/cap-active");
  await expect(frame.locator("#nur-v197-adjunct-root")).toBeVisible();
  await screenshot(page, `rtl-capsule-${suffix}.png`);
});

test("capsule room active chamber is polished and bounded", async ({ page }) => {
  await installVisualMocks(page);
  await page.setViewportSize({ width: 1280, height: 720 });
  await page.goto("/capsule/cap-active");
  const frame = universeFrame(page);
  const capsule = frame.locator("#nur-v197-adjunct-root");
  await expect(capsule).toBeVisible();
  await expect(capsule.locator(".nur-adjunct-fact").filter({ hasText: "State" }).locator("strong")).toHaveText("ACTIVE");
  await expect(capsule.locator(".nur-adjunct-boundary")).toContainText("does not speak for");
  await screenshot(page, "capsule-room-active-top-card-readability-1280x720.png");
});

test("mobile visual evidence covers Systems, RTL Talk, and Share Orbit capture", async ({ page }, testInfo) => {
  test.skip(!["webkit-mobile", "chromium-mobile"].includes(testInfo.project.name), "mobile evidence lane only.");
  const prefix = testInfo.project.name === "webkit-mobile" ? "webkit" : "chromium";
  await installVisualMocks(page, "ur");
  await page.setViewportSize({ width: 393, height: 852 });
  const frame = universeFrame(page);

  await page.goto("/systems");
  await expect(frame.locator("#page-systems")).toBeVisible();
  await assertSystemsMapGeometry(page, `${prefix}-393x852`);
  await screenshot(page, `systems-${prefix}-mobile-393x852.png`);

  await page.goto("/talk");
  await expect(frame.locator("#page-talk")).toBeVisible();
  await assertRtlDirection(frame);
  await screenshot(page, `rtl-talk-${prefix}-mobile-393x852.png`);

  await page.goto("/systems");
  await frame.locator("#scope-open").click();
  const sheet = frame.locator("#scope-modal .scope-modal");
  await expect(sheet).toBeVisible();
  await assertBoundaryControlsStyled(frame);
  await screenshot(page, `rtl-share-orbit-${prefix}-mobile-393x852.png`);
});
