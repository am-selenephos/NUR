import {
  V197ApiClient,
  V197ApiError,
  type V197BridgeSnapshot,
  type V197CapsuleAnswer,
  type V197CapsuleView,
  type V197CommunityPost,
  type V197ConsultationDetail,
  type V197OwnedCapsule,
} from "./v197ApiClient";
import { applyV197Locale, directionForPreference, V197_LOCALE_META, type WritingPreference } from "./v197I18n";
import V197_ADJUNCT_FORENSIC_CSS from "../styles/v197-adjunct-forensic.css?raw";
import { markV197HolographicWordmark } from "./v197Brand";
import { createV197StarSeal } from "./v197StarSeal";

const ROOT_ID = "nur-v197-adjunct-root";
const STYLE_ID = "nur-v197-adjunct-style";

type RefreshSnapshot = () => Promise<V197BridgeSnapshot>;

function text(value: unknown, fallback = "Not recorded"): string {
  if (typeof value === "string" && value.trim()) return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return fallback;
}

function date(value: unknown): string {
  if (typeof value !== "string" || !value) return "No expiry";
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString();
}

function element<K extends keyof HTMLElementTagNameMap>(
  document: Document,
  tag: K,
  className?: string,
  content?: string,
): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (content !== undefined) node.textContent = content;
  return node;
}

function button(document: Document, label: string, action: string, primary = false): HTMLButtonElement {
  const node = element(document, "button", primary ? "nur-adjunct-button is-primary" : "nur-adjunct-button", label);
  node.type = "button";
  node.dataset.adjunctAction = action;
  return node;
}

function fact(document: Document, label: string, value: string): HTMLElement {
  const node = element(document, "div", "nur-adjunct-fact");
  node.append(element(document, "span", "nur-adjunct-label", label));
  node.append(element(document, "strong", undefined, value));
  return node;
}

function panel(document: Document, eyebrow: string, title: string): HTMLElement {
  const node = element(document, "section", "nur-adjunct-panel");
  node.append(element(document, "p", "nur-adjunct-eyebrow", eyebrow));
  node.append(element(document, "h2", undefined, title));
  return node;
}

function empty(document: Document, title: string, body: string): HTMLElement {
  const node = element(document, "div", "nur-adjunct-empty");
  const seal = createV197StarSeal(document, 20, false);
  seal.classList.add("nur-adjunct-empty-seal");
  node.append(seal, element(document, "strong", undefined, title));
  node.append(element(document, "p", undefined, body));
  return node;
}

function status(document: Document, message: string, tone: "quiet" | "good" | "warn" = "quiet"): HTMLElement {
  const node = element(document, "p", `nur-adjunct-status is-${tone}`, message);
  node.setAttribute("role", "status");
  return node;
}

function recordId(row: Record<string, unknown>): string {
  return text(row.id, "");
}

function ensureStyle(document: Document): void {
  if (document.getElementById(STYLE_ID)) return;
  const style = element(document, "style");
  style.id = STYLE_ID;
  style.textContent = V197_ADJUNCT_FORENSIC_CSS;
  document.head.append(style);
}

function mount(document: Document, title: string, subtitle: string, backRoute = "/systems"): HTMLElement {
  document.getElementById(ROOT_ID)?.remove();
  ensureStyle(document);
  const root = element(document, "div");
  root.id = ROOT_ID;
  root.dataset.v197NativeAdjunct = "true";
  const shell = element(document, "main", "nur-adjunct-shell");
  const topbar = element(document, "header", "nur-adjunct-topbar");
  const back = element(document, "button", "nur-adjunct-back", "← Return to NUR");
  back.type = "button";
  back.dataset.adjunctRoute = backRoute;
  const brand = element(document, "div", "nur-adjunct-brand", "NUR");
  markV197HolographicWordmark(brand);
  const brandSeal = createV197StarSeal(document, 24, true);
  brandSeal.classList.add("nur-adjunct-brand-seal");
  brand.prepend(brandSeal);
  topbar.append(back, brand, element(document, "span", "nur-adjunct-privacy", "Private by default. Shared only by choice."));
  const hero = element(document, "section", "nur-adjunct-hero");
  hero.append(element(document, "p", "nur-adjunct-eyebrow", "Neural Upgrade Rewiring"));
  hero.append(element(document, "h1", undefined, title));
  hero.append(element(document, "p", "nur-adjunct-subtitle", subtitle));
  shell.append(topbar, hero);
  root.append(shell);
  document.body.append(root);
  back.addEventListener("click", () => {
    window.history.pushState({}, "", backRoute);
    window.dispatchEvent(new PopStateEvent("popstate"));
  });
  return shell;
}

async function renderSettings(
  document: Document,
  api: V197ApiClient,
  snapshot: V197BridgeSnapshot,
  refreshSnapshot: RefreshSnapshot,
): Promise<void> {
  const shell = mount(document, "Your NUR, held on your terms.", "Language, model access, motion and learning preferences stay in your owner-scoped ledger.");
  const grid = element(document, "div", "nur-adjunct-grid");
  shell.append(grid);

  const provider = panel(document, "Provider boundary", "Intelligence connection");
  const providerState = snapshot.health?.ai_provider === "openai" ? "OPENAI_CONFIGURED" : "DISABLED";
  provider.append(element(document, "div", "nur-adjunct-facts"));
  provider.querySelector(".nur-adjunct-facts")?.append(
    fact(document, "Provider", providerState),
    fact(document, "Execution", "Server-side only"),
    fact(document, "Prompt logging", "Off by default"),
  );
  provider.append(status(document, providerState === "OPENAI_CONFIGURED"
    ? "The backend can answer Talk requests. No key is exposed to this document."
    : "AI is not connected. Run the local configuration script, then start NUR in OpenAI mode.", providerState === "OPENAI_CONFIGURED" ? "good" : "warn"));

  const language = panel(document, "Language and voice", "How NUR speaks with you");
  const localeLabel = element(document, "label", "nur-adjunct-field");
  localeLabel.append(element(document, "span", undefined, "Interface language"));
  const locale = element(document, "select", "nur-adjunct-select") as HTMLSelectElement;
  locale.dataset.adjunctControl = "locale";
  for (const row of V197_LOCALE_META) {
    const option = element(document, "option", undefined, `${row.label} · ${row.status === "polished_beta" ? "polished beta" : "draft"}`) as HTMLOptionElement;
    option.value = row.locale;
    option.selected = row.locale === (snapshot.preferences?.locale ?? snapshot.session.profile.locale ?? "en");
    locale.append(option);
  }
  localeLabel.append(locale);
  const writingLabel = element(document, "label", "nur-adjunct-field");
  writingLabel.append(element(document, "span", undefined, "Writing preference"));
  const writing = element(document, "select", "nur-adjunct-select") as HTMLSelectElement;
  writing.dataset.adjunctControl = "writing-preference";
  for (const [value, label] of [["default", "Language default"], ["roman", "Roman writing"], ["script", "Native script"]]) {
    const option = element(document, "option", undefined, label) as HTMLOptionElement;
    option.value = value;
    option.selected = value === (snapshot.preferences?.writing_preference ?? "default");
    writing.append(option);
  }
  writingLabel.append(writing);
  language.append(localeLabel, writingLabel);
  language.append(status(document, "Roman Urdu is stored as locale=ur with writing_preference=roman. Draft locales are labelled honestly."));

  const experience = panel(document, "Presence", "Motion, sound and Omega");
  const toggle = (label: string, key: string, checked: boolean) => {
    const row = element(document, "label", "nur-adjunct-toggle");
    row.append(element(document, "span", undefined, label));
    const input = element(document, "input") as HTMLInputElement;
    input.type = "checkbox";
    input.checked = checked;
    input.dataset.adjunctControl = key;
    row.append(input);
    return row;
  };
  experience.append(
    toggle("Quiet interface sound", "sound", snapshot.preferences?.sound_enabled ?? true),
    toggle("Reduce visual motion", "reduced-effects", snapshot.preferences?.reduced_effects ?? false),
    toggle("Omega research memory", "omega", snapshot.preferences?.omega_enabled ?? true),
  );

  const ownership = panel(document, "Owner controls", "Export and deletion boundaries");
  ownership.append(empty(document, "Not exposed in this beta", "Data export and account deletion require a complete verified owner flow. These controls remain honestly unavailable instead of pretending to work."));
  const disabledActions = element(document, "div", "nur-adjunct-actions");
  const exportButton = button(document, "Export my NUR", "settings-export");
  const deleteButton = button(document, "Delete account", "settings-delete");
  exportButton.disabled = true;
  deleteButton.disabled = true;
  disabledActions.append(exportButton, deleteButton);
  ownership.append(disabledActions);

  const savePanel = panel(document, "Persisted owner preference", "Return with the same language");
  savePanel.classList.add("is-wide");
  const actions = element(document, "div", "nur-adjunct-actions");
  const save = button(document, "Save preferences", "settings-save", true);
  actions.append(save);
  const saveState = status(document, "Changes are stored only in your owner-scoped preference row.");
  savePanel.append(actions, saveState);
  save.addEventListener("click", async () => {
    save.disabled = true;
    saveState.textContent = "Saving…";
    try {
      const selectedLocale = locale.value;
      const selectedWriting = writing.value as WritingPreference;
      await api.patchPreferences({
        locale: selectedLocale,
        writing_preference: selectedWriting,
        sound_enabled: (experience.querySelector('[data-adjunct-control="sound"]') as HTMLInputElement).checked,
        reduced_effects: (experience.querySelector('[data-adjunct-control="reduced-effects"]') as HTMLInputElement).checked,
        omega_enabled: (experience.querySelector('[data-adjunct-control="omega"]') as HTMLInputElement).checked,
      });
      const next = await refreshSnapshot();
      applyV197Locale(document, selectedLocale, selectedWriting);
      document.documentElement.dir = directionForPreference(selectedLocale, selectedWriting);
      saveState.textContent = "Saved. NUR will return in this language and writing style.";
      saveState.className = "nur-adjunct-status is-good";
      if (next.preferences) snapshot.preferences = next.preferences;
    } catch (error) {
      saveState.textContent = error instanceof Error ? error.message : "Preferences could not be saved.";
      saveState.className = "nur-adjunct-status is-warn";
    } finally {
      save.disabled = false;
    }
  });

  grid.append(provider, language, experience, ownership, savePanel);
}

