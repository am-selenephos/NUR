import type { LoginRequest, MeResponse, RegisterRequest } from "@nur/shared-types";

const BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function readCookie(name: string): string | null {
  const m = document.cookie.match(new RegExp("(?:^|; )" + name + "=([^;]*)"));
  return m ? decodeURIComponent(m[1]) : null;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const method = (init.method ?? "GET").toUpperCase();
  const headers = new Headers(init.headers);
  if (init.body) headers.set("Content-Type", "application/json");
  // CSRF double-submit: echo the readable cookie on state-changing verbs.
  if (method !== "GET" && method !== "HEAD") {
    const csrf = readCookie("nur_csrf");
    if (csrf) headers.set("X-CSRF-Token", csrf);
  }
  const res = await fetch(BASE + path, { ...init, method, headers, credentials: "include" });
  if (res.status === 204) return undefined as T;
  const text = await res.text();
  const data = text ? JSON.parse(text) : undefined;
  if (!res.ok) throw new ApiError(res.status, data?.detail ?? `Request failed (${res.status})`);
  return data as T;
}

export const api = {
  me: () => request<MeResponse>("/api/v1/auth/me"),
  register: (body: RegisterRequest) =>
    request<MeResponse>("/api/v1/auth/register", { method: "POST", body: JSON.stringify(body) }),
  login: (body: LoginRequest) =>
    request<{ ok: boolean }>("/api/v1/auth/login", { method: "POST", body: JSON.stringify(body) }),
  logout: () => request<void>("/api/v1/auth/logout", { method: "POST" }),
};

