import { expect, test } from "@playwright/test";
import { installNurMocks } from "./helpers/nurMocks";

test.use({ serviceWorkers: "block" });

test("Talk persists user and NUR turns through API reload", async ({ page }) => {
  await installNurMocks(page);
  await page.goto("/talk");
  await expect(page.getByText("Persist this already.")).toBeVisible();
  await expect(page.getByText("Persisted answer.")).toBeVisible();

  await page.locator("#talk-input").fill("Persist this new line too.");
  await page.getByRole("button", { name: "Send to NUR" }).click();
  await expect(page.getByText("I saved this turn, but live AI is disabled on this server.")).toBeVisible();
  await expect(page.getByTestId("talk-omega-holding").first()).toBeVisible();

  await page.reload();
  await expect(page.getByText("Persist this already.")).toBeVisible();
  await expect(page.getByText("Persist this new line too.")).toBeVisible();
  await expect(page.getByText("I saved this turn, but live AI is disabled on this server.")).toBeVisible();
});

test("former Glow control cannot increment without a persisted outcome", async ({ page }) => {
  const state = await installNurMocks(page);
  await page.goto("/talk");
  await expect(page.getByText("Mark a Personal Glow")).toHaveCount(0);

  const before = state.outcomePosts;
  await page.getByTestId("talk-record-outcome").click();
  await expect(page.getByTestId("talk-outcome-form")).toBeVisible();
  expect(state.outcomePosts).toBe(before);

  await page.getByTestId("talk-outcome-input").fill("The owner returned the outcome.");
  await page.getByTestId("talk-submit-outcome").click();
  await expect.poll(() => state.outcomePosts).toBe(before + 1);
});