function capsuleStatePanel(document: Document, view: V197CapsuleView): HTMLElement {
  const overview = panel(document, "Approved Context Capsule", `${view.title} — shared context`);
  overview.classList.add("is-wide");
  const facts = element(document, "div", "nur-adjunct-facts");
  facts.append(
    fact(document, "State", view.state),
    fact(document, "Purpose", view.purpose),
    fact(document, "Access", view.capability),
    fact(document, "Expires", date(view.expires_at)),
  );
  overview.append(facts, element(document, "p", "nur-adjunct-boundary", view.safety_copy));
  return overview;
}

async function renderRecipientCapsule(document: Document, api: V197ApiClient, capsuleId: string, view: V197CapsuleView): Promise<void> {
  const shell = mount(document, `${view.owner_display}'s shared context`, view.state === "ACTIVE"
    ? "Held open deliberately. Only the sources approved for this room can be reached."
    : `This bounded room is ${view.state.toLowerCase()}. Nothing outside it becomes visible.`, "/today");
  const grid = element(document, "div", "nur-adjunct-grid");
  shell.append(grid);
  grid.append(capsuleStatePanel(document, view));

  if (view.state !== "ACTIVE") {
    const terminal = panel(document, view.state, "The owner's boundary now closes this room.");
    terminal.classList.add("is-wide");
    terminal.append(empty(document, "Access is closed", "No cached answer is shown and no new question can be asked after revocation or expiry."));
    grid.append(terminal);
    return;
  }

  const included = panel(document, "Approved source ledger", "What is included");
  const includedList = element(document, "div", "nur-adjunct-list");
  if (!view.included.length) includedList.append(empty(document, "No source was included", "This room carries no answerable context."));
  for (const source of view.included) {
    const row = element(document, "article", "nur-adjunct-row");
    const head = element(document, "div", "nur-adjunct-row-head");
    head.append(element(document, "strong", undefined, source.title), element(document, "span", "nur-adjunct-chip", `${source.source_kind} · ${source.representation}`));
    row.append(head, element(document, "p", undefined, source.body));
    includedList.append(row);
  }
  included.append(includedList);

  const excluded = panel(document, "Boundary proof", "What is excluded");
  const excludedList = element(document, "div", "nur-adjunct-list");
  if (!view.excluded_summary.length) excludedList.append(empty(document, "No withheld category is enumerated", "The recipient still cannot traverse the owner's general memory, Talk, Journal, Timeline, Settings or Omega."));
  for (const item of view.excluded_summary) {
    const row = element(document, "div", "nur-adjunct-row");
    row.append(element(document, "strong", undefined, `${text(item.source_kind)} · ${text(item.count, "0")} withheld`));
    row.append(element(document, "p", undefined, text(item.note, "Withheld by the owner")));
    excludedList.append(row);
  }
  excluded.append(excludedList);

  const ask = panel(document, "Scoped question", "Ask within this approved boundary");
  ask.classList.add("is-wide");
  const canAsk = view.capability === "ASK_SCOPED_QUESTIONS";
  const field = element(document, "label", "nur-adjunct-field");
  field.append(element(document, "span", undefined, "Question"));
  const input = element(document, "textarea", "nur-adjunct-textarea") as HTMLTextAreaElement;
  input.placeholder = canAsk ? "Ask only about the approved sources…" : "This room is read-only.";
  input.disabled = !canAsk;
  input.dataset.adjunctControl = "capsule-question";
  field.append(input);
  const actions = element(document, "div", "nur-adjunct-actions");
  const askButton = button(document, "Ask from approved context", "capsule-ask", true);
  askButton.disabled = !canAsk;
  const copyButton = button(document, "Copy room address", "capsule-copy");
  actions.append(askButton, copyButton);
  const askState = status(document, canAsk ? "Answers cite only included source IDs." : "The owner granted read-only access.");
  const answerHost = element(document, "div");
  ask.append(field, actions, askState, answerHost);

  copyButton.addEventListener("click", async () => {
    await navigator.clipboard?.writeText(window.location.href);
    askState.textContent = "Room address copied.";
    askState.className = "nur-adjunct-status is-good";
  });
  askButton.addEventListener("click", async () => {
    const question = input.value.trim();
    if (!question) {
      askState.textContent = "Write one scoped question first.";
      askState.className = "nur-adjunct-status is-warn";
      return;
    }
    askButton.disabled = true;
    askState.textContent = "Reading only the approved sources…";
    try {
      const answer: V197CapsuleAnswer = await api.askCapsule(capsuleId, question);
      answerHost.replaceChildren();
      const answerNode = element(document, "article", "nur-adjunct-answer");
      answerNode.append(element(document, "p", "nur-adjunct-eyebrow", `${answer.answer_mode} · source-bound`));
      answerNode.append(element(document, "blockquote", undefined, answer.answer_text));
      answerNode.append(element(document, "p", undefined, answer.source_refs.length ? `Sources: ${answer.source_refs.join(", ")}` : "No approved source supported a direct answer."));
      if (answer.policy_explanation) answerNode.append(element(document, "p", "nur-adjunct-boundary", answer.policy_explanation));
      answerHost.append(answerNode);
      askState.textContent = "Answer persisted inside the capsule ledger.";
      askState.className = "nur-adjunct-status is-good";
    } catch (error) {
      askState.textContent = error instanceof Error ? error.message : "The bounded answer could not be created.";
      askState.className = "nur-adjunct-status is-warn";
    } finally {
      askButton.disabled = !canAsk;
    }
  });

  grid.append(included, excluded, ask);
}

async function renderOwnerCapsule(document: Document, api: V197ApiClient, capsule: V197OwnedCapsule): Promise<void> {
  const shell = mount(document, "A bounded room you control.", "Owner preview exposes lifecycle and audit controls, never the recipient's private question composer.", "/universe/orbits");
  const grid = element(document, "div", "nur-adjunct-grid");
  shell.append(grid);
  const lifecycle = panel(document, "Owner capsule", capsule.title);
  lifecycle.classList.add("is-wide");
  const state = capsule.revoked_at ? "REVOKED" : "ACTIVE";
  const facts = element(document, "div", "nur-adjunct-facts");
  facts.append(fact(document, "State", state), fact(document, "Purpose", capsule.purpose), fact(document, "Capability", capsule.capability), fact(document, "Expires", date(capsule.expires_at)));
  lifecycle.append(facts);
  const actions = element(document, "div", "nur-adjunct-actions");
  const auditButton = button(document, "Open access audit", "capsule-audit");
  const revokeButton = button(document, "Revoke now", "capsule-revoke", true);
  revokeButton.disabled = state === "REVOKED";
  actions.append(auditButton, revokeButton);
  const lifecycleState = status(document, state === "ACTIVE" ? "Revocation takes effect immediately." : "This capsule is already revoked.", state === "ACTIVE" ? "quiet" : "warn");
  const auditHost = element(document, "div", "nur-adjunct-list");
  lifecycle.append(actions, lifecycleState, auditHost);
  auditButton.addEventListener("click", async () => {
    auditButton.disabled = true;
    try {
      const rows = await api.capsuleAudit(capsule.id);
      auditHost.replaceChildren();
      if (!rows.length) auditHost.append(empty(document, "No access event yet", "The room has not been opened by a recipient."));
      for (const row of rows) {
        const item = element(document, "div", "nur-adjunct-row");
        item.append(element(document, "strong", undefined, text(row.event_kind)), element(document, "p", undefined, date(row.created_at)));
        auditHost.append(item);
      }
      lifecycleState.textContent = `${rows.length} owner-scoped audit event${rows.length === 1 ? "" : "s"}.`;
    } catch (error) {
      lifecycleState.textContent = error instanceof Error ? error.message : "Audit could not be read.";
      lifecycleState.className = "nur-adjunct-status is-warn";
    } finally {
      auditButton.disabled = false;
    }
  });
  revokeButton.addEventListener("click", async () => {
    revokeButton.disabled = true;
    lifecycleState.textContent = "Closing the room…";
    try {
      await api.revokeCapsule(capsule.id);
      lifecycleState.textContent = "Revoked. Recipient reads and asks are blocked immediately.";
      lifecycleState.className = "nur-adjunct-status is-good";
    } catch (error) {
      lifecycleState.textContent = error instanceof Error ? error.message : "Revocation failed.";
      lifecycleState.className = "nur-adjunct-status is-warn";
      revokeButton.disabled = false;
    }
  });
  grid.append(lifecycle);
}

async function renderCapsule(document: Document, api: V197ApiClient, capsuleId: string): Promise<void> {
  try {
    const view = await api.capsuleView(capsuleId);
    await renderRecipientCapsule(document, api, capsuleId, view);
    return;
  } catch (error) {
    if (!(error instanceof V197ApiError) || error.status !== 404) throw error;
  }
  const owned = (await api.ownedCapsules()).find(row => row.id === capsuleId);
  if (owned) {
    await renderOwnerCapsule(document, api, owned);
    return;
  }
  const shell = mount(document, "This room is not available.", "No Context Capsule is shared with this session at this address.", "/today");
  const unavailable = panel(document, "Boundary held", "Nothing leaks through a missing grant");
  unavailable.classList.add("is-wide");
  unavailable.append(empty(document, "No active grant", "Sign in as the intended recipient or ask the owner for a current capsule address."));
  const grid = element(document, "div", "nur-adjunct-grid");
  grid.append(unavailable);
  shell.append(grid);
}

