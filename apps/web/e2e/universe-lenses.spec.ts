import { mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { expect, test, type Locator, type Page } from "@playwright/test";
import { installNurMocks, mockClaim } from "./helpers/nurMocks";

const proofDir = process.env.NUR_PROOF_DIR ?? (process.cwd().endsWith("/apps/web") ? "../../proof/screenshots" : "proof/screenshots");
test.use({ serviceWorkers: "block" });

function proofPath(name: string) {
  const path = join(proofDir, name);
  mkdirSync(dirname(path), { recursive: true });
  return path;
}

async function visibleBox(label: string, locator: Locator) {
  await expect(locator, label).toBeVisible();
  const box = await locator.boundingBox();
  expect(box, `${label} has a DOM box`).not.toBeNull();
  return box!;
}

function overlaps(a: { x: number; y: number; width: number; height: number }, b: { x: number; y: number; width: number; height: number }, pad = 0) {
  return !(a.x + a.width + pad <= b.x || b.x + b.width + pad <= a.x || a.y + a.height + pad <= b.y || b.y + b.height + pad <= a.y);
}

async function assertNoHorizontalOverflow(page: Page) {
  const widths = await page.evaluate(() => ({
    scroll: document.documentElement.scrollWidth,
    client: document.documentElement.clientWidth,
  }));
  expect(widths.scroll).toBeLessThanOrEqual(widths.client + 2);
}

test("Universe topbar routes to real lenses and search opens seeded records", async ({ page }) => {
  await installNurMocks(page);
  await page.goto("/universe");

  await page.getByRole("tab", { name: /Map/ }).click();
  await expect(page).toHaveURL(/\/universe\/map$/);
  await expect(page.getByTestId("universe-map-page")).toBeVisible();

  await page.getByRole("tab", { name: /Orbits/ }).click();
  await expect(page).toHaveURL(/\/universe\/orbits$/);
  await expect(page.getByTestId("universe-orbits-page")).toBeVisible();

  await page.getByRole("tab", { name: /Timeline/ }).click();
  await expect(page).toHaveURL(/\/universe\/timeline$/);
  await expect(page.getByTestId("universe-timeline-page")).toBeVisible();

  await page.getByRole("tab", { name: /Insights/ }).click();
  await expect(page).toHaveURL(/\/universe\/insights$/);
  await expect(page.getByTestId("universe-insights-page")).toBeVisible();

  await page.getByPlaceholder("Search NUR, system").fill("Postgres");
  await page.keyboard.press("Enter");
  await expect(page.getByText("Postgres RLS is the trust boundary.")).toBeVisible();
  await page.getByText("Postgres RLS is the trust boundary.").click();
  await expect(page).toHaveURL(/\/universe\/orbits$/);
});

test("Systems map labels breathe at 1280 and Add System does not cover labels", async ({ page }) => {
  await installNurMocks(page);
  await page.setViewportSize({ width: 1280, height: 720 });
  await page.goto("/universe/map");
  await expect(page.getByTestId("universe-map-page")).toBeVisible();

  const quiet = await visibleBox("Quiet Ambition label", page.getByTestId("lens-map-node-quiet"));
  const embodied = await visibleBox("Embodied Edge label", page.getByTestId("lens-map-node-embodied"));
  const relational = await visibleBox("Relational Gravity label", page.getByTestId("lens-map-node-relational"));
  const add = await visibleBox("Add System control", page.getByTestId("lens-add-system"));
  const title = await visibleBox("map title", page.locator(".lens-map-title"));
  const master = await visibleBox("master star", page.locator(".lens-map-master"));

  expect(overlaps(quiet, embodied, 10), "Quiet Ambition and Embodied Edge breathe").toBe(false);
  expect(overlaps(embodied, relational, 10), "Embodied Edge and Relational Gravity breathe").toBe(false);
  expect(overlaps(add, quiet, 10), "Add System does not cover Quiet Ambition").toBe(false);
  expect(overlaps(add, relational, 10), "Add System does not cover Relational Gravity").toBe(false);
  expect(overlaps(master, title, 6), "master star and NUR title do not collide").toBe(false);
  await assertNoHorizontalOverflow(page);

  await page.screenshot({ path: proofPath("systems-map-1280-label-breathing.png"), fullPage: false });
  await page.getByTestId("lens-map-node-embodied").click();
  await expect(page.getByRole("heading", { name: "Embodied Edge" })).toBeVisible();
  await page.getByTestId("lens-add-system").click();
  await expect(page.getByRole("heading", { name: /Name the sky it needs/i })).toBeVisible();
});

test("timeline filters, insights, and why-changed route are wired to Omega data", async ({ page }) => {
  await installNurMocks(page);
  await page.goto("/universe/timeline");
  await page.getByRole("button", { name: "omega" }).click();
  await expect(page.getByText("manual consolidation")).toBeVisible();
  await page.getByText("manual consolidation").click();
  await expect(page.getByText("Evidence detail")).toBeVisible();

  await page.goto("/universe/insights");
  await expect(page.getByText("The owner may prefer evidence-gated learning.")).toBeVisible();
  await page.getByText("Outcome evidence should strengthen planning patterns only after persisted results.").click();
  await expect(page).toHaveURL(new RegExp(`/universe/omega/why-changed/${mockClaim.id}$`));
  await expect(page.getByText("2 supporting evidence edges increased confidence.")).toBeVisible();
});

test("mobile map first viewport is usable, not clipped", async ({ page }) => {
  await installNurMocks(page);
  await page.setViewportSize({ width: 393, height: 852 });
  await page.goto("/universe/map");
  await expect(page.getByTestId("universe-map-page")).toBeVisible();
  await expect(page.getByTestId("lens-add-system")).toBeVisible();
  await expect(page.getByTestId("lens-map-node-quiet")).toBeVisible();
  await assertNoHorizontalOverflow(page);
  await page.screenshot({ path: proofPath("systems-map-mobile-393-clean.png"), fullPage: false });
});