/* ——— Gate 2/3 client surface (all real endpoints; nothing simulated) ——— */
export type CycleRef = { kind: string; id: string; excerpt: string; rank: number };
export type Cycle = {
  trigger_event_id: string; retrieved: CycleRef[]; gateway: string;
  gateway_available: boolean; gateway_reason: string;
  evaluation_event_id: string | null; proposals: unknown[];
};
export type CognitiveEventRow = {
  id: string;
  event_kind: string;
  content_text: string | null;
  structured_payload: Record<string, unknown>;
  orbit_id: string | null;
  scope: string;
  parent_event_id: string | null;
  created_at: string;
};
export type EventWithCycle = { event: CognitiveEventRow; cycle: Cycle | null };
export type NURTalkOutput = {
  direct_response: string;
  observed: string[];
  inferred: string[];
  hypotheses: string[];
  uncertainty: string[];
  next_move: string | null;
  memory_candidates: string[];
  source_refs: string[];
};
export type TalkTurnResponse = {
  turn_event_id: string;
  response_event_id: string;
  model_run_id: string;
  provider: string;
  provider_available: boolean;
  provider_reason: string | null;
  output: NURTalkOutput;
  evidence: { retrieval: CycleRef[]; withheld: unknown[] };
  verification: { verdict: string; checks: Record<string, unknown> };
  omega?: OmegaTalkSummary | null;
};
export type TalkThreadRow = {
  id: string;
  who: "user" | "nur";
  text: string | null;
  structured_payload: Record<string, unknown>;
  created_at: string;
};
export type JournalRow = { id: string; body: string; created_at: string };
export type StepRow = { id: string; title: string; body: string | null; position: number; done: boolean; done_at: string | null };
export type PlanRow = { id: string; title: string; status: string; steps: StepRow[] };
export type ResearchRow = { id: string; question: string; status: string; created_at: string };
export type ResearchBriefRow = {
  id: string;
  owner_user_id: string;
  orbit_id: string | null;
  question: string;
  summary: string | null;
  status: string;
  provider_status: string;
  provenance_label: string;
  created_at: string;
  updated_at: string;
};
export type ResearchSourceNoteRow = {
  id: string;
  owner_user_id: string;
  orbit_id: string | null;
  research_brief_id: string | null;
  title: string;
  note: string;
  url: string | null;
  source_type: string;
  trust_state: string;
  provenance_label: string;
  created_at: string;
  updated_at: string;
};
export type CommunityNoteRow = {
  id: string;
  owner_user_id: string;
  orbit_id: string | null;
  title: string;
  note: string;
  collaborator_label: string | null;
  capsule_id: string | null;
  status: string;
  provenance_label: string;
  created_at: string;
  updated_at: string;
};
export type WebSignalQuestionRow = {
  id: string;
  owner_user_id: string;
  orbit_id: string | null;
  question: string;
  status: string;
  provider_status: string;
  provenance_label: string;
  created_at: string;
  updated_at: string;
};
export type WebSignalNoteRow = {
  id: string;
  owner_user_id: string;
  orbit_id: string | null;
  web_signal_question_id: string | null;
  title: string;
  note: string;
  url: string | null;
  provenance_label: string;
  created_at: string;
  updated_at: string;
};
export type ProviderCapabilityRow = {
  id: string;
  provider_name: string;
  capability_key: string;
  status: string;
  reason: string;
  configured: boolean;
  created_at: string;
  updated_at: string;
};
export type OrbitRow = { id: string; title: string; kind: string; description: string | null; status: string };
export type OrbitStateRow = {
  active_systems: number;
  outcomes_returned: number;
  insights_evolving: number;
  open_questions: number;
  research_staged: number;
  plans_active: number;
  live_status: "owner_ledger" | string;
};
export type DecisionRow = { id: string; statement: string; rationale: string | null; created_at: string };
export type ReferenceRow = { id: string; title: string; body: string | null; kind: string; created_at: string };
export type SourceRow = { id: string; source_kind: string; source_id: string; inclusion_mode: string };
export type CapsuleRowT = { id: string; orbit_id: string; title: string; purpose: string; capability: string; expires_at: string | null; revoked_at: string | null; version: number; created_at: string };
export type GrantRowT = { id: string; recipient_user_id: string | null; capability: string; last_accessed_at: string | null };
export type IncludedSourceT = { source_id: string; source_kind: string; representation: string; title: string; body: string };
export type CapsuleViewT = {
  capsule_id: string; state: "ACTIVE" | "REVOKED" | "EXPIRED"; title: string; purpose: string;
  owner_display: string; capability: string; expires_at: string | null;
  recipient_instructions: string | null; safety_copy: string;
  included: IncludedSourceT[]; excluded_summary: { source_kind: string; count: number; note: string }[];
  grant_id: string | null;
};
export type AnswerT = { question: string; answer_text: string; answer_mode: string; source_refs: { source_kind: string; representation: string; source_id: string }[]; confidence: number | null; policy_explanation: string | null };
export type AuditRowT = { event_kind: string; created_at: string; meta: Record<string, unknown> };
export type OmegaTalkSummary = {
  enabled: boolean;
  workspace_frame_id: string | null;
  what_changed: string[];
  open_contradictions: string[];
  unresolved_predictions: string[];
  memory_note: string;
};
export type OmegaExperience = {
  id: string; event_kind: string; summary: string; provenance_label: string; sensitivity: string; created_at: string;
};
export type OmegaClaim = {
  id: string; claim_text: string; claim_type: string; truth_status: string; confidence: number;
  support_count: number; contradiction_count: number; created_at: string; updated_at: string;
};
export type OmegaEvidence = {
  id: string; claim_id: string; evidence_kind: string; evidence_id: string; relation: string; strength: number; note: string | null; created_at: string;
};
export type OmegaWhyChanged = {
  claim_id: string; claim_text: string; current_truth_status: string; current_confidence: number;
  changed_because: string[]; supporting_edges: string[]; contradicting_edges: string[]; unresolved_note: string | null;
};
export type OmegaContradiction = {
  id: string; claim_a_id: string; claim_b_id: string; status: string; severity: string; description: string; proposed_resolution: string | null; created_at: string;
};
export type OmegaPrediction = {
  id: string; prediction_text: string; expected_observation: string; confidence: number; status: string; outcome_id: string | null; created_at: string; resolved_at: string | null;
};
export type OmegaLearningProposal = {
  id: string; proposal_kind: string; description: string; evidence_summary: string; risk_level: string; status: string; approved_by_owner: boolean; created_at: string;
};
export type OmegaConsolidationRun = {
  id: string; run_kind: string; input_counts: Record<string, unknown>; created_claims: number; updated_claims: number;
  contradictions_found: number; predictions_resolved: number; proposals_created: number; status: string; created_at: string; completed_at: string | null;
};
export type OmegaReviewQueueItem = {
  id: string; orbit_id: string | null; experience_id: string | null; candidate_claim_text: string;
  candidate_claim_type: string; candidate_truth_status: string; sensitivity: string; reason: string;
  model_candidate: Record<string, unknown>; status: string; created_claim_id: string | null;
  reviewed_at: string | null; created_at: string; updated_at: string;
};
export type OmegaExport = {
  exported_at: string; owner_user_id: string; safety: Record<string, unknown>; counts: Record<string, number>;
  claims: OmegaClaim[]; contradictions: OmegaContradiction[]; predictions: OmegaPrediction[];
  consolidation_runs: OmegaConsolidationRun[]; learning_proposals: OmegaLearningProposal[];
  review_queue: OmegaReviewQueueItem[];
};
export type OmegaDashboard = {
  statuses: Record<string, string>;
  claims: OmegaClaim[];
  contradictions: OmegaContradiction[];
  predictions: OmegaPrediction[];
  consolidation_runs: OmegaConsolidationRun[];
  learning_proposals: OmegaLearningProposal[];
  recent_experiences: OmegaExperience[];
  review_queue: OmegaReviewQueueItem[];
};
export type ProfilePreferences = {
  locale: string | null;
  writing_preference: "default" | "roman" | "script" | string;
  sound_enabled: boolean;
  reduced_effects: boolean;
  default_boundary: string;
  active_orbit_id: string | null;
  omega_enabled: boolean;
  updated_at: string;
};
export type ConvertResult = {
  source_kind: string;
  source_id: string;
  target_kind: string;
  target_id: string;
  orbit_id: string;
  orbit_source_id: string;
};
export type UniverseSearchHit = {
  kind: string;
  id: string;
  label: string;
  excerpt: string | null;
  route: string;
  created_at: string;
  provenance_label: string;
};
export type MapSummary = {
  provenance_label: string;
  counts: { key: string; label: string; count: number }[];
  nodes: { id: string; title: string; kind: string; orbit_id: string | null; active: boolean; counts: Record<string, number> }[];
};
export type OrbitsSummary = {
  provenance_label: string;
  orbits: Array<OrbitRow & { created_at: string; counts: Record<string, number> }>;
};
export type TimelineSummary = {
  provenance_label: string;
  items: { id: string; kind: string; title: string; body: string; created_at: string; provenance_label: string; route: string }[];
};
export type InsightsSummary = {
  provenance_label: string;
  counts: Record<string, number>;
  claims: Record<string, unknown>[];
  contradictions: Record<string, unknown>[];
  predictions: Record<string, unknown>[];
  review_queue: Record<string, unknown>[];
};
export type OmegaSchedulerStatus = {
  enabled: boolean;
  scheduled_consolidation: boolean;
  interval_hours: number;
  worker_mode: string;
  last_consolidation_run_at: string | null;
  last_consolidation_status: string;
  provenance_label: string;
};