function omegaList(
  document: Document,
  rows: Array<Record<string, unknown>>,
  titleKey: string,
  bodyKey: string,
  chipKey: string,
  actions?: (row: Record<string, unknown>) => HTMLElement,
): HTMLElement {
  const list = element(document, "div", "nur-adjunct-list");
  if (!rows.length) return empty(document, "No persisted evidence yet", "Omega does not invent a result before the owner's evidence exists.");
  for (const row of rows) {
    const item = element(document, "article", "nur-adjunct-row");
    const head = element(document, "div", "nur-adjunct-row-head");
    head.append(element(document, "strong", undefined, text(row[titleKey])), element(document, "span", "nur-adjunct-chip", text(row[chipKey], "UNRESOLVED")));
    item.append(head);
    const body = text(row[bodyKey], "");
    if (body) item.append(element(document, "p", undefined, body));
    if (actions) item.append(actions(row));
    list.append(item);
  }
  return list;
}

function navigate(route: string): void {
  window.history.pushState({}, "", route);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

async function renderOmegaDashboard(document: Document, api: V197ApiClient): Promise<void> {
  const [dashboard, scheduler] = await Promise.all([api.omegaDashboard(), api.omegaScheduler()]);
  const shell = mount(document, "Evidence changes the model, deliberately.", "Omega is an owner-only cognition ledger: claims, contradictions, predictions and governed learning proposals. It is not sentience and exposes no chain-of-thought.");
  const grid = element(document, "div", "nur-adjunct-grid");
  shell.append(grid);

  const runtime = panel(document, "Omega substrate", "Consolidation status");
  runtime.classList.add("is-wide");
  const facts = element(document, "div", "nur-adjunct-facts");
  facts.append(fact(document, "Scheduler", scheduler.enabled && scheduler.scheduled_consolidation ? "ACTIVE" : "DISABLED"), fact(document, "Worker", scheduler.worker_mode), fact(document, "Last run", scheduler.last_consolidation_status), fact(document, "Interval", `${scheduler.interval_hours} hours`));
  runtime.append(facts);
  const runtimeActions = element(document, "div", "nur-adjunct-actions");
  const consolidate = button(document, "Consolidate owner evidence", "omega-consolidate", true);
  const review = button(document, `Open review queue (${dashboard.review_queue.length})`, "omega-review");
  const exportButton = button(document, "Export owner Omega", "omega-export");
  runtimeActions.append(consolidate, review, exportButton);
  const runtimeState = status(document, "Consolidation proposes changes; sensitive inferences still require owner review.");
  runtime.append(runtimeActions, runtimeState);
  review.addEventListener("click", () => navigate("/universe/omega/review"));
  consolidate.addEventListener("click", async () => {
    consolidate.disabled = true;
    runtimeState.textContent = "Consolidating the owner ledger…";
    try {
      const run = await api.consolidateOmega();
      runtimeState.textContent = `Run ${text(run.status)}: ${text(run.created_claims, "0")} claims created, ${text(run.contradictions_found, "0")} contradictions found.`;
      runtimeState.className = "nur-adjunct-status is-good";
    } catch (error) {
      runtimeState.textContent = error instanceof Error ? error.message : "Consolidation did not complete.";
      runtimeState.className = "nur-adjunct-status is-warn";
    } finally {
      consolidate.disabled = false;
    }
  });
  exportButton.addEventListener("click", async () => {
    exportButton.disabled = true;
    try {
      const data = await api.omegaExport();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const anchor = element(document, "a") as HTMLAnchorElement;
      anchor.href = url;
      anchor.download = "nur-omega-owner-export.json";
      anchor.click();
      URL.revokeObjectURL(url);
      runtimeState.textContent = "Owner-scoped Omega export prepared locally.";
      runtimeState.className = "nur-adjunct-status is-good";
    } catch (error) {
      runtimeState.textContent = error instanceof Error ? error.message : "Export failed.";
      runtimeState.className = "nur-adjunct-status is-warn";
    } finally {
      exportButton.disabled = false;
    }
  });

  const claimPanel = panel(document, "Candidate understanding", `Claims · ${dashboard.claims.length}`);
  claimPanel.append(omegaList(document, dashboard.claims, "claim_text", "", "truth_status", row => {
    const actions = element(document, "div", "nur-adjunct-actions");
    const why = button(document, "Why changed?", "omega-why");
    why.addEventListener("click", () => navigate(`/universe/omega/why-changed/${recordId(row)}`));
    actions.append(why);
    return actions;
  }));

  const contradictionPanel = panel(document, "Open tension", `Contradictions · ${dashboard.contradictions.length}`);
  contradictionPanel.append(omegaList(document, dashboard.contradictions, "description", "proposed_resolution", "severity"));
  const predictionPanel = panel(document, "Unresolved future", `Predictions · ${dashboard.predictions.length}`);
  predictionPanel.append(omegaList(document, dashboard.predictions, "prediction_text", "expected_observation", "status"));
  const proposalPanel = panel(document, "Governed learning", `Proposals · ${dashboard.learning_proposals.length}`);
  proposalPanel.append(omegaList(document, dashboard.learning_proposals, "description", "evidence_summary", "status"));
  grid.append(runtime, claimPanel, contradictionPanel, predictionPanel, proposalPanel);
}

async function renderOmegaReview(document: Document, api: V197ApiClient): Promise<void> {
  const rows = await api.omegaReviewQueue();
  const shell = mount(document, "Nothing sensitive becomes truth by accident.", "Review model-generated claim candidates before they enter the owner evidence graph.", "/universe/omega");
  const grid = element(document, "div", "nur-adjunct-grid");
  shell.append(grid);
  const review = panel(document, "Owner confirmation gate", `Pending review · ${rows.length}`);
  review.classList.add("is-wide");
  const reviewState = status(document, "Approval and rejection are persisted and owner-scoped.");
  review.append(omegaList(document, rows, "candidate_claim_text", "reason", "sensitivity", row => {
    const actions = element(document, "div", "nur-adjunct-actions");
    const approve = button(document, "Approve as reviewed", `omega-review-approve-${recordId(row)}`, true);
    const reject = button(document, "Reject", `omega-review-reject-${recordId(row)}`);
    const act = async (action: "approve" | "reject") => {
      approve.disabled = true;
      reject.disabled = true;
      try {
        await api.reviewOmegaItem(recordId(row), action);
        row.status = action === "approve" ? "APPROVED" : "REJECTED";
        reviewState.textContent = `Candidate ${action === "approve" ? "approved" : "rejected"}. Refreshing owner queue…`;
        reviewState.className = "nur-adjunct-status is-good";
        await renderOmegaReview(document, api);
      } catch (error) {
        reviewState.textContent = error instanceof Error ? error.message : "Review action failed.";
        reviewState.className = "nur-adjunct-status is-warn";
        approve.disabled = false;
        reject.disabled = false;
      }
    };
    approve.addEventListener("click", () => void act("approve"));
    reject.addEventListener("click", () => void act("reject"));
    actions.append(approve, reject);
    return actions;
  }), reviewState);
  grid.append(review);
}

async function renderOmegaWhyChanged(document: Document, api: V197ApiClient, claimId: string): Promise<void> {
  const [why, evidence] = await Promise.all([api.omegaWhyChanged(claimId), api.omegaEvidence(claimId)]);
  const shell = mount(document, "Why NUR changed its mind.", "A provenance explanation assembled from the owner evidence graph, not hidden chain-of-thought.", "/universe/omega");
  const grid = element(document, "div", "nur-adjunct-grid");
  shell.append(grid);
  const claim = panel(document, "Current claim", text(why.claim_text));
  claim.classList.add("is-wide");
  const facts = element(document, "div", "nur-adjunct-facts");
  facts.append(fact(document, "Truth state", text(why.current_truth_status)), fact(document, "Confidence", text(why.current_confidence)));
  claim.append(facts);

  const changed = panel(document, "Change ledger", "What moved this claim");
  const reasons = Array.isArray(why.changed_because) ? why.changed_because : [];
  changed.append(omegaList(document, reasons.map((value, index) => ({ id: String(index), title: text(value), state: "EVIDENCE" })), "title", "", "state"));

  const evidencePanel = panel(document, "Evidence graph", `Edges · ${evidence.length}`);
  evidencePanel.append(omegaList(document, evidence, "relation", "note", "evidence_kind"));
  const actions = element(document, "div", "nur-adjunct-actions");
  const confirm = button(document, "Confirm claim", "omega-claim-confirm", true);
  const retire = button(document, "Retire claim", "omega-claim-retire");
  actions.append(confirm, retire);
  const actionState = status(document, text(why.unresolved_note, "Owner review remains the final authority."));
  claim.append(actions, actionState);
  const act = async (action: "confirm" | "retire") => {
    confirm.disabled = true;
    retire.disabled = true;
    try {
      if (action === "confirm") await api.confirmOmegaClaim(claimId);
      else await api.retireOmegaClaim(claimId);
      actionState.textContent = action === "confirm" ? "Claim confirmed by owner." : "Claim retired from active use.";
      actionState.className = "nur-adjunct-status is-good";
    } catch (error) {
      actionState.textContent = error instanceof Error ? error.message : "Claim action failed.";
      actionState.className = "nur-adjunct-status is-warn";
      confirm.disabled = false;
      retire.disabled = false;
    }
  };
  confirm.addEventListener("click", () => void act("confirm"));
  retire.addEventListener("click", () => void act("retire"));
  grid.append(claim, changed, evidencePanel);
}

function consultationStages(document: Document, detail: V197ConsultationDetail): HTMLElement {
  const rail = element(document, "div", "nur-adjunct-actions");
  const completed = new Set(detail.completed_stages.map(row => row.stage));
  for (const stage of detail.stage_order) {
    const chip = element(document, "span", "nur-adjunct-chip", `${completed.has(stage) ? "✓ " : stage === detail.next_stage ? "✦ " : ""}${stage}`);
    if (stage === detail.next_stage) chip.dataset.currentStage = "true";
    rail.append(chip);
  }
  return rail;
}

async function renderConsultationIndex(
  document: Document,
  api: V197ApiClient,
  snapshot: V197BridgeSnapshot,
): Promise<void> {
  const rows = await api.consultations();
  const shell = mount(document, "A question moves when context returns.", "Consultation keeps lived experience, constraints, disagreement, evidence and the final outcome inside one bounded ORIENT → RETURN path.");
  const grid = element(document, "div", "nur-adjunct-grid");
  shell.append(grid);

  const listPanel = panel(document, "Consultation ledger", `Open and returned · ${rows.length}`);
  const list = element(document, "div", "nur-adjunct-list");
  if (!rows.length) list.append(empty(document, "No Consultation yet", "Open one bounded question. Nothing is synthesized before contributions exist."));
  for (const row of rows) {
    const item = element(document, "article", "nur-adjunct-row");
    const head = element(document, "div", "nur-adjunct-row-head");
    head.append(element(document, "strong", undefined, row.title), element(document, "span", "nur-adjunct-chip", `${row.current_stage} · ${row.status}`));
    item.append(head, element(document, "p", undefined, row.question));
    const actions = element(document, "div", "nur-adjunct-actions");
    const open = button(document, "Enter Consultation", `consultation-open-${row.id}`);
    open.addEventListener("click", () => navigate(`/consultations/${row.id}`));
    actions.append(open);
    item.append(actions);
    list.append(item);
  }
  listPanel.append(list);

  const create = panel(document, "ORIENT", "Open a bounded Consultation");
  const field = (label: string, control: HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement) => {
    const wrapper = element(document, "label", "nur-adjunct-field");
    wrapper.append(element(document, "span", undefined, label), control);
    return wrapper;
  };
  const title = element(document, "input", "nur-adjunct-input") as HTMLInputElement;
  title.placeholder = "Consultation title";
  const question = element(document, "textarea", "nur-adjunct-textarea") as HTMLTextAreaElement;
  question.placeholder = "What is the actual question?";
  const purpose = element(document, "input", "nur-adjunct-input") as HTMLInputElement;
  purpose.placeholder = "Why does this need a shared return?";
  const desired = element(document, "input", "nur-adjunct-input") as HTMLInputElement;
  desired.placeholder = "What useful outcome should exist?";
  const scope = element(document, "input", "nur-adjunct-input") as HTMLInputElement;
  scope.placeholder = "What is inside and outside this Consultation?";
  const room = element(document, "select", "nur-adjunct-select") as HTMLSelectElement;
  room.append(element(document, "option", undefined, "Private owner Consultation"));
  room.options[0].value = "";
  for (const candidate of snapshot.communityRooms ?? []) {
    const option = element(document, "option", undefined, `${candidate.title} · ${candidate.current_user_role}`) as HTMLOptionElement;
    option.value = candidate.id;
    room.append(option);
  }
  create.append(field("Title", title), field("Question", question), field("Purpose", purpose), field("Desired outcome", desired), field("Scope statement", scope), field("Bounded room", room));
  const actions = element(document, "div", "nur-adjunct-actions");
  const createButton = button(document, "Open Consultation", "consultation-create", true);
  actions.append(createButton);
  const createState = status(document, "Only explicit Consultation records are shared. Private Talk, Journal and Omega remain outside.");
  create.append(actions, createState);
  createButton.addEventListener("click", async () => {
    const values = [title.value, question.value, purpose.value, desired.value, scope.value].map(value => value.trim());
    if (values.some(value => !value)) {
      createState.textContent = "Title, question, purpose, desired outcome and scope are all required.";
      createState.className = "nur-adjunct-status is-warn";
      return;
    }
    createButton.disabled = true;
    try {
      const created = await api.createConsultation({
        title: values[0], question: values[1], purpose: values[2], desired_outcome: values[3],
        scope_statement: values[4], room_id: room.value || null,
        orbit_id: snapshot.session.orbit.id, system_slug: "quiet-ambition",
      });
      navigate(`/consultations/${created.id}`);
    } catch (error) {
      createState.textContent = error instanceof Error ? error.message : "Consultation could not be opened.";
      createState.className = "nur-adjunct-status is-warn";
      createButton.disabled = false;
    }
  });
  grid.append(listPanel, create);
}

async function renderConsultationDetail(document: Document, api: V197ApiClient, consultationId: string): Promise<void> {
  const detail = await api.consultation(consultationId);
  const row = detail.consultation;
  const shell = mount(document, row.title, row.question, "/consultations");
  const grid = element(document, "div", "nur-adjunct-grid");
  shell.append(grid);

  const orientation = panel(document, "Bounded Consultation", `${row.current_stage} · ${row.status}`);
  orientation.classList.add("is-wide");
  const facts = element(document, "div", "nur-adjunct-facts");
  facts.append(fact(document, "Purpose", row.purpose), fact(document, "Desired outcome", row.desired_outcome), fact(document, "Scope", row.scope_statement), fact(document, "Your role", row.current_user_role));
  orientation.append(facts, consultationStages(document, detail), element(document, "p", "nur-adjunct-boundary", detail.what_nur_may_be_wrong_about));

  const contributions = panel(document, "GATHER", `Contributions · ${detail.contributions.length}`);
  const contributionList = element(document, "div", "nur-adjunct-list");
  if (!detail.contributions.length) contributionList.append(empty(document, "No contribution yet", "Lived experience, constraints and disagreement stay visible instead of being smoothed away."));
  for (const contribution of detail.contributions) {
    const item = element(document, "article", "nur-adjunct-row");
    const head = element(document, "div", "nur-adjunct-row-head");
    head.append(element(document, "strong", undefined, contribution.contribution_type.replaceAll("_", " ")), element(document, "span", "nur-adjunct-chip", contribution.provenance_label));
    item.append(head, element(document, "p", undefined, contribution.body));
    contributionList.append(item);
  }
  contributions.append(contributionList);
  if (row.status === "ACTIVE") {
    const type = element(document, "select", "nur-adjunct-select") as HTMLSelectElement;
    for (const value of ["LIVED_EXPERIENCE", "PRACTICAL_MOVE", "CONSTRAINT", "COUNTEREXAMPLE", "DISAGREEMENT", "WITNESS", "TRIED_THIS", "OUTCOME", "EXPERT_VOICE", "RESEARCH_EVIDENCE"]) {
      const option = element(document, "option", undefined, value.replaceAll("_", " ")) as HTMLOptionElement;
      option.value = value;
      type.append(option);
    }
    const body = element(document, "textarea", "nur-adjunct-textarea") as HTMLTextAreaElement;
    body.placeholder = "Add only what belongs inside this Consultation…";
    const send = button(document, "Add contribution", "consultation-contribute", true);
    const contributionState = status(document, "This contribution is shared only with members of the bounded room.");
    contributions.append(type, body, send, contributionState);
    send.addEventListener("click", async () => {
      if (!body.value.trim()) {
        contributionState.textContent = "Write one contribution first.";
        contributionState.className = "nur-adjunct-status is-warn";
        return;
      }
      send.disabled = true;
      try {
        await api.addConsultationContribution(consultationId, {
          contribution_type: type.value, body: body.value.trim(),
          language_tag: document.documentElement.lang || "en",
        });
        await renderConsultationDetail(document, api, consultationId);
      } catch (error) {
        contributionState.textContent = error instanceof Error ? error.message : "Contribution was not saved.";
        contributionState.className = "nur-adjunct-status is-warn";
        send.disabled = false;
      }
    });
  }

  const movement = panel(document, "Owner movement", row.status === "COMPLETED" ? "RETURN is held" : `Complete ${detail.next_stage}`);
  const stageList = element(document, "div", "nur-adjunct-list");
  for (const stage of detail.completed_stages) {
    const item = element(document, "article", "nur-adjunct-row");
    item.append(element(document, "strong", undefined, stage.stage), element(document, "p", undefined, JSON.stringify(stage.stage_payload)));
    stageList.append(item);
  }
  movement.append(stageList);
  if (row.status === "ACTIVE" && row.current_user_role === "OWNER" && detail.next_stage) {
    const note = element(document, "textarea", "nur-adjunct-textarea") as HTMLTextAreaElement;
    note.placeholder = detail.next_stage === "RETURN" ? "Record the outcome and prediction comparison…" : `Record the ${detail.next_stage} evidence…`;
    const advance = button(document, `Persist ${detail.next_stage}`, `consultation-stage-${detail.next_stage.toLowerCase()}`, true);
    const stageState = status(document, "Stage movement happens only after server persistence.");
    movement.append(note, advance, stageState);
    advance.addEventListener("click", async () => {
      if (!note.value.trim()) {
        stageState.textContent = "Record this stage before advancing.";
        stageState.className = "nur-adjunct-status is-warn";
        return;
      }
      advance.disabled = true;
      try {
        const result = await api.completeConsultationStage(consultationId, detail.next_stage!, { note: note.value.trim() });
        if (result.glow?.status === "AWARDED") stageState.textContent = `RETURN persisted · +${text(result.glow.awarded_points, "0")} Glow`;
        await renderConsultationDetail(document, api, consultationId);
      } catch (error) {
        stageState.textContent = error instanceof Error ? error.message : "Stage was not persisted.";
        stageState.className = "nur-adjunct-status is-warn";
        advance.disabled = false;
      }
    });
  } else if (row.status === "ACTIVE") {
    movement.append(empty(document, "Owner movement only", "Members contribute evidence and disagreement. The Consultation owner advances the stage."));
  } else {
    movement.append(status(document, "This Consultation completed its RETURN loop.", "good"));
  }
  grid.append(orientation, contributions, movement);
}

async function loadCommunityFeed(api: V197ApiClient): Promise<{
  rooms: Awaited<ReturnType<V197ApiClient["communityRooms"]>>;
  posts: V197CommunityPost[];
}> {
  const rooms = await api.communityRooms();
  const groups = await Promise.all(rooms.map(room => api.communityPosts(room.id).catch(() => [])));
  const posts = groups.flat().sort((a, b) => Date.parse(b.created_at) - Date.parse(a.created_at));
  return { rooms, posts };
}

async function renderCommunityIndex(document: Document, api: V197ApiClient, route: string): Promise<void> {
  const { rooms, posts } = await loadCommunityFeed(api);
  const shell = mount(document, "Shared signal without private spill.", "Community is built from real bounded rooms and persisted contributions. No fake people, replies, activity or live public count appears here.");
  const grid = element(document, "div", "nur-adjunct-grid");
  shell.append(grid);

  if (["/community/people", "/community/saved", "/community/notifications", "/community/moderation"].includes(route)) {
    const unavailable = panel(document, "Honest product state", route.split("/").pop()?.replaceAll("-", " ") ?? "Community");
    unavailable.classList.add("is-wide");
    unavailable.append(empty(document, "Not connected in this build", "This route has no fabricated records. Bounded rooms, posts, comments, reactions and Consultations remain available."));
    const actions = element(document, "div", "nur-adjunct-actions");
    const back = button(document, "Open bounded Community", "community-return", true);
    back.addEventListener("click", () => navigate("/community"));
    actions.append(back);
    unavailable.append(actions);
    grid.append(unavailable);
    return;
  }

  const roomPanel = panel(document, "Group NUR boundaries", `Rooms · ${rooms.length}`);
  const roomList = element(document, "div", "nur-adjunct-list");
  if (!rooms.length) roomList.append(empty(document, "No bounded room yet", "Create one real room. NUR will not invent a community around you."));
  for (const room of rooms) {
    const row = element(document, "article", "nur-adjunct-row");
    const head = element(document, "div", "nur-adjunct-row-head");
    head.append(element(document, "strong", undefined, room.title), element(document, "span", "nur-adjunct-chip", `${room.is_demo ? "DEMO · " : ""}${room.room_kind}`));
    row.append(head, element(document, "p", undefined, room.description ?? room.privacy));
    const actions = element(document, "div", "nur-adjunct-actions");
    const open = button(document, "Enter bounded room", `community-room-${room.id}`);
    open.addEventListener("click", () => navigate(`/community/room/${room.id}`));
    actions.append(open);
    row.append(actions);
    roomList.append(row);
  }
  roomPanel.append(roomList);
  const roomTitle = element(document, "input", "nur-adjunct-input") as HTMLInputElement;
  roomTitle.placeholder = "Name one bounded room";
  const createRoom = button(document, "Create Group NUR room", "community-room-create", true);
  const roomState = status(document, "The creator becomes owner. Membership is explicit and server-enforced.");
  roomPanel.append(roomTitle, createRoom, roomState);
  createRoom.addEventListener("click", async () => {
    if (!roomTitle.value.trim()) {
      roomState.textContent = "Name the room first.";
      roomState.className = "nur-adjunct-status is-warn";
      return;
    }
    createRoom.disabled = true;
    try {
      const created = await api.createCommunityRoom(roomTitle.value.trim(), "GROUP");
      navigate(`/community/room/${created.id}`);
    } catch (error) {
      roomState.textContent = error instanceof Error ? error.message : "Room was not created.";
      roomState.className = "nur-adjunct-status is-warn";
      createRoom.disabled = false;
    }
  });

  const feed = panel(document, "Persisted signal feed", `Posts · ${posts.length}`);
  const postList = element(document, "div", "nur-adjunct-list");
  if (!posts.length) postList.append(empty(document, "No post yet", "Room members can write the first persisted contribution."));
  for (const post of posts) {
    const room = rooms.find(candidate => candidate.id === post.room_id);
    const row = element(document, "article", "nur-adjunct-row");
    const head = element(document, "div", "nur-adjunct-row-head");
    head.append(element(document, "strong", undefined, post.title), element(document, "span", "nur-adjunct-chip", `${post.is_demo ? "DEMO · " : ""}${room?.title ?? "ROOM"}`));
    row.append(head, element(document, "p", undefined, post.body));
    const actions = element(document, "div", "nur-adjunct-actions");
    const open = button(document, "Open thread", `community-post-${post.id}`);
    open.addEventListener("click", () => navigate(`/community/post/${post.id}?room=${post.room_id}`));
    actions.append(open);
    row.append(actions);
    postList.append(row);
  }
  feed.append(postList);
  grid.append(roomPanel, feed);
}

async function renderCommunityRoom(document: Document, api: V197ApiClient, roomId: string): Promise<void> {
  const [room, summary, messages, posts] = await Promise.all([
    api.get<Record<string, unknown>>(`/community/rooms/${encodeURIComponent(roomId)}`),
    api.communityRoomSummary(roomId), api.communityMessages(roomId), api.communityPosts(roomId),
  ]);
  const shell = mount(document, text(room.title), text(room.description, "A bounded Group NUR room."), "/community");
  const grid = element(document, "div", "nur-adjunct-grid");
  shell.append(grid);
  const boundary = panel(document, "Room boundary", `${text(room.current_user_role)} · ${text(room.room_kind)}`);
  boundary.classList.add("is-wide");
  const facts = element(document, "div", "nur-adjunct-facts");
  facts.append(fact(document, "Messages", text(summary.counts.messages, "0")), fact(document, "Posts", text(summary.counts.posts, "0")), fact(document, "Contributions", text(summary.counts.comments, "0")), fact(document, "External public feed", summary.external_public_feed));
  boundary.append(facts, element(document, "p", "nur-adjunct-boundary", text(room.privacy)));
  const boundaryActions = element(document, "div", "nur-adjunct-actions");
  const consultation = button(document, "Start Consultation", "community-start-consultation", true);
  consultation.addEventListener("click", () => navigate("/consultations"));
  boundaryActions.append(consultation);
  boundary.append(boundaryActions);

  const conversation = panel(document, "Group NUR", `Conversation · ${messages.length}`);
  const messageList = element(document, "div", "nur-adjunct-list");
  if (!messages.length) messageList.append(empty(document, "No room message yet", "NUR stays quiet until a member contributes."));
  for (const message of messages) {
    const item = element(document, "article", "nur-adjunct-row");
    item.append(element(document, "span", "nur-adjunct-chip", `${message.is_demo ? "DEMO · " : ""}${message.provenance_label}`), element(document, "p", undefined, message.body));
    messageList.append(item);
  }
  const messageInput = element(document, "textarea", "nur-adjunct-textarea") as HTMLTextAreaElement;
  messageInput.placeholder = "Write inside this room boundary…";
  const sendMessage = button(document, "Send to room", "community-message-send", true);
  const messageState = status(document, "A persisted real message may earn server-verified Glow. DEMO messages never do.");
  conversation.append(messageList, messageInput, sendMessage, messageState);
  sendMessage.addEventListener("click", async () => {
    if (!messageInput.value.trim()) return;
    sendMessage.disabled = true;
    try {
      const saved = await api.postCommunityMessage(roomId, messageInput.value.trim(), document.documentElement.lang || "en");
      messageState.textContent = saved.glow?.status === "AWARDED" ? `Persisted · +${saved.glow.awarded_points} Glow` : "Persisted in the bounded room.";
      messageState.className = "nur-adjunct-status is-good";
      await renderCommunityRoom(document, api, roomId);
    } catch (error) {
      messageState.textContent = error instanceof Error ? error.message : "Message was not saved.";
      messageState.className = "nur-adjunct-status is-warn";
      sendMessage.disabled = false;
    }
  });

  const threads = panel(document, "Room threads", `Posts · ${posts.length}`);
  const threadList = element(document, "div", "nur-adjunct-list");
  for (const post of posts) {
    const item = element(document, "article", "nur-adjunct-row");
    const head = element(document, "div", "nur-adjunct-row-head");
    head.append(element(document, "strong", undefined, post.title), element(document, "span", "nur-adjunct-chip", post.is_demo ? "DEMO" : post.provenance_label));
    item.append(head, element(document, "p", undefined, post.body));
    const open = button(document, "Open thread", `community-post-${post.id}`);
    open.addEventListener("click", () => navigate(`/community/post/${post.id}?room=${roomId}`));
    item.append(open);
    threadList.append(item);
  }
  const postTitle = element(document, "input", "nur-adjunct-input") as HTMLInputElement;
  postTitle.placeholder = "Thread title";
  const postBody = element(document, "textarea", "nur-adjunct-textarea") as HTMLTextAreaElement;
  postBody.placeholder = "Question, lived experience, resource, outcome or Project log…";
  const publish = button(document, "Publish in room", "community-post-create", true);
  const postState = status(document, "Only room members can read this thread.");
  threads.append(threadList, postTitle, postBody, publish, postState);
  publish.addEventListener("click", async () => {
    if (!postTitle.value.trim() || !postBody.value.trim()) {
      postState.textContent = "A thread needs both title and body.";
      postState.className = "nur-adjunct-status is-warn";
      return;
    }
    publish.disabled = true;
    try {
      const saved = await api.createCommunityPost(roomId, postTitle.value.trim(), postBody.value.trim(), document.documentElement.lang || "en");
      navigate(`/community/post/${saved.id}?room=${roomId}`);
    } catch (error) {
      postState.textContent = error instanceof Error ? error.message : "Thread was not published.";
      postState.className = "nur-adjunct-status is-warn";
      publish.disabled = false;
    }
  });
  grid.append(boundary, conversation, threads);
}

async function renderCommunityPost(document: Document, api: V197ApiClient, postId: string): Promise<void> {
  const requestedRoom = new URL(window.location.href).searchParams.get("room");
  const rooms = await api.communityRooms();
  let roomId = requestedRoom;
  let post: V197CommunityPost | undefined;
  if (roomId) post = (await api.communityPosts(roomId)).find(row => row.id === postId);
  if (!post) {
    for (const room of rooms) {
      const found = (await api.communityPosts(room.id)).find(row => row.id === postId);
      if (found) { post = found; roomId = room.id; break; }
    }
  }
  if (!post || !roomId) throw new Error("This thread is not available inside your room memberships.");
  const comments = await api.communityComments(roomId, postId);
  const shell = mount(document, post.title, post.body, `/community/room/${roomId}`);
  const grid = element(document, "div", "nur-adjunct-grid");
  shell.append(grid);
  const thread = panel(document, "Bounded thread", `${post.is_demo ? "DEMO · " : ""}${post.provenance_label}`);
  thread.classList.add("is-wide");
  thread.append(element(document, "p", undefined, post.body));
  const reactions = element(document, "div", "nur-adjunct-actions");
  const useful = button(document, "✦ Useful", "community-react-useful");
  const witness = button(document, "Witness", "community-react-witness");
  const reactionState = status(document, "Reactions are unique persisted room records.");
  const react = async (reaction: string) => {
    useful.disabled = true; witness.disabled = true;
    try {
      await api.createCommunityReaction(roomId!, "POST", postId, reaction);
      reactionState.textContent = `${reaction} reaction persisted.`;
      reactionState.className = "nur-adjunct-status is-good";
    } catch (error) {
      reactionState.textContent = error instanceof Error ? error.message : "Reaction failed.";
      reactionState.className = "nur-adjunct-status is-warn";
    }
  };
  useful.addEventListener("click", () => void react("USEFUL"));
  witness.addEventListener("click", () => void react("WITNESS"));
  reactions.append(useful, witness);
  thread.append(reactions, reactionState);

  const discussion = panel(document, "Discussion", `Replies · ${comments.length}`);
  discussion.classList.add("is-wide");
  const list = element(document, "div", "nur-adjunct-list");
  if (!comments.length) list.append(empty(document, "No reply yet", "No fabricated person is waiting here."));
  for (const comment of comments) {
    const row = element(document, "article", "nur-adjunct-row");
    row.append(element(document, "span", "nur-adjunct-chip", comment.is_demo ? "DEMO" : "MEMBER_WRITTEN"), element(document, "p", undefined, comment.body));
    list.append(row);
  }
  const reply = element(document, "textarea", "nur-adjunct-textarea") as HTMLTextAreaElement;
  reply.placeholder = "Reply with experience, evidence, constraint or disagreement…";
  const send = button(document, "Reply", "community-comment-create", true);
  const replyState = status(document, "The reply remains inside this room thread.");
  discussion.append(list, reply, send, replyState);
  send.addEventListener("click", async () => {
    if (!reply.value.trim()) return;
    send.disabled = true;
    try {
      const saved = await api.createCommunityComment(roomId!, postId, reply.value.trim(), document.documentElement.lang || "en");
      replyState.textContent = saved.glow?.status === "AWARDED" ? `Reply persisted · +${saved.glow.awarded_points} Glow` : "Reply persisted.";
      replyState.className = "nur-adjunct-status is-good";
      await renderCommunityPost(document, api, postId);
    } catch (error) {
      replyState.textContent = error instanceof Error ? error.message : "Reply was not saved.";
      replyState.className = "nur-adjunct-status is-warn";
      send.disabled = false;
    }
  });
  grid.append(thread, discussion);
}

async function renderProjectsIndex(document: Document, api: V197ApiClient): Promise<void> {
  const projects = await api.projects();
  const shell = mount(document, "Intent becomes evidence, then a shipped result.", "AM Projects keeps objective, tasks, bounded agent proposals, evidence, reviews and owner approval in one Project Orbit.");
  const grid = element(document, "div", "nur-adjunct-grid");
  shell.append(grid);
  const ledger = panel(document, "Owner Project ledger", `Projects · ${projects.length}`);
  const list = element(document, "div", "nur-adjunct-list");
  if (!projects.length) list.append(empty(document, "No Project yet", "Create one objective. No agent gets authority merely because a card exists."));
  for (const project of projects) {
    const row = element(document, "article", "nur-adjunct-row");
    const head = element(document, "div", "nur-adjunct-row-head");
    head.append(element(document, "strong", undefined, text(project.title)), element(document, "span", "nur-adjunct-chip", text(project.status)));
    row.append(head, element(document, "p", undefined, text(project.objective)));
    const open = button(document, "Open Project Orbit", `project-open-${recordId(project)}`);
    open.addEventListener("click", () => navigate(`/projects/${recordId(project)}/overview`));
    row.append(open);
    list.append(row);
  }
  ledger.append(list);

  const create = panel(document, "New Project Orbit", "Define what done means");
  const title = element(document, "input", "nur-adjunct-input") as HTMLInputElement;
  title.placeholder = "Project title";
  const objective = element(document, "textarea", "nur-adjunct-textarea") as HTMLTextAreaElement;
  objective.placeholder = "Objective and success definition…";
  const system = element(document, "select", "nur-adjunct-select") as HTMLSelectElement;
  for (const value of ["quiet-ambition", "rebuild", "study", "money", "body", "connection", "creation"]) {
    const option = element(document, "option", undefined, value.replaceAll("-", " ")) as HTMLOptionElement;
    option.value = value;
    system.append(option);
  }
  const createButton = button(document, "Create Project Orbit", "project-create", true);
  const createState = status(document, "External actions remain denied until an owner explicitly approves a bounded run.");
  create.append(title, objective, system, createButton, createState);
  createButton.addEventListener("click", async () => {
    if (!title.value.trim() || !objective.value.trim()) {
      createState.textContent = "A Project needs a title and objective.";
      createState.className = "nur-adjunct-status is-warn";
      return;
    }
    createButton.disabled = true;
    try {
      const created = await api.createProject({ title: title.value.trim(), objective: objective.value.trim(), system_slug: system.value });
      navigate(`/projects/${recordId(created)}/overview`);
    } catch (error) {
      createState.textContent = error instanceof Error ? error.message : "Project was not created.";
      createState.className = "nur-adjunct-status is-warn";
      createButton.disabled = false;
    }
  });
  grid.append(ledger, create);
}

async function renderProjectDetail(document: Document, api: V197ApiClient, projectId: string, route: string): Promise<void> {
  const [project, tasks, runs, evidence, reviews, artifacts] = await Promise.all([
    api.project(projectId), api.projectTasks(projectId), api.projectRuns(projectId),
    api.projectEvidence(projectId), api.projectReviews(projectId), api.projectArtifacts(projectId),
  ]);
  const shell = mount(document, text(project.title), text(project.objective), "/projects");
  const tabs = element(document, "nav", "nur-adjunct-actions");
  const tabNames = ["overview", "tasks", "evidence", "agents", "runs", "insights", "deliverables", "settings", "share"];
  for (const tab of tabNames) {
    const control = button(document, tab.replaceAll("-", " "), `project-tab-${tab}`, route.endsWith(`/${tab}`));
    control.addEventListener("click", () => navigate(`/projects/${projectId}/${tab}`));
    tabs.append(control);
  }
  shell.append(tabs);
  const grid = element(document, "div", "nur-adjunct-grid");
  shell.append(grid);

  const state = panel(document, "Project Orbit", `${text(project.status)} · ${text(project.system_slug, "unassigned system")}`);
  state.classList.add("is-wide");
  const facts = element(document, "div", "nur-adjunct-facts");
  facts.append(fact(document, "Tasks", text(tasks.length)), fact(document, "Passed evidence", text(evidence.filter(row => row.verification_status === "PASSED").length)), fact(document, "Agent proposals", text(runs.length)), fact(document, "Owner reviews", text(reviews.length)));
  state.append(facts, element(document, "p", "nur-adjunct-boundary", "No run can pre-authorize spending, publishing, deployment, messaging, secret access or security changes."));

  const taskPanel = panel(document, "Execution", `Tasks · ${tasks.length}`);
  const taskList = element(document, "div", "nur-adjunct-list");
  for (const task of tasks) {
    const row = element(document, "article", "nur-adjunct-row");
    const head = element(document, "div", "nur-adjunct-row-head");
    head.append(element(document, "strong", undefined, text(task.title)), element(document, "span", "nur-adjunct-chip", text(task.status)));
    row.append(head, element(document, "p", undefined, text(task.acceptance_criteria, "Acceptance criteria not set")));
    if (task.status !== "DONE") {
      const done = button(document, "Close with passed evidence", `project-task-done-${recordId(task)}`);
      done.addEventListener("click", async () => {
        try {
          await api.patchProjectTask(recordId(task), { status: "DONE" });
          await renderProjectDetail(document, api, projectId, route);
        } catch (error) {
          const note = status(document, error instanceof Error ? error.message : "Task completion was rejected.", "warn");
          row.append(note);
        }
      });
      row.append(done);
    }
    taskList.append(row);
  }
  const taskTitle = element(document, "input", "nur-adjunct-input") as HTMLInputElement;
  taskTitle.placeholder = "One concrete task";
  const criteria = element(document, "input", "nur-adjunct-input") as HTMLInputElement;
  criteria.placeholder = "Acceptance criteria";
  const addTask = button(document, "Add task", "project-task-create", true);
  const taskState = status(document, "A task cannot become DONE without PASSED evidence.");
  taskPanel.append(taskList, taskTitle, criteria, addTask, taskState);
  addTask.addEventListener("click", async () => {
    if (!taskTitle.value.trim() || !criteria.value.trim()) return;
    addTask.disabled = true;
    try {
      await api.createProjectTask(projectId, { title: taskTitle.value.trim(), acceptance_criteria: criteria.value.trim(), assigned_role: "implementer" });
      await renderProjectDetail(document, api, projectId, route);
    } catch (error) {
      taskState.textContent = error instanceof Error ? error.message : "Task was not created.";
      taskState.className = "nur-adjunct-status is-warn";
      addTask.disabled = false;
    }
  });

  const proof = panel(document, "Evidence gate", `Evidence · ${evidence.length}`);
  const proofList = element(document, "div", "nur-adjunct-list");
  for (const item of evidence) {
    const row = element(document, "article", "nur-adjunct-row");
    row.append(element(document, "span", "nur-adjunct-chip", text(item.verification_status)), element(document, "p", undefined, text(item.summary)));
    proofList.append(row);
  }
  const proofSummary = element(document, "textarea", "nur-adjunct-textarea") as HTMLTextAreaElement;
  proofSummary.placeholder = "What was verified?";
  const proofLocator = element(document, "input", "nur-adjunct-input") as HTMLInputElement;
  proofLocator.placeholder = "Evidence locator/path/URL";
  const taskSelect = element(document, "select", "nur-adjunct-select") as HTMLSelectElement;
  taskSelect.append(element(document, "option", undefined, "Project-level evidence"));
  taskSelect.options[0].value = "";
  for (const task of tasks) {
    const option = element(document, "option", undefined, text(task.title)) as HTMLOptionElement;
    option.value = recordId(task);
    taskSelect.append(option);
  }
  const addEvidence = button(document, "Record passed evidence", "project-evidence-create", true);
  const proofState = status(document, "PASSED evidence requires both a named verifier and a locator.");
  proof.append(proofList, taskSelect, proofSummary, proofLocator, addEvidence, proofState);
  addEvidence.addEventListener("click", async () => {
    if (!proofSummary.value.trim() || !proofLocator.value.trim()) return;
    addEvidence.disabled = true;
    try {
      const saved = await api.createProjectEvidence(projectId, {
        task_id: taskSelect.value || null, evidence_kind: "TEST_OUTPUT",
        summary: proofSummary.value.trim(), locator: proofLocator.value.trim(),
        verification_status: "PASSED", verifier: "OWNER",
      });
      const glow = saved.glow as Record<string, unknown> | undefined;
      proofState.textContent = glow?.status === "AWARDED" ? `Evidence persisted · +${text(glow.awarded_points, "0")} Glow` : "Evidence persisted.";
      await renderProjectDetail(document, api, projectId, route);
    } catch (error) {
      proofState.textContent = error instanceof Error ? error.message : "Evidence was not recorded.";
      proofState.className = "nur-adjunct-status is-warn";
      addEvidence.disabled = false;
    }
  });

  const agent = panel(document, "Bounded agent work", `Runs · ${runs.length}`);
  const runList = element(document, "div", "nur-adjunct-list");
  for (const run of runs) {
    const row = element(document, "article", "nur-adjunct-row");
    const head = element(document, "div", "nur-adjunct-row-head");
    head.append(element(document, "strong", undefined, text(run.role)), element(document, "span", "nur-adjunct-chip", text(run.status)));
    row.append(head, element(document, "p", undefined, text(run.request_summary)));
    if (run.status === "PROPOSED") {
      const actions = element(document, "div", "nur-adjunct-actions");
      const approve = button(document, "Approve bounded run", `project-run-approve-${recordId(run)}`, true);
      const cancel = button(document, "Cancel", `project-run-cancel-${recordId(run)}`);
      approve.addEventListener("click", async () => { await api.projectRunAction(recordId(run), "approve"); await renderProjectDetail(document, api, projectId, route); });
      cancel.addEventListener("click", async () => { await api.projectRunAction(recordId(run), "cancel"); await renderProjectDetail(document, api, projectId, route); });
      actions.append(approve, cancel); row.append(actions);
    }
    runList.append(row);
  }
  const role = element(document, "select", "nur-adjunct-select") as HTMLSelectElement;
  for (const value of ["architect", "implementer", "researcher", "visual reviewer", "QA", "security reviewer", "writer", "translator"]) {
    const option = element(document, "option", undefined, value) as HTMLOptionElement; option.value = value; role.append(option);
  }
  const request = element(document, "textarea", "nur-adjunct-textarea") as HTMLTextAreaElement;
  request.placeholder = "Propose a scoped task. This records intent; it does not execute autonomously.";
  const propose = button(document, "Propose agent run", "project-run-propose", true);
  const runState = status(document, "Owner approval changes PROPOSED to APPROVED. It still does not grant external action authority.");
  agent.append(runList, role, request, propose, runState);
  propose.addEventListener("click", async () => {
    if (!request.value.trim()) return;
    propose.disabled = true;
    try {
      await api.proposeProjectRun(projectId, { role: role.value, request_summary: request.value.trim(), task_id: tasks.length ? recordId(tasks[0]) : null });
      await renderProjectDetail(document, api, projectId, route);
    } catch (error) {
      runState.textContent = error instanceof Error ? error.message : "Run proposal failed.";
      runState.className = "nur-adjunct-status is-warn";
      propose.disabled = false;
    }
  });

  const review = panel(document, "Owner review", `Reviews · ${reviews.length} · Artifacts · ${artifacts.length}`);
  const reviewList = element(document, "div", "nur-adjunct-list");
  for (const item of reviews) {
    const row = element(document, "article", "nur-adjunct-row");
    row.append(element(document, "span", "nur-adjunct-chip", text(item.decision)), element(document, "p", undefined, text(item.note, "No note")));
    reviewList.append(row);
  }
  const reviewNote = element(document, "textarea", "nur-adjunct-textarea") as HTMLTextAreaElement;
  reviewNote.placeholder = "Why is this accepted, rejected or corrected?";
  const approveReview = button(document, "Record owner approval", "project-review-create", true);
  const reviewState = status(document, "Review records judgment; it does not rewrite evidence.");
  review.append(reviewList, reviewNote, approveReview, reviewState);
  approveReview.addEventListener("click", async () => {
    if (!reviewNote.value.trim()) return;
    approveReview.disabled = true;
    try {
      await api.createProjectReview(projectId, { decision: "APPROVE", note: reviewNote.value.trim() });
      await renderProjectDetail(document, api, projectId, route);
    } catch (error) {
      reviewState.textContent = error instanceof Error ? error.message : "Review was not saved.";
      reviewState.className = "nur-adjunct-status is-warn";
      approveReview.disabled = false;
    }
  });
  grid.append(state, taskPanel, proof, agent, review);
}

function renderGlow(document: Document, snapshot: V197BridgeSnapshot): void {
  const glow = snapshot.glow;
  const shell = mount(document, "Movement becomes visible light.", "Glow is a persisted, source-linked economy. Points appear only after a server-verified action; caps, idempotency and DEMO gates remain active.");
  const grid = element(document, "div", "nur-adjunct-grid");
  shell.append(grid);
  const level = panel(document, "Current constellation", `${glow.rank} · Level ${glow.level}`);
  level.classList.add("is-wide");
  const facts = element(document, "div", "nur-adjunct-facts");
  facts.append(fact(document, "Available Glow", text(glow.balance)), fact(document, "Lifetime", text(glow.lifetime_points)), fact(document, "Today", text(glow.today_points)), fact(document, "This week", text(glow.weekly_points)));
  level.append(facts);
  if (glow.next_unlock) {
    const remaining = text((glow.next_unlock as Record<string, unknown>).points_remaining, "0");
    const rank = text((glow.next_unlock as Record<string, unknown>).rank, "next constellation");
    level.append(status(document, `${remaining} source-linked Glow until ${rank}.`));
  } else level.append(status(document, "Current configured constellation reached.", "good"));

  const quests = panel(document, "Return tension", "Quests and mission");
  const questRows = [glow.daily_quest, glow.weekly_mission].filter(Boolean) as Array<Record<string, unknown>>;
  const questList = element(document, "div", "nur-adjunct-list");
  for (const quest of questRows) {
    const row = element(document, "article", "nur-adjunct-row");
    const head = element(document, "div", "nur-adjunct-row-head");
    head.append(element(document, "strong", undefined, text(quest.title)), element(document, "span", "nur-adjunct-chip", quest.completed ? "RETURNED" : `${text(quest.progress, "0")}/${text(quest.target, "1")}`));
    row.append(head);
    questList.append(row);
  }
  if (!questRows.length) questList.append(empty(document, "No active quest", "NUR will not invent progress."));
  quests.append(questList);

  const streaks = panel(document, "Continuity", `Streaks · ${glow.streaks.length}`);
  const streakList = element(document, "div", "nur-adjunct-list");
  for (const streak of glow.streaks) {
    const row = element(document, "article", "nur-adjunct-row");
    const head = element(document, "div", "nur-adjunct-row-head");
    head.append(element(document, "strong", undefined, streak.streak_key.replaceAll("_", " ")), element(document, "span", "nur-adjunct-chip", `${streak.current_count} current · ${streak.best_count} best`));
    row.append(head, element(document, "p", undefined, streak.repairs_remaining ? `${streak.repairs_remaining} recovery token${streak.repairs_remaining === 1 ? "" : "s"}` : "No recovery token recorded"));
    streakList.append(row);
  }
  if (!glow.streaks.length) streakList.append(empty(document, "No streak yet", "One eligible persisted action starts continuity."));
  streaks.append(streakList);

  const ledger = panel(document, "Source-linked ledger", `Recent Glow · ${glow.recent_transactions.length}`);
  ledger.classList.add("is-wide");
  const transactionList = element(document, "div", "nur-adjunct-list");
  for (const transaction of glow.recent_transactions) {
    const row = element(document, "article", "nur-adjunct-row");
    const head = element(document, "div", "nur-adjunct-row-head");
    head.append(element(document, "strong", undefined, transaction.reason), element(document, "span", "nur-adjunct-chip", `+${transaction.final_points}`));
    row.append(head, element(document, "p", undefined, `${transaction.event_type} · ${date(transaction.created_at)}`));
    transactionList.append(row);
  }
  if (!glow.recent_transactions.length) transactionList.append(empty(document, "No transaction yet", "No points are displayed without persisted proof."));
  ledger.append(transactionList);
  grid.append(level, quests, streaks, ledger);
}

async function renderNotifications(document: Document, api: V197ApiClient): Promise<void> {
  const [preferences, notifications] = await Promise.all([api.notificationPreferences(), api.notifications()]);
  const shell = mount(document, "Return cues, under your control.", "NUR notifications are owner-scoped and factual. There are no fabricated replies, fake urgency or hidden external delivery channels.");
  const grid = element(document, "div", "nur-adjunct-grid");
  shell.append(grid);
  const inbox = panel(document, "In-app ledger", `Notifications · ${notifications.length}`);
  const list = element(document, "div", "nur-adjunct-list");
  if (!notifications.length) list.append(empty(document, "Nothing is demanding your attention", "NUR will not manufacture a social obligation."));
  for (const notification of notifications) {
    const row = element(document, "article", "nur-adjunct-row");
    const head = element(document, "div", "nur-adjunct-row-head");
    head.append(element(document, "strong", undefined, text(notification.title)), element(document, "span", "nur-adjunct-chip", `${notification.is_demo ? "DEMO · " : ""}${text(notification.category)}`));
    row.append(head, element(document, "p", undefined, text(notification.body)));
    const actions = element(document, "div", "nur-adjunct-actions");
    if (notification.route) {
      const open = button(document, "Open", `notification-open-${recordId(notification)}`);
      open.addEventListener("click", () => navigate(text(notification.route, "/today")));
      actions.append(open);
    }
    if (!notification.read_at) {
      const read = button(document, "Mark read", `notification-read-${recordId(notification)}`);
      read.addEventListener("click", async () => { await api.markNotificationRead(recordId(notification)); await renderNotifications(document, api); });
      actions.append(read);
    }
    row.append(actions);
    list.append(row);
  }
  inbox.append(list);

  const controls = panel(document, "Delivery boundary", "Frequency and quiet hours");
  const frequency = element(document, "select", "nur-adjunct-select") as HTMLSelectElement;
  frequency.dataset.adjunctControl = "notification-frequency";
  for (const value of ["QUIET", "BALANCED", "ACTIVE"]) {
    const option = element(document, "option", undefined, value.toLowerCase()) as HTMLOptionElement;
    option.value = value; option.selected = value === preferences.frequency; frequency.append(option);
  }
  const quietStart = element(document, "input", "nur-adjunct-input") as HTMLInputElement;
  quietStart.dataset.adjunctControl = "notification-quiet-start";
  quietStart.type = "time"; quietStart.value = text(preferences.quiet_hours_start, "");
  const quietEnd = element(document, "input", "nur-adjunct-input") as HTMLInputElement;
  quietEnd.dataset.adjunctControl = "notification-quiet-end";
  quietEnd.type = "time"; quietEnd.value = text(preferences.quiet_hours_end, "");
  const save = button(document, "Save notification boundary", "notification-preferences-save", true);
  const preferenceState = status(document, `${text(preferences.delivery_status, "IN_APP_ONLY")} · external push is not claimed.`);
  controls.append(frequency, quietStart, quietEnd, save, preferenceState);
  save.addEventListener("click", async () => {
    save.disabled = true;
    try {
      await api.patchNotificationPreferences({ category_settings: preferences.category_settings ?? {}, frequency: frequency.value, quiet_hours_start: quietStart.value || null, quiet_hours_end: quietEnd.value || null, push_enabled: false, email_enabled: false });
      preferenceState.textContent = "Notification boundary persisted.";
      preferenceState.className = "nur-adjunct-status is-good";
    } catch (error) {
      preferenceState.textContent = error instanceof Error ? error.message : "Preferences were not saved.";
      preferenceState.className = "nur-adjunct-status is-warn";
      save.disabled = false;
    }
  });

  const reminder = panel(document, "Owner reminder", "Create one truthful re-entry cue");
  const title = element(document, "input", "nur-adjunct-input") as HTMLInputElement;
  title.dataset.adjunctControl = "notification-title";
  title.placeholder = "What should return?";
  const body = element(document, "textarea", "nur-adjunct-textarea") as HTMLTextAreaElement;
  body.dataset.adjunctControl = "notification-body";
  body.placeholder = "Why will this still matter?";
  const route = element(document, "input", "nur-adjunct-input") as HTMLInputElement;
  route.dataset.adjunctControl = "notification-route";
  route.placeholder = "/plan";
  const create = button(document, "Create in-app reminder", "notification-reminder-create", true);
  const reminderState = status(document, "This creates a real owner-written reminder, not a fake human ping.");
  reminder.append(title, body, route, create, reminderState);
  create.addEventListener("click", async () => {
    if (!title.value.trim() || !body.value.trim()) return;
    create.disabled = true;
    try {
      await api.createReminder({ category: "PROGRESS", title: title.value.trim(), body: body.value.trim(), route: route.value.trim() || "/today" });
      await renderNotifications(document, api);
    } catch (error) {
      reminderState.textContent = error instanceof Error ? error.message : "Reminder was not created.";
      reminderState.className = "nur-adjunct-status is-warn";
      create.disabled = false;
    }
  });
  grid.append(inbox, controls, reminder);
}

function renderError(document: Document, error: unknown, backRoute = "/systems"): void {
  const shell = mount(document, "This chamber could not open.", "NUR kept the boundary closed instead of inventing data.", backRoute);
  const grid = element(document, "div", "nur-adjunct-grid");
  const errorPanel = panel(document, "Honest runtime state", "No fabricated fallback");
  errorPanel.classList.add("is-wide");
  errorPanel.append(status(document, error instanceof Error ? error.message : "The requested owner data is unavailable.", "warn"));
  grid.append(errorPanel);
  shell.append(grid);
}

export async function renderV197Adjunct(
  document: Document,
  route: string,
  api: V197ApiClient,
  snapshot: V197BridgeSnapshot,
  refreshSnapshot: RefreshSnapshot,
): Promise<boolean> {
  const existing = document.getElementById(ROOT_ID);
  const isAdjunct = route === "/settings"
    || route.startsWith("/capsule/")
    || route === "/consultations"
    || route.startsWith("/consultations/")
    || route === "/community"
    || route.startsWith("/community/")
    || route === "/projects"
    || route.startsWith("/projects/")
    || route === "/glow"
    || route === "/notifications"
    || route === "/universe/omega"
    || route === "/universe/omega/review"
    || route.startsWith("/universe/omega/why-changed/");
  if (!isAdjunct) {
    existing?.remove();
    return false;
  }

  try {
    if (route === "/settings") await renderSettings(document, api, snapshot, refreshSnapshot);
    else if (route.startsWith("/capsule/")) await renderCapsule(document, api, decodeURIComponent(route.slice("/capsule/".length)));
    else if (route === "/consultations") await renderConsultationIndex(document, api, snapshot);
    else if (route.startsWith("/consultations/")) await renderConsultationDetail(document, api, decodeURIComponent(route.split("/")[2] ?? ""));
    else if (route.startsWith("/community/room/")) await renderCommunityRoom(document, api, decodeURIComponent(route.split("/")[3] ?? ""));
    else if (route.startsWith("/community/post/")) await renderCommunityPost(document, api, decodeURIComponent(route.split("/")[3] ?? ""));
    else if (route === "/community" || route.startsWith("/community/")) await renderCommunityIndex(document, api, route);
    else if (route === "/projects" || route === "/projects/new") await renderProjectsIndex(document, api);
    else if (route.startsWith("/projects/")) await renderProjectDetail(document, api, decodeURIComponent(route.split("/")[2] ?? ""), route);
    else if (route === "/glow") renderGlow(document, snapshot);
    else if (route === "/notifications") await renderNotifications(document, api);
    else if (route === "/universe/omega/review") await renderOmegaReview(document, api);
    else if (route.startsWith("/universe/omega/why-changed/")) await renderOmegaWhyChanged(document, api, decodeURIComponent(route.slice("/universe/omega/why-changed/".length)));
    else await renderOmegaDashboard(document, api);
  } catch (error) {
    renderError(document, error, route.startsWith("/universe/omega") ? "/universe/omega" : "/systems");
  }
  return true;
}
