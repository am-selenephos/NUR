import { expect, test } from "@playwright/test";

test.use({ viewport: { width: 1280, height: 720 } });

// Amendment §8, in the browser: owner builds an Orbit, captures a decision,
// mints a Capsule for a named recipient, the recipient works inside the
// boundary, the owner revokes, the room closes. No force clicks anywhere.
test("capsule lifecycle across two accounts: share, scoped answer, revoke", async ({ page }) => {
  test.setTimeout(180_000);
  const stamp = Date.now();
  const ownerEmail = `owner-${stamp}@nurapp.dev`;
  const recipientEmail = `maddy-${stamp}@nurapp.dev`;
  const pw = "orbit-pass-2025";

  async function register(name: string, email: string) {
    await page.goto("/");
    await page.getByTestId("tab-register").click();
    await page.locator("#f4-name").fill(name);
    await page.locator("#f4-email").fill(email);
    await page.locator("#f4-password").fill(pw);
    await page.getByTestId("consent").check();
    await page.getByTestId("auth-submit").first().click();
    await expect(page.getByRole("heading", { name: "One honest direction." })).toBeVisible();
    await page.getByTestId("direction-my-mind").click();
    await page.getByTestId("auth-sketch-orbit").click();
    await page.getByTestId("auth-return-sky").click();
    await expect(page.locator("#page-today")).toBeVisible();
  }
  async function logout() {
    await page.getByTestId("user-star").click();
    await page.getByTestId("logout").click();
    await expect(page.getByTestId("tab-register")).toBeVisible();
  }
  async function login(email: string) {
    await page.goto("/");
    await page.getByTestId("tab-login").click();
    await page.locator("#f4-signin-email").fill(email);
    await page.locator("#f4-signin-password").fill(pw);
    await page.locator('[data-mode="signin"] [data-testid="auth-submit"]').click();
    await expect(page.locator("#page-today")).toBeVisible();
  }

  // ── owner: real orbit from a suggested sky ──
  await register("Selene", ownerEmail);
  await page.getByTestId("pw-rail-sys-quiet-ambition").click();
  await expect(page.locator("#page-systems")).toBeVisible();
  await expect(page.getByTestId("share-orbit")).toBeVisible();

  // ── share sheet: capture sources, include ONLY the decision ──
  await page.getByTestId("share-orbit").click();
  await expect(page.getByTestId("share-sheet")).toBeVisible();
  await expect(page.getByTestId("keep-decision")).toBeVisible();
  const captureStyles = await page.getByTestId("keep-decision").evaluate((el) => {
    const styles = getComputedStyle(el);
    return {
      backgroundColor: styles.backgroundColor,
      backgroundImage: styles.backgroundImage,
      borderColor: styles.borderColor,
      color: styles.color,
      fontFamily: styles.fontFamily,
    };
  });
  expect(captureStyles.backgroundColor).not.toBe("rgb(255, 255, 255)");
  expect(captureStyles.backgroundImage).toContain("linear-gradient");
  expect(captureStyles.borderColor).not.toBe("rgb(0, 0, 0)");
  expect(captureStyles.color).not.toBe("rgb(0, 0, 0)");
  expect(captureStyles.fontFamily.toLowerCase()).toContain("crimson");

  await page.getByTestId("new-decision").fill("Postgres RLS is the trust boundary");
  await page.getByTestId("new-decision").press("Enter");
  await expect(page.getByTestId("src-DECISION")).toBeVisible();
  await page.getByTestId("new-reference").fill("Capsule spectrum palette");
  await page.getByTestId("new-reference").press("Enter");
  await expect(page.getByTestId("src-REFERENCE")).toBeVisible();
  const sourceCheckStyles = await page.getByTestId("src-DECISION").evaluate((el) => {
    const styles = getComputedStyle(el);
    return {
      appearance: styles.appearance,
      backgroundColor: styles.backgroundColor,
      backgroundImage: styles.backgroundImage,
      borderColor: styles.borderColor,
    };
  });
  expect(sourceCheckStyles.appearance).not.toBe("auto");
  expect(sourceCheckStyles.backgroundColor).not.toBe("rgb(255, 255, 255)");
  expect(sourceCheckStyles.backgroundImage).toContain("linear-gradient");
  expect(sourceCheckStyles.borderColor).not.toBe("rgb(0, 0, 0)");
  await page.screenshot({
    path: process.cwd().endsWith("/apps/web")
      ? "../../proof/g5-share-sheet-repaired-v2-no-white-controls.png"
      : "proof/g5-share-sheet-repaired-v2-no-white-controls.png",
    fullPage: false,
  });
  await page.getByTestId("src-DECISION").check(); // reference stays EXCLUDED

  await page.getByTestId("cap-purpose").fill("Get a designer useful in 20 minutes");
  await page.getByTestId("cap-email").fill(recipientEmail);
  await page.getByTestId("create-capsule").click();
  const card = page.getByTestId("capsule-created");
  await expect(card).toBeVisible();
  const capsuleId = (await card.innerText()).match(/capsule\/([0-9a-f-]{36})/)![1];
  await page.keyboard.press("Escape");
  await logout();

  // ── recipient: the room, the boundary, the scoped answer ──
  await register("Maddy", recipientEmail);
  await page.goto(`/capsule/${capsuleId}`);
  await expect(page.getByTestId("capsule-room")).toBeVisible();
  await expect(page.getByTestId("capsule-state")).toHaveText("ACTIVE");
  await expect(page.getByTestId("safety-copy")).toContainText("does not speak for");
  await expect(page.getByTestId("excluded-row")).toContainText("reference"); // withheld, visible as a boundary
  await page.getByTestId("capsule-question").fill("What did you decide about Postgres RLS as the trust boundary?");
  await page.getByTestId("capsule-ask").click();
  await expect(page.getByTestId("capsule-answer").first()).toContainText("trust boundary");
  await expect(page.getByTestId("answer-mode").first()).toContainText("Direct statement");
  await page.goto("/today");
  await expect(page.locator("#page-today")).toBeVisible();
  await logout();

  // ── owner revokes ──
  await login(ownerEmail);
  await page.getByTestId("pw-rail-sys-quiet-ambition").click();
  await expect(page.getByTestId("share-orbit")).toBeVisible();
  await page.getByTestId("share-orbit").click();
  await page.getByTestId(`revoke-${capsuleId}`).click();
  await expect(page.getByTestId(`revoke-${capsuleId}`)).toHaveCount(0); // revoked rows lose the button
  await page.keyboard.press("Escape");
  await logout();

  // ── recipient refresh: the distinct closed state ──
  await login(recipientEmail);
  await page.goto(`/capsule/${capsuleId}`);
  await expect(page.getByTestId("capsule-state")).toHaveText("REVOKED");
  await expect(page.getByTestId("inactive-note")).toBeVisible();
  await expect(page.getByTestId("capsule-question")).toHaveCount(0);
});