const J = JSON.stringify;
export const nur = {
  healthz: () => request<{ status: string; ai_provider: string }>("/healthz"),
  readyz: () => request<{ status: string; checks: Record<string, string> }>("/readyz"),
  metricsText: async () => {
    const res = await fetch(BASE + "/metrics", { credentials: "include" });
    if (!res.ok) throw new ApiError(res.status, `Metrics request failed (${res.status})`);
    return res.text();
  },
  talk: (message: string, orbit_id?: string, mode?: string, locale = navigator.language || "en", writing_preference = "default") =>
    request<TalkTurnResponse>("/api/v1/cognition/talk", { method: "POST", body: J({ message, orbit_id, mode, locale, writing_preference }) }),
  talkThread: (orbit_id?: string) =>
    request<TalkThreadRow[]>(`/api/v1/cognition/talk-thread${orbit_id ? `?orbit_id=${encodeURIComponent(orbit_id)}` : ""}`),
  talkTurn: (content_text: string, orbit_id?: string) =>
    request<EventWithCycle>("/api/v1/cognition/events", { method: "POST", body: J({ event_kind: "TALK_TURN", content_text, orbit_id }) }),
  listEvents: (kind?: string, limit = 80) =>
    request<CognitiveEventRow[]>(`/api/v1/cognition/events?limit=${limit}${kind ? `&kind=${encodeURIComponent(kind)}` : ""}`),
  createEvent: (event_kind: string, content_text: string, structured_payload: Record<string, unknown> = {}, orbit_id?: string, scope = "PRIVATE_ORBIT") =>
    request<EventWithCycle>("/api/v1/cognition/events", {
      method: "POST",
      body: J({ event_kind, content_text, structured_payload, orbit_id, scope }),
    }),
  keepJournal: (body: string) => request<JournalRow>("/api/v1/journal", { method: "POST", body: J({ body }) }),
  listJournal: () => request<JournalRow[]>("/api/v1/journal"),
  listPlans: () => request<PlanRow[]>("/api/v1/plans"),
  createPlan: (title: string, steps: { title: string; body?: string }[]) =>
    request<PlanRow>("/api/v1/plans", { method: "POST", body: J({ title, steps }) }),
  addPlanStep: (plan_id: string, title: string, body?: string) =>
    request<StepRow>(`/api/v1/plans/${plan_id}/steps`, { method: "POST", body: J({ title, body }) }),
  patchStep: (id: string, done: boolean) =>
    request<StepRow>(`/api/v1/plan-steps/${id}`, { method: "PATCH", body: J({ done }) }),
  stepOutcome: (plan_step_id: string, observed_result: string) =>
    request<{ id: string }>("/api/v1/outcomes", { method: "POST", body: J({ plan_step_id, observed_result }) }),
  correct: (correction_text: string, target_event_id?: string, reason?: string) =>
    request<{ id: string }>("/api/v1/cognition/corrections", {
      method: "POST",
      body: J({ correction_text, target_event_id, reason }),
    }),
  stageResearch: (question: string, notes?: string, orbit_id?: string) =>
    request<ResearchRow>("/api/v1/research-drafts", { method: "POST", body: J({ question, notes, orbit_id }) }),
  listResearch: () => request<ResearchRow[]>("/api/v1/research-drafts"),
  convertJournal: (id: string, orbit_id?: string, kind = "REFERENCE") =>
    request<ConvertResult>(`/api/v1/journal/${id}/convert`, { method: "POST", body: J({ orbit_id, kind }) }),
  convertResearch: (id: string, orbit_id?: string, kind = "OPEN_QUESTION") =>
    request<ConvertResult>(`/api/v1/research-drafts/${id}/convert`, { method: "POST", body: J({ orbit_id, kind }) }),
  listOrbits: () => request<OrbitRow[]>("/api/v1/orbits"),
  orbitState: () => request<OrbitStateRow>("/api/v1/orbits/current-state"),
  mapSummary: () => request<MapSummary>("/api/v1/universe/map-summary"),
  orbitsSummary: () => request<OrbitsSummary>("/api/v1/universe/orbits-summary"),
  timelineSummary: (limit = 80) => request<TimelineSummary>(`/api/v1/universe/timeline?limit=${limit}`),
  insightsSummary: () => request<InsightsSummary>("/api/v1/universe/insights-summary"),
  universeSearch: (q: string, limit = 8) =>
    request<UniverseSearchHit[]>(`/api/v1/universe/search?q=${encodeURIComponent(q)}&limit=${limit}`),
  getPreferences: () => request<ProfilePreferences>("/api/v1/profile/preferences"),
  patchPreferences: (body: Partial<Pick<ProfilePreferences, "locale" | "writing_preference" | "sound_enabled" | "reduced_effects" | "default_boundary" | "active_orbit_id" | "omega_enabled">>) =>
    request<ProfilePreferences>("/api/v1/profile/preferences", { method: "PATCH", body: J(body) }),
  listResearchBriefs: () => request<ResearchBriefRow[]>("/api/v1/research/briefs"),
  createResearchBrief: (question: string, summary?: string, orbit_id?: string) =>
    request<ResearchBriefRow>("/api/v1/research/briefs", { method: "POST", body: J({ question, summary, orbit_id }) }),
  createResearchSourceNote: (title: string, note: string, orbit_id?: string, research_brief_id?: string) =>
    request<ResearchSourceNoteRow>("/api/v1/research/source-notes", { method: "POST", body: J({ title, note, orbit_id, research_brief_id }) }),
  listResearchSourceNotes: () => request<ResearchSourceNoteRow[]>("/api/v1/research/source-notes"),
  convertResearchBrief: (id: string) =>
    request<ConvertResult>(`/api/v1/research/briefs/${id}/convert`, { method: "POST" }),
  listCommunityNotes: () => request<CommunityNoteRow[]>("/api/v1/community/consultation-notes"),
  createCommunityNote: (title: string, note: string, orbit_id?: string, collaborator_label?: string) =>
    request<CommunityNoteRow>("/api/v1/community/consultation-notes", { method: "POST", body: J({ title, note, orbit_id, collaborator_label }) }),
  listWebSignalQuestions: () => request<WebSignalQuestionRow[]>("/api/v1/web-signals/questions"),
  createWebSignalQuestion: (question: string, orbit_id?: string) =>
    request<WebSignalQuestionRow>("/api/v1/web-signals/questions", { method: "POST", body: J({ question, orbit_id }) }),
  listWebSignalNotes: () => request<WebSignalNoteRow[]>("/api/v1/web-signals/notes"),
  createWebSignalNote: (title: string, note: string, orbit_id?: string, web_signal_question_id?: string) =>
    request<WebSignalNoteRow>("/api/v1/web-signals/notes", { method: "POST", body: J({ title, note, orbit_id, web_signal_question_id }) }),
  attachWebSignalNote: (id: string) =>
    request<ConvertResult>(`/api/v1/web-signals/notes/${id}/attach`, { method: "POST" }),
  providerCapabilities: () => request<ProviderCapabilityRow[]>("/api/v1/provider-capabilities"),
  createOrbit: (title: string, description?: string) =>
    request<OrbitRow>("/api/v1/orbits", { method: "POST", body: J({ title, kind: "PROJECT", description }) }),
  listDecisions: (orbit: string) => request<DecisionRow[]>(`/api/v1/orbits/${orbit}/decisions`),
  addDecision: (orbit: string, statement: string, rationale?: string) =>
    request<DecisionRow>(`/api/v1/orbits/${orbit}/decisions`, { method: "POST", body: J({ statement, rationale }) }),
  listReferences: (orbit: string) => request<ReferenceRow[]>(`/api/v1/orbits/${orbit}/references`),
  addReference: (orbit: string, title: string, body?: string, kind = "REFERENCE") =>
    request<ReferenceRow>(`/api/v1/orbits/${orbit}/references`, { method: "POST", body: J({ title, body, kind }) }),
  listSources: (orbit: string) => request<SourceRow[]>(`/api/v1/orbits/${orbit}/sources`),
  attachSource: (orbit: string, source_kind: string, source_id: string) =>
    request<SourceRow>(`/api/v1/orbits/${orbit}/sources`, { method: "POST", body: J({ source_kind, source_id }) }),
  createCapsule: (orbit: string, payload: { title: string; purpose: string; capability: string; orbit_source_ids: string[]; representations: Record<string, string>; expires_at?: string | null }) =>
    request<CapsuleRowT>(`/api/v1/orbits/${orbit}/capsules`, { method: "POST", body: J(payload) }),
  myCapsules: () => request<CapsuleRowT[]>("/api/v1/capsules"),
  grantCapsule: (id: string, recipient_email: string, capability: string, expires_at?: string | null) =>
    request<GrantRowT>(`/api/v1/capsules/${id}/grants`, { method: "POST", body: J({ recipient_email, capability, expires_at }) }),
  revokeCapsule: (id: string) => request<CapsuleRowT>(`/api/v1/capsules/${id}/revoke`, { method: "POST" }),
  capsuleAudit: (id: string) => request<AuditRowT[]>(`/api/v1/capsules/${id}/audit`),
  capsuleView: (id: string) => request<CapsuleViewT>(`/api/v1/capsules/${id}/view`),
  askCapsule: (id: string, question: string) =>
    request<AnswerT>(`/api/v1/capsules/${id}/questions`, { method: "POST", body: J({ question }) }),
  omegaDashboard: () => request<OmegaDashboard>("/api/v1/omega/dashboard"),
  omegaClaimEvidence: (id: string) => request<OmegaEvidence[]>(`/api/v1/omega/claims/${id}/evidence`),
  omegaWhyChanged: (id: string) => request<OmegaWhyChanged>(`/api/v1/omega/claims/${id}/why-changed`),
  omegaExport: () => request<OmegaExport>("/api/v1/omega/export"),
  omegaSchedulerStatus: () => request<OmegaSchedulerStatus>("/api/v1/omega/scheduler-status"),
  omegaReviewQueue: () => request<OmegaReviewQueueItem[]>("/api/v1/omega/review-queue"),
  omegaReviewAction: (id: string, action: "approve" | "reject") =>
    request<OmegaReviewQueueItem>(`/api/v1/omega/review-queue/${id}/${action}`, { method: "POST" }),
  omegaReviewEdit: (id: string, candidate_claim_text: string, candidate_claim_type: string) =>
    request<OmegaReviewQueueItem>(`/api/v1/omega/review-queue/${id}/edit`, {
      method: "POST",
      body: J({ candidate_claim_text, candidate_claim_type }),
    }),
  omegaConsolidate: () => request<OmegaConsolidationRun>("/api/v1/omega/consolidate", { method: "POST", body: J({ run_kind: "MANUAL" }) }),
  omegaConfirmClaim: (id: string) => request<OmegaClaim>(`/api/v1/omega/claims/${id}/confirm`, { method: "POST" }),
  omegaRetireClaim: (id: string) => request<OmegaClaim>(`/api/v1/omega/claims/${id}/retire`, { method: "POST" }),
  omegaResolveContradiction: (id: string) =>
    request<OmegaContradiction>(`/api/v1/omega/contradictions/${id}/resolve`, { method: "POST", body: J({ status: "RESOLVED" }) }),
  omegaLearningAction: (id: string, action: "approve" | "reject" | "rollback") =>
    request<OmegaLearningProposal>(`/api/v1/omega/learning-proposals/${id}/${action}`, { method: "POST" }),
};
