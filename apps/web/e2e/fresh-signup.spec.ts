import { mkdir } from "node:fs/promises";
import { join } from "node:path";

import { expect, test, type Page } from "@playwright/test";

const proofRoot = process.env.NUR_FRESH_SIGNUP_PROOF_DIR
  ?? (process.cwd().endsWith("/apps/web") ? "../../proof/fresh-signup" : "proof/fresh-signup");

async function shot(page: Page, name: string): Promise<void> {
  await mkdir(proofRoot, { recursive: true });
  await page.screenshot({ path: join(proofRoot, name), fullPage: false, animations: "disabled" });
}

/** Fresh-registration auto-entry proof — a never-used email must land inside
 * the authenticated NUR universe immediately, with the normal secure session
 * cookie, and survive a browser refresh with no second sign-in. Failure paths
 * must stay outside the universe with a readable explanation. */

async function openSignup(page: import("@playwright/test").Page) {
  await page.goto("/", { waitUntil: "load" });
  const entry = page.frameLocator("#nur-entry-stage");
  await entry.locator("body").evaluate(() => {
    (window as unknown as { nurShowFront?: () => void }).nurShowFront?.();
  });
  await entry.locator("#f4-begin").click();
  return entry;
}

async function fillSignup(
  entry: ReturnType<import("@playwright/test").Page["frameLocator"]>,
  email: string,
) {
  await entry.locator("#f4-name").fill("Fresh Star");
  await entry.locator("#f4-email").fill(email);
  await entry.locator("#f4-password").fill("fresh-orbit-pass-77");
  const consent = entry.locator("#f4-consent-check");
  if (await consent.count()) await consent.check();
}

test("fresh signup enters the authenticated universe immediately and survives refresh", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "chromium-desktop", "The registration proof runs once on desktop.");
  test.setTimeout(120_000);
  const email = `fresh-${Date.now()}-${Math.floor(Math.random() * 1e6)}@nurapp.dev`;

  const entry = await openSignup(page);
  await fillSignup(entry, email);
  const entryBrand = await entry.locator("#nur-front-v61").evaluate(root => {
    const word = root.querySelector<HTMLElement>(".f4-brand-word")?.getBoundingClientRect();
    const subtitle = root.querySelector<HTMLElement>(".f4-brand-sub")?.getBoundingClientRect();
    const stars = document.querySelector<HTMLCanvasElement>("#nur-v197-static-starfield");
    if (!word || !subtitle) throw new Error("V197 Entry brand geometry is missing.");
    return {
      wordTop: word.top,
      centerDelta: Math.abs((word.left + word.width / 2) - (subtitle.left + subtitle.width / 2)),
      wordToSubtitleGap: subtitle.top - word.bottom,
      staticStarCount: Number(stars?.dataset.nurStarCount ?? 0),
    };
  });
  expect(entryBrand.wordTop).toBeGreaterThanOrEqual(10);
  expect(entryBrand.centerDelta).toBeLessThanOrEqual(1);
  expect(entryBrand.wordToSubtitleGap).toBeGreaterThanOrEqual(0);
  expect(entryBrand.staticStarCount).toBeGreaterThanOrEqual(92);
  const registered = page.waitForResponse(response =>
    response.url().includes("/api/v1/auth/register"));
  const verifiedSession = page.waitForResponse(response =>
    response.url().includes("/api/v1/auth/me") && response.status() === 200);
  await entry.locator("#f4-signup-form button[type='submit']").click();
  const registerResponse = await registered;
  const meResponse = await verifiedSession;
  expect(registerResponse.status(), "registration must succeed").toBe(201);
  expect(meResponse.status(), "bridge must verify the new secure session").toBe(200);
  const payload = await registerResponse.json() as { id: string; email: string; orbit: { kind: string } };
  expect(payload.email).toBe(email);
  expect(payload.orbit.kind).toBe("PERSONAL_BRIDGE");
  const setCookieNames = (await registerResponse.headersArray())
    .filter(header => header.name.toLowerCase() === "set-cookie")
    .map(header => header.value.split("=", 1)[0]);
  expect(setCookieNames).toEqual(expect.arrayContaining(["nur_session", "nur_csrf"]));
  const browserCookies = await page.context().cookies();
  const sessionCookie = browserCookies.find(cookie => cookie.name === "nur_session");
  const csrfCookie = browserCookies.find(cookie => cookie.name === "nur_csrf");
  expect(sessionCookie).toMatchObject({ httpOnly: true, sameSite: "Lax" });
  expect(csrfCookie).toMatchObject({ httpOnly: false, sameSite: "Lax" });

  // Auto-entry: the authenticated shell opens with NO second sign-in.
  await expect(page.locator("#nur-universe-stage")).toHaveClass(/is-visible/, { timeout: 25_000 });
  const universe = page.frameLocator("#nur-universe-stage");
  await expect(page).toHaveURL(/\/today$/);
  await expect(universe.locator("#page-today")).toBeVisible({ timeout: 20_000 });
  await expect(universe.locator("#nur-v197-static-starfield")).toHaveAttribute("data-nur-star-count", /\d+/);

  // The normal secure session cookie authenticates the current-user endpoint.
  const me = await page.evaluate(async () => {
    const response = await fetch("/api/v1/auth/me", { credentials: "include" });
    return { status: response.status, email: response.ok ? (await response.json()).email as string : null };
  });
  expect(me.status).toBe(200);
  expect(me.email).toBe(email);
  await shot(page, "fresh-user-auto-entry.png");

  // Refresh: the session survives and re-enters without any manual login.
  // The host restores the last active page (Today), so assert that surface.
  await page.reload({ waitUntil: "load" });
  await expect(page.locator("#nur-universe-stage")).toHaveClass(/is-visible/, { timeout: 25_000 });
  await expect(page.frameLocator("#nur-universe-stage").locator("#page-today")).toBeVisible({ timeout: 20_000 });
  const meAfterReload = await page.evaluate(async () => {
    const response = await fetch("/api/v1/auth/me", { credentials: "include" });
    return response.status;
  });
  expect(meAfterReload).toBe(200);
  await shot(page, "fresh-user-session-after-refresh.png");
  await testInfo.attach("fresh-signup-network-proof.json", {
    body: JSON.stringify({
      register_status: registerResponse.status(),
      register_email_matches: payload.email === email,
      returned_user_id: Boolean(payload.id),
      session_cookie: { present: Boolean(sessionCookie), http_only: sessionCookie?.httpOnly, same_site: sessionCookie?.sameSite },
      csrf_cookie: { present: Boolean(csrfCookie), http_only: csrfCookie?.httpOnly, same_site: csrfCookie?.sameSite },
      authenticated_me_status: me.status,
      refresh_me_status: meAfterReload,
      second_manual_login_required: false,
    }, null, 2),
    contentType: "application/json",
  });
});

