import { mkdir } from "node:fs/promises";
import { dirname, join } from "node:path";
import { expect, test, type Locator, type Page, type Route } from "@playwright/test";

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
  await page.screenshot({ path, fullPage: false });
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
  await page.addInitScript(language => {
    Object.defineProperty(navigator, "language", { get: () => language });
    Object.defineProperty(navigator, "languages", { get: () => [language, "en"] });
  }, locale);
  await page.route("**/api/v1/auth/me", route => json(route, {
    ...baseUser,
    profile: { ...baseUser.profile, locale },
  }));
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

function overlaps(a: Awaited<ReturnType<typeof box>>, b: Awaited<ReturnType<typeof box>>, pad = 0) {
  return !(
    a.x + a.width + pad <= b.x ||
    b.x + b.width + pad <= a.x ||
    a.y + a.height + pad <= b.y ||
    b.y + b.height + pad <= a.y
  );
}

function assertNoOverlap(label: string, a: Awaited<ReturnType<typeof box>>, b: Awaited<ReturnType<typeof box>>, pad = 0) {
  expect(overlaps(a, b, pad), label).toBe(false);
}

async function assertNoHorizontalOverflow(page: Page) {
  const overflow = await page.evaluate(() => ({
    documentScrollWidth: document.documentElement.scrollWidth,
    documentClientWidth: document.documentElement.clientWidth,
    bodyScrollWidth: document.body.scrollWidth,
    bodyClientWidth: document.body.clientWidth,
  }));
  expect(overflow.documentScrollWidth, "document has no horizontal overflow").toBeLessThanOrEqual(overflow.documentClientWidth + 1);
  expect(overflow.bodyScrollWidth, "body has no horizontal overflow").toBeLessThanOrEqual(overflow.bodyClientWidth + 1);
}

async function assertMetricReadable(page: Page, testId: string, expected: RegExp) {
  const metric = page.getByTestId(testId);
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
  expect(fit.scrollWidth, `${testId} does not clip horizontally`).toBeLessThanOrEqual(fit.width + 3);
  expect(fit.scrollHeight, `${testId} does not clip vertically`).toBeLessThanOrEqual(fit.height + 3);
}

async function assertCaptureControlsStyled(page: Page) {
  await expect(page.getByTestId("new-decision")).toBeVisible();
  await expect(page.getByTestId("new-reference")).toBeVisible();
  for (const id of ["keep-decision", "keep-reference"]) {
    const button = page.getByTestId(id);
    await expect(button).toBeVisible();
    await expect(button).toHaveClass(/share-capture-btn/);
    const style = await button.evaluate(el => {
      const cs = getComputedStyle(el);
      return {
        backgroundColor: cs.backgroundColor,
        backgroundImage: cs.backgroundImage,
        borderRadius: cs.borderRadius,
        color: cs.color,
      };
    });
    expect(style.backgroundColor, `${id} is not native white`).not.toBe("rgb(255, 255, 255)");
    expect(style.backgroundImage, `${id} has NUR gradient styling`).not.toBe("none");
    expect(Number.parseFloat(style.borderRadius), `${id} is pill-like`).toBeGreaterThanOrEqual(16);
  }
}

async function assertBidiIsolation(page: Page) {
  const isolates = page.locator(".bidi-isolate");
  await expect(isolates.first()).toBeVisible();
  const count = await isolates.count();
  expect(count, "mixed text has bidi isolation wrappers").toBeGreaterThanOrEqual(3);
  const first = await isolates.first().evaluate(el => ({
    dir: el.getAttribute("dir"),
    unicodeBidi: getComputedStyle(el).unicodeBidi,
  }));
  expect(first.dir).toBe("auto");
  expect(first.unicodeBidi).toContain("isolate");
}

