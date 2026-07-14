import { expect, test, type Page, type Route } from "@playwright/test";

const user = {
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
  created_at: new Date().toISOString(),
};

type ThreadRow = {
  id: string;
  who: "user" | "nur";
  text: string;
  structured_payload: Record<string, unknown>;
  created_at: string;
};

async function json(route: Route, body: unknown, status = 200) {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

async function installTalkMocks(page: Page, opts: { providerAvailable: boolean }) {
  const thread: ThreadRow[] = [];
  let lastTalkMode = "talk";
  let planCreated = false;
  let correctionSaved = false;
  let outcomePosts = 0;

  await page.route("**/api/v1/auth/me", route => json(route, user));
  await page.route("**/api/v1/orbits/current-state", route => json(route, {
    active_systems: 1, outcomes_returned: outcomePosts, insights_evolving: 0,
    open_questions: 0, research_staged: 0, plans_active: 0, live_status: "owner_ledger",
  }));
  await page.route("**/api/v1/orbits", route => {
    if (route.request().method() === "GET") return json(route, [orbit]);
    return json(route, orbit, 201);
  });
  await page.route("**/api/v1/journal", route => json(route, []));
  await page.route("**/api/v1/plans", async route => {
    if (route.request().method() === "GET") return json(route, []);
    planCreated = true;
    return json(route, {
      id: "plan-1",
      title: "Use this move",
      status: "ACTIVE",
      steps: [{ id: "step-1", title: "Record what changed from Talk", body: null, position: 0, done: false, done_at: null }],
    }, 201);
  });
  await page.route("**/api/v1/outcomes", async route => {
    outcomePosts += 1;
    return json(route, { id: `outcome-${outcomePosts}` }, 201);
  });
  await page.route("**/api/v1/cognition/corrections", route => {
    correctionSaved = true;
    return json(route, { id: "correction-1" }, 201);
  });
  await page.route("**/api/v1/cognition/talk-thread**", route => json(route, thread));
  await page.route("**/api/v1/cognition/talk", async route => {
    const body = JSON.parse(route.request().postData() || "{}") as { message: string; mode?: string };
    lastTalkMode = body.mode ?? "talk";
    thread.push({
      id: `turn-${thread.length + 1}`,
      who: "user",
      text: body.message,
      structured_payload: {},
      created_at: new Date().toISOString(),
    });
    const output = opts.providerAvailable ? {
      direct_response: "You are asking for source-faithful movement.",
      observed: ["The current line asks for movement."],
      inferred: ["The next move should stay small."],
      hypotheses: ["If the move is visible, it will be easier to return to."],
      uncertainty: ["This is based only on the mocked owned source."],
      next_move: "Write one visible owner-approved step.",
      memory_candidates: [],
      source_refs: ["DECISION:33333333-3333-3333-3333-333333333333"],
    } : {
      direct_response: "I saved this turn, but live AI is disabled on this server.",
      observed: [],
      inferred: [],
      hypotheses: [],
      uncertainty: ["AI provider disabled."],
      next_move: "Keep one concrete next line.",
      memory_candidates: [],
      source_refs: [],
    };
    const response = {
      turn_event_id: "44444444-4444-4444-4444-444444444444",
      response_event_id: `55555555-5555-5555-5555-55555555555${thread.length}`,
      model_run_id: "66666666-6666-6666-6666-666666666666",
      provider: opts.providerAvailable ? "openai" : "disabled",
      provider_available: opts.providerAvailable,
      provider_reason: opts.providerAvailable ? null : "AI provider is disabled.",
      output,
      evidence: {
        retrieval: opts.providerAvailable ? [{
          kind: "DECISION",
          id: "33333333-3333-3333-3333-333333333333",
          excerpt: "The owner approved one visible step.",
          rank: 1,
        }] : [],
        withheld: [],
      },
      verification: { verdict: opts.providerAvailable ? "PASS" : "WARN", checks: {} },
    };
    thread.push({
      id: response.response_event_id,
      who: "nur",
      text: output.direct_response,
      structured_payload: {
        talk_output: output,
        provider_reason: response.provider_reason,
        provider_available: response.provider_available,
        model_run_id: response.model_run_id,
      },
      created_at: new Date().toISOString(),
    });
    return json(route, response);
  });

  return {
    thread,
    lastTalkMode: () => lastTalkMode,
    planCreated: () => planCreated,
    correctionSaved: () => correctionSaved,
    outcomePosts: () => outcomePosts,
  };
}

test("talk disabled provider is explicit and screenshotable", async ({ page }) => {
  await installTalkMocks(page, { providerAvailable: false });
  await page.goto("/talk");
  await expect(page.locator("#page-talk")).toBeVisible();
  await page.locator("#talk-input").fill("Hold this without fake AI.");
  await page.getByRole("button", { name: "Send to NUR" }).click();
  await expect(page.getByText("I saved this turn, but live AI is disabled on this server.")).toBeVisible();
  await expect(page.getByText("AI provider is disabled.")).toBeVisible();
  await page.screenshot({
    path: process.cwd().endsWith("/apps/web")
      ? "../../proof/100/talk-disabled-provider-browser.png"
      : "proof/100/talk-disabled-provider-browser.png",
    fullPage: false,
  });
});

test("talk mocked provider shows structured labels and plan/correction actions", async ({ page }) => {
  const mocks = await installTalkMocks(page, { providerAvailable: true });
  await page.goto("/talk");
  await page.getByRole("button", { name: "Think deeper" }).click();
  await page.locator("#talk-input").fill("Make this source faithful.");
  await page.getByRole("button", { name: "Send to NUR" }).click();
  await expect(page.getByText("Observed")).toBeVisible();
  await expect(page.getByText("Inferred")).toBeVisible();
  await expect(page.getByText("Hypotheses")).toBeVisible();
  await expect(page.getByText("Uncertainty")).toBeVisible();
  expect(mocks.lastTalkMode()).toBe("reflect");

  await page.getByTestId("use-next-move-plan").click();
  await expect.poll(() => mocks.planCreated()).toBe(true);

  await page.getByTestId("talk-correction").fill("Do not infer urgency without evidence.");
  await page.getByTestId("submit-correction").click();
  await expect.poll(() => mocks.correctionSaved()).toBe(true);
});

test("former glow action is outcome-gated before visible count changes", async ({ page }) => {
  const mocks = await installTalkMocks(page, { providerAvailable: true });
  await page.goto("/today");
  await expect(page.getByText("quietly held · 0")).toBeVisible();

  await page.goto("/talk");
  await expect(page.getByText("Mark a Personal Glow")).toHaveCount(0);
  await page.getByTestId("talk-record-outcome").click();
  await expect(page.getByTestId("talk-outcome-form")).toBeVisible();
  expect(mocks.outcomePosts()).toBe(0);

  await page.goto("/today");
  await expect(page.getByText("quietly held · 0")).toBeVisible();

  await page.goto("/talk");
  await page.getByTestId("talk-record-outcome").click();
  await page.getByTestId("talk-outcome-input").fill("The owner shipped the visible fix.");
  await page.getByTestId("talk-submit-outcome").click();
  await expect.poll(() => mocks.outcomePosts()).toBe(1);

  await page.goto("/today");
  await expect(page.getByText("quietly held · 1")).toBeVisible();
});

test("talk thread survives reload from persisted API state", async ({ page }) => {
  const mocks = await installTalkMocks(page, { providerAvailable: true });
  mocks.thread.push(
    {
      id: "persisted-user",
      who: "user",
      text: "This line was already persisted.",
      structured_payload: {},
      created_at: new Date().toISOString(),
    },
    {
      id: "persisted-nur",
      who: "nur",
      text: "Persisted answer.",
      structured_payload: {
        provider_available: true,
        talk_output: {
          direct_response: "Persisted answer.",
          observed: [],
          inferred: [],
          hypotheses: [],
          uncertainty: [],
          next_move: null,
          memory_candidates: [],
          source_refs: [],
        },
      },
      created_at: new Date().toISOString(),
    },
  );

  await page.goto("/talk");
  await expect(page.getByText("This line was already persisted.")).toBeVisible();
  await page.reload();
  await expect(page.getByText("This line was already persisted.")).toBeVisible();
  await expect(page.getByText("Persisted answer.")).toBeVisible();
});
