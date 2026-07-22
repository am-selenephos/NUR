import { expect, test, type BrowserContext, type FrameLocator, type Page } from "@playwright/test";

/** Amendment §8 against the live V197 surface: the owner mints a Capsule that
 * includes ONLY an approved Decision (a Reference stays withheld), the named
 * recipient works inside the boundary and receives a source-bound answer, the
 * owner revokes, and the room closes with a distinct terminal state. Two real
 * accounts, real API, no force clicks.
 *
 * The React share sheet was retired with the frontend forensic rebuild; the
 * owner's source selection is exercised through the same owner-scoped API the
 * product uses, and every visible step runs through exact V197 controls. */

async function signIn(page: Page, email: string, password: string): Promise<FrameLocator> {
  await page.goto("/", { waitUntil: "load" });
  const entry = page.frameLocator("#nur-entry-stage");
  await entry.locator("body").evaluate(() => {
    (window as unknown as { nurShowFront?: () => void }).nurShowFront?.();
  });
  await entry.locator("#f4-signin").click();
  await entry.locator("#f4-signin-email").fill(email);
  await entry.locator("#f4-signin-password").fill(password);
  await entry.locator("#f4-signin-form button[type='submit']").click();
  await expect(page.locator("#nur-universe-stage")).toHaveClass(/is-visible/, { timeout: 20_000 });
  const universe = page.frameLocator("#nur-universe-stage");
  await expect(universe.locator("#page-today")).toBeVisible({ timeout: 20_000 });
  return universe;
}

test("capsule lifecycle across two accounts: share, scoped answer, revoke", async ({ browser }) => {
  test.setTimeout(180_000);
  const stamp = Date.now();

  const ownerContext: BrowserContext = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  const recipientContext: BrowserContext = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  const ownerPage = await ownerContext.newPage();
  const recipientPage = await recipientContext.newPage();

  // ── owner: real session through the exact V197 entry ──
  await signIn(ownerPage, "owner@nur.app", "owner-demo-pass-123");

  // ── owner: approve one Decision, withhold one Reference, mint the grant ──
  // (the persisted-source boundary itself — driven through the same
  // owner-scoped, CSRF-protected API the product uses)
  const minted = await ownerPage.evaluate(async (nonce) => {
    const csrf = decodeURIComponent(
      document.cookie.split("; ").find(row => row.startsWith("nur_csrf="))?.split("=")[1] ?? "");
    const call = async (path: string, body: Record<string, unknown>) => {
      const response = await fetch(`/api/v1${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
        credentials: "include",
        body: JSON.stringify(body),
      });
      if (!response.ok) throw new Error(`${path} -> ${response.status}: ${await response.text()}`);
      return response.json();
    };
    const me = await (await fetch("/api/v1/auth/me", { credentials: "include" })).json();
    const orbitId = me.orbit?.id ?? me.profile?.active_orbit_id;
    if (!orbitId) throw new Error("Owner session has no orbit.");

    const decision = await call(`/orbits/${orbitId}/decisions`, {
      statement: `Postgres RLS is the trust boundary (${nonce}).`,
      rationale: "Browser lifecycle proof decision.",
    });
    const reference = await call(`/orbits/${orbitId}/references`, {
      title: `Withheld palette reference ${nonce}`,
      body: "Capsule spectrum palette. This reference must never reach the recipient.",
      kind: "REFERENCE",
    });
    const decisionSource = await call(`/orbits/${orbitId}/sources`, {
      source_kind: "DECISION", source_id: decision.id,
    });
    await call(`/orbits/${orbitId}/sources`, {
      source_kind: "REFERENCE", source_id: reference.id,
    });
    const capsule = await call(`/orbits/${orbitId}/capsules`, {
      title: `Lifecycle proof capsule ${nonce}`,
      purpose: "Show the recipient sees approved context only.",
      capability: "ASK_SCOPED_QUESTIONS",
      orbit_source_ids: [decisionSource.id],
      representations: { [decisionSource.id]: "FULL" },
    });
    await call(`/capsules/${capsule.id}/grants`, {
      recipient_email: "recipient@nur.app",
      capability: "ASK_SCOPED_QUESTIONS",
    });
    return { capsuleId: capsule.id as string };
  }, stamp);

  // ── owner: the lifecycle room shows ACTIVE state and a live revoke control ──
  const ownerUniverse = ownerPage.frameLocator("#nur-universe-stage");
  await ownerPage.goto(`/capsule/${minted.capsuleId}`, { waitUntil: "load" });
  const ownerRoot = ownerUniverse.locator("#nur-v197-adjunct-root");
  await expect(ownerRoot).toContainText("Owner capsule", { timeout: 20_000 });
  await expect(ownerRoot).toContainText("ACTIVE");
  await expect(ownerRoot.locator('[data-adjunct-action="capsule-revoke"]')).toBeEnabled();

  // ── recipient: the room, the boundary, the scoped answer ──
  await signIn(recipientPage, "recipient@nur.app", "recipient-demo-pass-123");
  const recipientUniverse = recipientPage.frameLocator("#nur-universe-stage");
  await recipientPage.goto(`/capsule/${minted.capsuleId}`, { waitUntil: "load" });
  const room = recipientUniverse.locator("#nur-v197-adjunct-root");
  await expect(room).toContainText("ACTIVE", { timeout: 20_000 });
  await expect(room).toContainText("Show the recipient sees approved context only.");
  await expect(room).toContainText(`Postgres RLS is the trust boundary (${stamp}).`); // included, FULL
  await expect(room).toContainText(/withheld/i); // the excluded reference stays a visible boundary
  await expect(room).not.toContainText("Capsule spectrum palette"); // withheld body never leaks

  const answered = recipientPage.waitForResponse(response =>
    response.url().includes("/questions") && response.status() === 201);
  await room.locator('[data-adjunct-control="capsule-question"]').fill("What did you decide about the trust boundary?");
  await room.locator('[data-adjunct-action="capsule-ask"]').click();
  await answered;
  await expect(room.locator(".nur-adjunct-answer blockquote")).toContainText(/trust boundary/i);
  await expect(room.locator(".nur-adjunct-answer .nur-adjunct-eyebrow")).toContainText("source-bound");

  // ── owner revokes through the exact V197 control ──
  const revoked = ownerPage.waitForResponse(response =>
    response.url().includes("/revoke") && response.status() < 300);
  await ownerRoot.locator('[data-adjunct-action="capsule-revoke"]').click();
  await revoked;
  await expect(ownerRoot).toContainText("Revoked. Recipient reads and asks are blocked immediately.");

  // ── recipient refresh: the distinct closed state, no question interface ──
  await recipientPage.reload({ waitUntil: "load" });
  const closedRoom = recipientPage.frameLocator("#nur-universe-stage").locator("#nur-v197-adjunct-root");
  await expect(closedRoom).toContainText("REVOKED", { timeout: 20_000 });
  await expect(closedRoom).toContainText("Access is closed");
  await expect(closedRoom.locator('[data-adjunct-control="capsule-question"]')).toHaveCount(0);

  await ownerContext.close();
  await recipientContext.close();
});