async function assertSystemsMapGeometry(page: Page, viewportLabel: string) {
  await expect(page.locator("#page-systems")).toBeVisible();
  const viewport = page.viewportSize();
  const title = await box(`${viewportLabel} map title`, page.locator(".universe-map-title"));
  const subtitle = await box(`${viewportLabel} map subtitle`, page.getByTestId("map-subtitle"));
  const master = await box(`${viewportLabel} master star`, page.getByTestId("map-master-star"));
  const add = await box(`${viewportLabel} add system`, page.getByTestId("pw-add-system"));
  const visibleNodes = page.locator(".universe-system-node:visible");
  const nodeCount = await visibleNodes.count();

  assertNoOverlap(`${viewportLabel}: System Field/title collision`, title, await maybeBox(page.getByTestId("system-field-readout")), 6);
  assertNoOverlap(`${viewportLabel}: NUR title/master star collision`, title, master, 8);
  assertNoOverlap(`${viewportLabel}: Neural subtitle/master star collision`, subtitle, master, 8);
  assertNoOverlap(`${viewportLabel}: Add System/title collision`, add, title, 8);
  assertNoOverlap(`${viewportLabel}: Add System/master star collision`, add, master, 8);

  for (let i = 0; i < nodeCount; i += 1) {
    const node = await box(`${viewportLabel} map node ${i}`, visibleNodes.nth(i));
    assertNoOverlap(`${viewportLabel}: Add System covers node label ${i}`, add, node, 4);
  }

  if (viewport?.width === 1280) {
    const quiet = await box("1280 Quiet Ambition label", page.getByTestId("map-node-quiet"));
    const embodied = await box("1280 Embodied Edge label", page.getByTestId("map-node-embodied"));
    const relational = await box("1280 Relational Gravity label", page.getByTestId("map-node-relational"));
    assertNoOverlap("1280: Quiet Ambition and Embodied Edge have horizontal air", quiet, embodied, 18);
    assertNoOverlap("1280: Quiet Ambition and Relational Gravity have diagonal air", quiet, relational, 18);
    assertNoOverlap("1280: Embodied Edge and Relational Gravity have vertical air", embodied, relational, 18);
    await expect(page.getByTestId("map-node-quiet").locator("b")).toBeVisible();
    await expect(page.getByTestId("map-node-embodied").locator("b")).toBeVisible();
    await expect(page.getByTestId("map-node-relational").locator("b")).toBeVisible();
    for (const node of [page.getByTestId("map-node-quiet"), page.getByTestId("map-node-embodied"), page.getByTestId("map-node-relational")]) {
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
    const topbar = await box("mobile top nav", page.locator(".nur-topbar"));
    expect(topbar.y, "mobile top nav is not clipped at the top").toBeGreaterThanOrEqual(0);
    expect(topbar.y + topbar.height, "mobile top nav stays inside its own opening area").toBeLessThanOrEqual(92);

    const commandRow = page.locator(".universe-command-row");
    const command = await box("mobile chips row", commandRow);
    const commandFlow = await commandRow.evaluate(el => ({
      scrollWidth: el.scrollWidth,
      clientWidth: el.clientWidth,
      overflowX: getComputedStyle(el).overflowX,
      overflowY: getComputedStyle(el).overflowY,
    }));
    expect(["auto", "scroll"], "mobile chips row is horizontally scrollable").toContain(commandFlow.overflowX);
    expect(commandFlow.overflowY, "mobile chips row does not clip vertically").not.toBe("visible");
    expect(command.height, "mobile chips row has stable hit area").toBeLessThanOrEqual(52);

    await assertMetricReadable(page, "metric-outcomes-returned", /outcomes returned/i);
    await assertMetricReadable(page, "metric-insights-evolving", /insights evolving/i);
    expect(add.y + add.height, "Add System is not a ghost control on the lower viewport edge").toBeLessThan(viewport.height - 120);
    expect(master.y, "master star appears in first mobile viewport").toBeGreaterThanOrEqual(0);
    expect(master.y + master.height, "master star is not awkwardly cut at first mobile viewport").toBeLessThanOrEqual(viewport.height - 18);
  }

  await assertNoHorizontalOverflow(page);
}

async function maybeBox(locator: Locator) {
  if (await locator.count() === 0 || !(await locator.first().isVisible())) {
    return { x: -1000, y: -1000, width: 1, height: 1 };
  }
  return box("optional system field", locator.first());
}

test("systems map has DOM anti-overlap proof at 1440, 1280, and mobile", async ({ page }) => {
  await installVisualMocks(page);

  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/systems");
  await assertSystemsMapGeometry(page, "1440x900");
  await screenshot(page, "systems-overlap-proof-1440x900.png");

  await page.setViewportSize({ width: 1280, height: 720 });
  await assertSystemsMapGeometry(page, "1280x720");
  await screenshot(page, "systems-overlap-proof-1280x720.png");
  await screenshot(page, "systems-1280-label-breathing.png");

  await page.setViewportSize({ width: 393, height: 852 });
  await assertSystemsMapGeometry(page, "393x852");
  await screenshot(page, "systems-overlap-proof-393x852.png");
  await screenshot(page, "systems-mobile-clean-393x852.png");
});

test("RTL screenshots cover Talk, Systems, Share Orbit, and Capsule", async ({ page }) => {
  await installVisualMocks(page, "ur");
  await page.setViewportSize({ width: 1280, height: 720 });

  await page.goto("/talk");
  await expect(page.locator("#page-talk")).toBeVisible();
  await assertBidiIsolation(page);
  await screenshot(page, "rtl-talk-1280x720.png");

  await page.goto("/systems");
  await expect(page.locator("#page-systems")).toBeVisible();
  await screenshot(page, "rtl-systems-1280x720.png");
  await page.getByTestId("share-orbit").click();
  const sheet = page.getByTestId("share-sheet");
  await expect(sheet).toBeVisible();
  await sheet.evaluate(el => { el.scrollTop = 0; });
  await page.getByTestId("keep-decision").scrollIntoViewIfNeeded();
  await assertCaptureControlsStyled(page);
  await sheet.evaluate(el => { el.scrollTop = 0; });
  await screenshot(page, "rtl-share-orbit-1280x720.png");
  await locatorScreenshot(sheet, "rtl-share-orbit-full-modal-top-1280x720.png");

  await page.goto("/capsule/cap-active");
  await expect(page.getByTestId("capsule-room")).toBeVisible();
  await screenshot(page, "rtl-capsule-1280x720.png");
});

test("capsule room active chamber is polished and bounded", async ({ page }) => {
  await installVisualMocks(page);
  await page.setViewportSize({ width: 1280, height: 720 });
  await page.goto("/capsule/cap-active");
  await expect(page.getByTestId("capsule-room")).toBeVisible();
  await expect(page.getByTestId("capsule-state")).toHaveText("ACTIVE");
  await expect(page.getByTestId("safety-copy")).toContainText("does not speak for");
  await screenshot(page, "capsule-room-active-top-card-readability-1280x720.png");
});

test("mobile visual evidence covers Systems, RTL Talk, and Share Orbit capture", async ({ page }, testInfo) => {
  test.skip(!["webkit-mobile", "chromium-mobile"].includes(testInfo.project.name), "mobile evidence lane only.");
  const prefix = testInfo.project.name === "webkit-mobile" ? "webkit" : "chromium";
  await installVisualMocks(page, "ur");
  await page.setViewportSize({ width: 393, height: 852 });

  await page.goto("/systems");
  await expect(page.locator("#page-systems")).toBeVisible();
  await assertSystemsMapGeometry(page, `${prefix}-393x852`);
  await screenshot(page, `systems-${prefix}-mobile-393x852.png`);

  await page.goto("/talk");
  await expect(page.locator("#page-talk")).toBeVisible();
  await assertBidiIsolation(page);
  await screenshot(page, `rtl-talk-${prefix}-mobile-393x852.png`);

  await page.goto("/systems");
  await page.getByTestId("share-orbit").scrollIntoViewIfNeeded();
  await page.getByTestId("share-orbit").click();
  const sheet = page.getByTestId("share-sheet");
  await expect(sheet).toBeVisible();
  await page.getByTestId("keep-decision").scrollIntoViewIfNeeded();
  await assertCaptureControlsStyled(page);
  await screenshot(page, `rtl-share-orbit-${prefix}-mobile-393x852.png`);
});
