import { expect, test } from "@playwright/test";

// Full V197 flow: landing -> Begin your Orbit -> register (real API) ->
// onboarding direction -> authenticated interface -> logout -> guard bounce.
test("register creates an orbit and reaches Today, then logout protects routes", async ({ page }) => {
  const email = `e2e-${Date.now()}@nurapp.dev`;
  await page.goto("/");
  await page.getByTestId("tab-register").click();
  await page.locator("#f4-name").fill("Selene");
  await page.locator("#f4-email").fill(email);
  await page.locator("#f4-password").fill("orbit-pass-2025");
  await page.getByTestId("consent").check();
  await page.getByTestId("auth-submit").first().click();
  await expect(page.getByRole("heading", { name: "One honest direction." })).toBeVisible();
  await page.getByTestId("direction-my-mind").click();
  await page.getByTestId("auth-sketch-orbit").click();
  await page.getByTestId("auth-return-sky").click();

  await expect(page.getByTestId("pw-rail-today")).toBeVisible();
  await expect(page.locator("#page-today")).toBeVisible();
  await expect(page.getByText(/You are here, Selene/)).toBeVisible();

  await page.getByTestId("user-star").click();
  await page.getByTestId("logout").click();
  await expect(page.getByTestId("tab-register")).toBeVisible(); // back on landing

  await page.goto("/today");
  await expect(page.locator('[data-mode="signin"] [data-testid="auth-submit"]')).toBeVisible(); // bounced to sign-in sheet
});
