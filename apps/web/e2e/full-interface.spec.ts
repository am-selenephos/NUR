import { expect, test } from "@playwright/test";
import { installNurMocks, mockClaim } from "./helpers/nurMocks";

test.use({ serviceWorkers: "block" });

const primaryRoutes: Array<{ path: string; marker: string; absent?: RegExp }> = [
  { path: "/today", marker: "You are here" },
  { path: "/talk", marker: "Talk in a room" },
  { path: "/journal", marker: "Let the thought" },
  { path: "/plan", marker: "Make one pattern" },
  { path: "/systems", marker: "A living universe" },
  { path: "/universe", marker: "A living universe" },
  { path: "/universe/map", marker: "See the system field" },
  { path: "/universe/orbits", marker: "Your Orbits" },
  { path: "/universe/timeline", marker: "A unified ledger" },
  { path: "/universe/insights", marker: "Candidates, not commandments" },
  { path: "/universe/research", marker: "Save the question" },
  { path: "/universe/community", marker: "Think with others" },
  { path: "/universe/web-signals", marker: "Name the outside signal" },
  { path: "/universe/omega", marker: "A private evidence layer" },
  { path: "/universe/omega/review", marker: "Sensitive Claim Review" },
  { path: `/universe/omega/why-changed/${mockClaim.id}`, marker: "Why NUR changed" },
  { path: "/settings", marker: "Configure power" },
  { path: "/capsule/cap-active", marker: "Ask about this context" },
];

test("every primary route is reachable, seeded, and not staged", async ({ page }) => {
  await installNurMocks(page);

  for (const route of primaryRoutes) {
    await page.goto(route.path);
    await expect(page.getByText(route.marker).first(), `${route.path} has its real marker`).toBeVisible();
    await expect(page.locator("body"), `${route.path} has no staged-primary copy`).not.toContainText(/This lens is staged|full view arrives with its data|Phase 3 shared-system/i);
    await expect(page.locator("body"), `${route.path} has no former Glow action`).not.toContainText("Mark a Personal Glow");
  }
});

test("primary buttons perform real route or persisted-state actions", async ({ page }) => {
  const state = await installNurMocks(page);

  await page.goto("/universe/research");
  await page.getByTestId("research-question").fill("Which source verifies the route?");
  await page.getByRole("button", { name: "Save" }).click();
  await expect(page.getByText("Which source verifies the route?")).toBeVisible();
  expect(state.researchBriefs.some(row => row.question === "Which source verifies the route?")).toBe(true);

  await page.goto("/universe/community");
  await page.getByPlaceholder("What would you ask a collaborator to inspect?").fill("Check whether the capsule boundary is clear.");
  await page.getByRole("button", { name: "Save" }).click();
  await expect(page.getByText("Check whether the capsule boundary is clear.")).toBeVisible();

  await page.goto("/universe/web-signals");
  await page.getByPlaceholder("What web signal should be checked later?").fill("Search pricing evidence later.");
  await page.getByRole("button", { name: "Save" }).click();
  await expect(page.getByText("Search pricing evidence later.")).toBeVisible();

  await page.goto("/settings");
  await expect(page.getByText("AI provider status")).toBeVisible();
  await page.getByRole("button", { name: "Check metrics" }).click();
  await expect(page.locator("body")).toContainText(/metrics reachable/);
});