test("duplicate-email signup moves to real signin without faking authenticated state", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "chromium-desktop", "The registration proof runs once on desktop.");
  const entry = await openSignup(page);
  await fillSignup(entry, "owner@nur.app"); // seeded demo account always exists
  const registered = page.waitForResponse(response =>
    response.url().includes("/api/v1/auth/register"));
  await entry.locator("#f4-signup-form button[type='submit']").click();
  expect((await registered).status()).toBe(400);

  const status = entry.locator("#f4-status");
  await expect(entry.locator('[data-mode="signin"]')).toHaveClass(/active/);
  await expect(entry.locator("#f4-signin-email")).toHaveValue("owner@nur.app");
  await expect(entry.locator("#f4-signin-password")).toHaveValue("fresh-orbit-pass-77");
  await expect(status).toContainText("already has an Orbit");
  await expect(status).toHaveClass(/nur-v197-auth-error/);
  // No fake authenticated UI: the universe never opens.
  await expect(page.locator("#nur-universe-stage")).not.toHaveClass(/is-visible/);
  const me = await page.evaluate(async () => (await fetch("/api/v1/auth/me", { credentials: "include" })).status);
  expect(me).toBe(401);
});

test("existing owner can recover from signup directly into the platform", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "chromium-desktop", "The duplicate-account recovery proof runs once on desktop.");
  const entry = await openSignup(page);
  await entry.locator("#f4-name").fill("Owner");
  await entry.locator("#f4-email").fill("owner@nur.app");
  await entry.locator("#f4-password").fill("owner-demo-pass-123");
  const consent = entry.locator("#f4-consent-check");
  if (await consent.count()) await consent.check();
  await entry.locator("#f4-signup-form button[type='submit']").click();

  await expect(entry.locator('[data-mode="signin"]')).toHaveClass(/active/);
  await expect(entry.locator("#f4-signin-email")).toHaveValue("owner@nur.app");
  await entry.locator("#f4-signin-form button[type='submit']").click();
  await expect(page.locator("#nur-universe-stage")).toHaveClass(/is-visible/, { timeout: 30_000 });
  await expect(page).toHaveURL(/\/today$/);
  await expect(page.frameLocator("#nur-universe-stage").locator("#page-today")).toBeVisible({ timeout: 20_000 });
});

test("client validation keeps an incomplete signup on the form", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "chromium-desktop", "The registration proof runs once on desktop.");
  const entry = await openSignup(page);
  await entry.locator("#f4-name").fill("Fresh Star");
  await entry.locator("#f4-email").fill("not-an-email");
  await entry.locator("#f4-password").fill("fresh-orbit-pass-77");
  const requests: string[] = [];
  page.on("request", request => {
    if (request.url().includes("/api/v1/auth/register")) requests.push(request.url());
  });
  await entry.locator("#f4-signup-form button[type='submit']").click();
  await page.waitForTimeout(800);
  expect(requests, "invalid input must never reach the API").toHaveLength(0);
  await expect(entry.locator("#f4-signup-form")).toBeVisible();
  await expect(page.locator("#nur-universe-stage")).not.toHaveClass(/is-visible/);
});

test("registration 429 stays on signup with a clear retry message", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "chromium-desktop", "The rate-limit presentation proof runs once on desktop.");
  await page.route("**/api/v1/auth/register", route => route.fulfill({
    status: 429,
    contentType: "application/json",
    body: JSON.stringify({ detail: "Too many attempts. Please wait and try again." }),
  }));
  const entry = await openSignup(page);
  await fillSignup(entry, `limited-${Date.now()}@nurapp.dev`);
  await entry.locator("#f4-signup-form button[type='submit']").click();

  await expect(entry.locator("#f4-status")).toBeVisible();
  await expect(entry.locator("#f4-status")).toContainText("Too many attempts");
  await expect(entry.locator("#f4-status")).toContainText("Wait a few minutes");
  await expect(entry.locator("#f4-signup-form")).toBeVisible();
  await expect(page.locator("#nur-universe-stage")).not.toHaveClass(/is-visible/);
  await shot(page, "registration-rate-limit-visible.png");
});
