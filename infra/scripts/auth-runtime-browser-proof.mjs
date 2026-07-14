import { mkdir, writeFile } from "node:fs/promises";
import { chromium } from "playwright";

const webUrl = process.env.WEB_ORIGIN || "http://localhost:5173";
const proofRoot = new URL("../../proof/auth-runtime/", import.meta.url).pathname;
await mkdir(proofRoot, { recursive: true });

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const consoleErrors = [];
page.on("console", message => {
  if (message.type() === "error") consoleErrors.push(message.text());
});

const proof = {
  browser_origin: webUrl,
  login_status: null,
  login_set_cookie_names: [],
  session_cookie_retained: false,
  csrf_cookie_retained: false,
  authenticated_me_status: null,
  final_url: null,
  today_visible: false,
  refresh_me_status: null,
  refresh_today_visible: false,
  logout_status: null,
  logout_me_status: null,
  landing_visible_after_logout: false,
  console_errors: consoleErrors,
};

function fail(message) {
  throw new Error(`AUTH_BROWSER_PROOF_FAILED: ${message}`);
}

try {
  await page.goto(webUrl, { waitUntil: "load" });
  const entry = page.frameLocator("#nur-entry-stage");
  await entry.locator("#f4-signin").waitFor({ state: "visible", timeout: 25_000 });
  await entry.locator("#f4-signin").click();
  await entry.locator("#f4-signin-email").fill("owner@nur.app");
  await entry.locator("#f4-signin-password").fill("owner-demo-pass-123");

  const loginResponsePromise = page.waitForResponse(response =>
    response.url().includes("/api/v1/auth/login"));
  const meResponsePromise = page.waitForResponse(response =>
    response.url().includes("/api/v1/auth/me") && response.status() === 200);
  await entry.locator("#f4-signin-form button[type='submit']").click();
  const loginResponse = await loginResponsePromise;
  const meResponse = await meResponsePromise;
  proof.login_status = loginResponse.status();
  proof.authenticated_me_status = meResponse.status();
  proof.login_set_cookie_names = (await loginResponse.headersArray())
    .filter(header => header.name.toLowerCase() === "set-cookie")
    .map(header => header.value.split("=", 1)[0]);

  const cookies = await page.context().cookies(webUrl);
  proof.session_cookie_retained = cookies.some(cookie => cookie.name === "nur_session" && cookie.httpOnly);
  proof.csrf_cookie_retained = cookies.some(cookie => cookie.name === "nur_csrf" && !cookie.httpOnly);
  if (proof.login_status !== 200) fail(`login HTTP ${proof.login_status}`);
  if (!proof.session_cookie_retained) fail("nur_session cookie missing");
  if (proof.authenticated_me_status !== 200) fail(`/auth/me HTTP ${proof.authenticated_me_status}`);

  await page.waitForURL(`${webUrl}/today`, { timeout: 30_000 });
  const universe = page.frameLocator("#nur-universe-stage");
  await universe.locator("#page-today").waitFor({ state: "visible", timeout: 30_000 });
  proof.final_url = page.url();
  proof.today_visible = true;
  await page.screenshot({ path: `${proofRoot}web-origin-today-authenticated.png`, animations: "disabled" });

  await page.reload({ waitUntil: "load" });
  await page.waitForURL(`${webUrl}/today`, { timeout: 30_000 });
  await page.frameLocator("#nur-universe-stage").locator("#page-today").waitFor({ state: "visible", timeout: 30_000 });
  proof.refresh_me_status = await page.evaluate(async () =>
    (await fetch("/api/v1/auth/me", { credentials: "include" })).status);
  proof.refresh_today_visible = true;
  if (proof.refresh_me_status !== 200) fail(`refresh /auth/me HTTP ${proof.refresh_me_status}`);
  await page.screenshot({ path: `${proofRoot}web-origin-refresh-authenticated.png`, animations: "disabled" });

  await page.frameLocator("#nur-universe-stage").locator(".nur-user").click();
  const logoutButton = page.frameLocator("#nur-universe-stage").locator('[data-action="auth-logout"]');
  await logoutButton.waitFor({ state: "visible", timeout: 10_000 });
  const logoutResponsePromise = page.waitForResponse(response =>
    response.url().includes("/api/v1/auth/logout"));
  await logoutButton.click();
  const logoutResponse = await logoutResponsePromise;
  proof.logout_status = logoutResponse.status();
  if (proof.logout_status !== 204) fail(`logout HTTP ${proof.logout_status}`);

  await page.waitForURL(webUrl + "/", { timeout: 20_000 });
  const landing = page.frameLocator("#nur-entry-stage");
  await landing.locator("#f4-begin").waitFor({ state: "visible", timeout: 20_000 });
  proof.logout_me_status = await page.evaluate(async () =>
    (await fetch("/api/v1/auth/me", { credentials: "include" })).status);
  proof.landing_visible_after_logout = true;
  if (proof.logout_me_status !== 401) fail(`post-logout /auth/me HTTP ${proof.logout_me_status}`);
  await page.screenshot({ path: `${proofRoot}web-origin-logout-landing.png`, animations: "disabled" });

  await writeFile(`${proofRoot}auth-runtime-proof.json`, JSON.stringify(proof, null, 2));
  process.stdout.write(`${JSON.stringify(proof)}\n`);
} finally {
  await browser.close();
}
