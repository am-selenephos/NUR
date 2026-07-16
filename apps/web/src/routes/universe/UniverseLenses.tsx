import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import BidiText from "../../components/BidiText";
import ExactMiniStar from "../../components/ExactMiniStar";
import MasterStar from "../../components/MasterStar";
import NURWordmark from "../../components/NURWordmark";
import { useOrbit } from "../../lib/orbitState";
import { LOCALE_META, dirForLocale } from "../../lib/i18n";
import {
  nur,
  type CapsuleRowT,
  type CommunityNoteRow,
  type CognitiveEventRow,
  type DecisionRow,
  type OmegaDashboard,
  type OmegaEvidence,
  type OmegaWhyChanged,
  type OrbitRow,
  type OrbitStateRow,
  type ReferenceRow,
  type ResearchBriefRow,
  type ProfilePreferences,
  type SourceRow,
  type WebSignalQuestionRow,
} from "../../lib/api";
import AddSystemModal from "./shell/AddSystemModal";
import ShareOrbitSheet from "./shell/ShareOrbitSheet";
import { V197_SYSTEM_NODES } from "../../v197/contract";

type V197SystemNode = typeof V197_SYSTEM_NODES[number];
type LensSealSize = "nur-mini-12" | "nur-mini-16";

type OrbitBundle = {
  decisions: DecisionRow[];
  references: ReferenceRow[];
  sources: SourceRow[];
  capsules: CapsuleRowT[];
};

function useOwnerState() {
  const [state, setState] = useState<OrbitStateRow | null>(null);
  useEffect(() => { void nur.orbitState().then(setState).catch(() => setState(null)); }, []);
  return state;
}

function statusLabel(status: string) {
  return status === "STAGED" ? "saved question" : status.toLowerCase().replaceAll("_", " ");
}

function LensSeal({ size = "nur-mini-16", className = "" }: { size?: LensSealSize; className?: string }) {
  const pixels = size === "nur-mini-12" ? "12" : "16";
  return (
    <span className={`nur-exact-mini-host nur-exact-icon-shell lens-authentic-seal ${className}`.trim()}
          data-nur-star-size={pixels} aria-hidden="true">
      <ExactMiniStar size={size} />
    </span>
  );
}

function EmptyState({ title, body }: { title: string; body: string }) {
  return (
    <div className="lens-empty">
      <LensSeal />
      <b>{title}</b>
      <p>{body}</p>
    </div>
  );
}

function formatDate(value: string | null | undefined) {
  if (!value) return "undated";
  return new Date(value).toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

async function loadOrbitBundle(orbitId: string): Promise<OrbitBundle> {
  const [decisions, references, sources, capsules] = await Promise.all([
    nur.listDecisions(orbitId),
    nur.listReferences(orbitId),
    nur.listSources(orbitId),
    nur.myCapsules(),
  ]);
  return { decisions, references, sources, capsules: capsules.filter(c => c.orbit_id === orbitId) };
}

export function UniverseMap() {
  const orbit = useOrbit();
  const ownerState = useOwnerState();
  const [summaryState, setSummaryState] = useState<string>("owner ledger");
  const [selected, setSelected] = useState<V197SystemNode>(V197_SYSTEM_NODES[0]);
  const [addOpen, setAddOpen] = useState(false);
  useEffect(() => {
    void nur.mapSummary()
      .then(summary => setSummaryState(`${summary.nodes.length} owned nodes · ${summary.provenance_label}`))
      .catch(() => setSummaryState("owner ledger unavailable"));
  }, []);

  return (
    <section className="nur-page active lens-page" id="page-universe-map" data-testid="universe-map-page">
      <p className="page-kicker">Map</p>
      <h1 className="page-title">See the system field<br /><em>without losing the center.</em></h1>
      <p className="page-sub">Every node is an owned or seedable system. Add System writes a real Orbit row; labels stay clear at desktop and mobile sizes.</p>
      <div className="lens-map-shell nur-panel">
        <div className="lens-map-sky" aria-label="Full system map">
          <div className="universe-rings ring-a" />
          <div className="universe-rings ring-b" />
          <div className="universe-rings ring-c" />
          <div className="lens-map-title"><NURWordmark variant="map" /><small>Neural Upgrade Rewiring</small></div>
          <div className="lens-map-master"><MasterStar variant="hero" /></div>
          {V197_SYSTEM_NODES.map(node => (
            <button key={node.key} type="button" className={`lens-map-node ${selected.key === node.key ? "active" : ""}`}
                    style={{ left: node.x, top: node.y }}
                    data-testid={`lens-map-node-${node.key}`}
                    onClick={() => setSelected(node)}>
              <LensSeal className="lens-map-node-seal" />
              <b>{node.name}</b>
              <small>{node.lensTag}</small>
            </button>
          ))}
          <button className="lens-map-add" type="button" data-testid="lens-add-system"
                  onClick={() => setAddOpen(true)}>
            <span>+</span><b>Add System</b><small>create a real Orbit</small>
          </button>
        </div>
        <aside className="lens-detail-panel">
          <span className="system-badge live">{summaryState}</span>
          <h2>{selected.name}</h2>
          <p>{selected.lensTag}. This panel is tied to your Orbit list and the selected map node.</p>
          <div className="lens-stat-grid">
            <span><b>{ownerState?.active_systems ?? orbit.projects.length}</b><em>active systems</em></span>
            <span><b>{ownerState?.open_questions ?? "0"}</b><em>open questions</em></span>
            <span><b>{ownerState?.outcomes_returned ?? orbit.glows}</b><em>outcomes returned</em></span>
          </div>
          <div className="universe-map-legend lens-legend">
            <span><LensSeal size="nur-mini-12" className="legend-private" /> private orbit</span>
            <span><LensSeal size="nur-mini-12" className="legend-shared" /> system shared</span>
            <span><LensSeal size="nur-mini-12" className="legend-learning" /> learning candidate</span>
          </div>
        </aside>
      </div>
      <AddSystemModal open={addOpen} onClose={() => setAddOpen(false)} />
    </section>
  );
}

export function UniverseOrbits() {
  const orbit = useOrbit();
  const [orbits, setOrbits] = useState<OrbitRow[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [bundle, setBundle] = useState<OrbitBundle | null>(null);
  const [newTitle, setNewTitle] = useState("");
  const [shareOpen, setShareOpen] = useState(false);

  useEffect(() => {
    void nur.listOrbits().then(rows => {
      setOrbits(rows);
      setSelectedId(id => id ?? rows.find(r => r.kind !== "PERSONAL_BRIDGE")?.id ?? rows[0]?.id ?? null);
    });
  }, []);
  useEffect(() => { void nur.orbitsSummary().catch(() => undefined); }, []);
  useEffect(() => {
    if (!selectedId) { setBundle(null); return; }
    void loadOrbitBundle(selectedId).then(setBundle).catch(() => setBundle(null));
  }, [selectedId]);

  const selected = orbits.find(o => o.id === selectedId) ?? null;
  async function createOrbit() {
    const title = newTitle.trim();
    if (!title) return;
    const row = await orbit.addSystem(title, "Created from the Orbits view.");
    setNewTitle("");
    setOrbits(rows => [...rows, row]);
    setSelectedId(row.id);
  }

  return (
    <section className="nur-page active lens-page" id="page-universe-orbits" data-testid="universe-orbits-page">
      <p className="page-kicker">Orbits</p>
      <h1 className="page-title">Choose what can live<br /><em>inside each orbit.</em></h1>
      <p className="page-sub">Orbits are real owner-owned containers: decisions, references, constraints, sources and capsules are loaded from the API.</p>
      <div className="lens-two-col">
        <aside className="nur-panel lens-list-panel">
          <div className="panel-top">
            <div><h2 className="panel-title">Your Orbits</h2><p className="panel-sub">Private by default.</p></div>
          </div>
          <div className="task-add-row">
            <input data-testid="new-orbit-title" placeholder="New orbit name" value={newTitle}
                   onChange={e => setNewTitle(e.target.value)}
                   onKeyDown={e => e.key === "Enter" && createOrbit()} />
            <button type="button" data-testid="orbits-create" onClick={createOrbit}>create</button>
          </div>
          <div className="lens-button-list">
            {orbits.map(row => (
              <button key={row.id} type="button" className={row.id === selectedId ? "active" : ""}
                      onClick={() => setSelectedId(row.id)}>
                <b>{row.title}</b><span>{row.kind.replace("_", " ").toLowerCase()} · {row.status.toLowerCase()}</span>
              </button>
            ))}
          </div>
        </aside>
        <article className="nur-panel panel-pad">
          {selected ? (
            <>
              <div className="panel-top">
                <div><h2 className="panel-title">{selected.title}</h2><p className="panel-sub">{selected.description ?? "No description yet."}</p></div>
                <button className="f4-primary compact" type="button" onClick={() => setShareOpen(true)}
                        disabled={selected.kind === "PERSONAL_BRIDGE"} data-testid="orbits-share">
                  Share Orbit <span>→</span>
                </button>
              </div>
              <div className="lens-stat-grid">
                <span><b>{bundle?.decisions.length ?? 0}</b><em>decisions</em></span>
                <span><b>{bundle?.references.length ?? 0}</b><em>references</em></span>
                <span><b>{bundle?.sources.length ?? 0}</b><em>shareable sources</em></span>
                <span><b>{bundle?.capsules.length ?? 0}</b><em>capsules</em></span>
              </div>
              <div className="lens-orbit-ledger">
                <h3>Decisions</h3>
                {(bundle?.decisions.length ? bundle.decisions : []).map(row => <p key={row.id}><BidiText>{row.statement}</BidiText></p>)}
                {bundle && bundle.decisions.length === 0 && <EmptyState title="No decision yet" body="Use Share Orbit to capture a decision before sharing." />}
                <h3>References and constraints</h3>
                {(bundle?.references.length ? bundle.references : []).map(row => <p key={row.id}><b>{row.kind}</b> · <BidiText>{row.title}</BidiText></p>)}
                {bundle && bundle.references.length === 0 && <EmptyState title="No reference yet" body="A reference can become an approved Capsule source." />}
              </div>
            </>
          ) : <EmptyState title="No Orbit selected" body="Create or choose an Orbit to inspect." />}
        </article>
      </div>
      {selected && selected.kind !== "PERSONAL_BRIDGE" && (
        <ShareOrbitSheet orbitId={selected.id} orbitTitle={selected.title} open={shareOpen} onClose={() => setShareOpen(false)} />
      )}
    </section>
  );
}

type TimelineFilter = "all" | "outcomes" | "corrections" | "capsules" | "omega";
type TimelineRow = { id: string; kind: string; title: string; body: string; at: string; group: TimelineFilter };

export function UniverseTimeline() {
  const [events, setEvents] = useState<CognitiveEventRow[]>([]);
  const [capsules, setCapsules] = useState<CapsuleRowT[]>([]);
  const [omega, setOmega] = useState<OmegaDashboard | null>(null);
  const [filter, setFilter] = useState<TimelineFilter>("all");
  const [selected, setSelected] = useState<TimelineRow | null>(null);

  useEffect(() => {
    void Promise.all([nur.listEvents(undefined, 120), nur.myCapsules(), nur.omegaDashboard(), nur.timelineSummary(120)])
      .then(([eventRows, capsuleRows, omegaRows]) => { setEvents(eventRows); setCapsules(capsuleRows); setOmega(omegaRows); })
      .catch(() => {});
  }, []);

  const rows = useMemo<TimelineRow[]>(() => {
    const eventRows = events.map(e => ({
      id: e.id,
      kind: e.event_kind,
      title: e.event_kind.replaceAll("_", " ").toLowerCase(),
      body: e.content_text ?? JSON.stringify(e.structured_payload).slice(0, 180),
      at: e.created_at,
      group: e.event_kind.includes("OUTCOME") ? "outcomes" as const
        : e.event_kind.includes("CORRECTION") ? "corrections" as const
          : "all" as const,
    }));
    const capsuleRows = capsules.map(c => ({
      id: c.id,
      kind: c.revoked_at ? "CAPSULE_REVOKED" : "CAPSULE_CREATED",
      title: c.revoked_at ? "capsule revoked" : "capsule created",
      body: c.purpose,
      at: c.revoked_at ?? c.created_at,
      group: "capsules" as const,
    }));
    const omegaRows = [
      ...(omega?.consolidation_runs ?? []).map(r => ({
        id: r.id, kind: "OMEGA_CONSOLIDATION", title: `${r.run_kind.toLowerCase()} consolidation`,
        body: `${r.created_claims} claims · ${r.contradictions_found} contradictions · ${r.predictions_resolved} predictions resolved`,
        at: r.created_at, group: "omega" as const,
      })),
      ...(omega?.claims ?? []).map(c => ({
        id: c.id, kind: "OMEGA_CLAIM", title: c.truth_status.toLowerCase(),
        body: c.claim_text, at: c.updated_at, group: "omega" as const,
      })),
    ];
    return [...eventRows, ...capsuleRows, ...omegaRows].sort((a, b) => Date.parse(b.at) - Date.parse(a.at));
  }, [events, capsules, omega]);
  const visible = filter === "all" ? rows : rows.filter(r => r.group === filter);

  return (
    <section className="nur-page active lens-page" id="page-universe-timeline" data-testid="universe-timeline-page">
      <p className="page-kicker">Timeline</p>
      <h1 className="page-title">A unified ledger<br /><em>of what actually happened.</em></h1>
      <p className="page-sub">Talk turns, model responses, journal entries, plan steps, outcomes, capsules, and Omega changes appear with provenance labels.</p>
      <div className="lens-filter-row" role="tablist" aria-label="Timeline filters">
        {(["all", "outcomes", "corrections", "capsules", "omega"] as const).map(f => (
          <button key={f} type="button" className={filter === f ? "active" : ""} onClick={() => setFilter(f)}>{f}</button>
        ))}
      </div>
      <div className="lens-two-col timeline-layout">
        <article className="nur-panel panel-pad">
          {visible.map(row => (
            <button key={`${row.kind}-${row.id}`} type="button" className="timeline-row"
                    onClick={() => setSelected(row)}>
              <span>{formatDate(row.at)}</span>
              <b>{row.title}</b>
              <em>{row.kind}</em>
              <p><BidiText>{row.body}</BidiText></p>
            </button>
          ))}
          {visible.length === 0 && <EmptyState title="Nothing in this filter yet" body="Seed or use the product, then this filter will fill from persisted rows." />}
        </article>
        <aside className="nur-panel panel-pad">
          <h2 className="panel-title">Evidence detail</h2>
          {selected ? (
            <>
              <p className="v172-eyebrow">{selected.kind}</p>
              <p><BidiText>{selected.body}</BidiText></p>
              <div className="v172-now-row"><span>recorded</span><b>{formatDate(selected.at)}</b></div>
            </>
          ) : <p className="panel-sub">Open an event to inspect its provenance without exposing raw private dumps.</p>}
        </aside>
      </div>
    </section>
  );
}

export function UniverseInsights() {
  const [data, setData] = useState<OmegaDashboard | null>(null);
  const nav = useNavigate();
  async function refresh() {
    const [dashboard] = await Promise.all([nur.omegaDashboard(), nur.insightsSummary()]);
    setData(dashboard);
  }
  useEffect(() => { void refresh().catch(() => undefined); }, []);

  return (
    <section className="nur-page active lens-page" id="page-universe-insights" data-testid="universe-insights-page">
      <p className="page-kicker">Insights</p>
      <h1 className="page-title">Candidates, not commandments<br /><em>until evidence returns.</em></h1>
      <p className="page-sub">This surface is backed by Omega claims, predictions, contradictions, review queue items, and learning proposals.</p>
      <div className="lens-insight-grid">
        <article className="nur-panel panel-pad">
          <div className="panel-top"><div><h2 className="panel-title">Candidate insights</h2><p className="panel-sub">Owner confirmation keeps sensitive inference gated.</p></div></div>
          {(data?.review_queue ?? []).map(item => (
            <div className="omega-card-row" key={item.id}>
              <b>{item.sensitivity} · {item.candidate_claim_type}</b>
              <span><BidiText>{item.candidate_claim_text}</BidiText></span>
              <div className="omega-button-row">
                <button type="button" onClick={async () => { await nur.omegaReviewAction(item.id, "approve"); await refresh(); }}>approve insight</button>
                <button type="button" onClick={async () => { await nur.omegaReviewAction(item.id, "reject"); await refresh(); }}>reject</button>
              </div>
            </div>
          ))}
          {data && data.review_queue.length === 0 && <EmptyState title="No sensitive item waiting" body="That is allowed; Omega does not promote sensitive claims automatically." />}
        </article>
        <article className="nur-panel panel-pad">
          <h2 className="panel-title">Open claims</h2>
          {(data?.claims ?? []).map(claim => (
            <button className="lens-claim-row" key={claim.id} type="button"
                    onClick={() => nav(`/universe/omega/why-changed/${claim.id}`)}>
              <b><BidiText>{claim.claim_text}</BidiText></b>
              <span>{claim.truth_status} · {Math.round(claim.confidence * 100)}% · {claim.support_count} support / {claim.contradiction_count} conflict</span>
            </button>
          ))}
        </article>
        <article className="nur-panel panel-pad">
          <h2 className="panel-title">What NUR may be wrong about</h2>
          {(data?.contradictions ?? []).map(c => (
            <div className="omega-card-row contradiction" key={c.id}>
              <b>{c.severity} · {c.status}</b>
              <span><BidiText>{c.description}</BidiText></span>
              <button type="button" onClick={async () => { await nur.omegaResolveContradiction(c.id); await refresh(); }}>mark reviewed</button>
            </div>
          ))}
          {data && data.contradictions.length === 0 && <p className="panel-sub">No open contradiction is currently returned by Omega.</p>}
        </article>
        <article className="nur-panel panel-pad">
          <h2 className="panel-title">Unresolved predictions</h2>
          {(data?.predictions ?? []).map(p => (
            <div className="omega-card-row" key={p.id}>
              <b><BidiText>{p.prediction_text}</BidiText></b>
              <span>Expected: <BidiText>{p.expected_observation}</BidiText></span>
              <em>{p.status} · {Math.round(p.confidence * 100)}%</em>
            </div>
          ))}
        </article>
      </div>
    </section>
  );
}

export function UniverseResearch() {
  const orbit = useOrbit();
  const [question, setQuestion] = useState("");
  const [rows, setRows] = useState<ResearchBriefRow[]>([]);
  const [savedRef, setSavedRef] = useState<string | null>(null);
  useEffect(() => { void nur.listResearchBriefs().then(setRows).catch(() => undefined); }, []);

  async function saveQuestion() {
    const text = question.trim();
    if (!text) return;
    const row = await nur.createResearchBrief(text, "Saved from /universe/research; not fetched or treated as truth.", orbit.activeOrbit?.id ?? undefined);
    setRows(r => [row, ...r]);
    setQuestion("");
  }

  async function saveAsReference(row: ResearchBriefRow) {
    if (!orbit.activeOrbit) return;
    const converted = await nur.convertResearchBrief(row.id);
    setSavedRef(converted.target_id);
    setRows(current => current.map(item => item.id === row.id ? { ...item, status: "CONVERTED" } : item));
  }

  return (
    <section className="nur-page active lens-page" id="page-universe-research" data-testid="universe-research-page">
      <p className="page-kicker">Research</p>
      <h1 className="page-title">Save the question<br /><em>before calling it truth.</em></h1>
      <p className="page-sub">No live external engine is connected in disabled mode. Research questions are persisted privately and can be converted into Orbit references.</p>
      <article className="nur-panel panel-pad">
        <div className="thought-composer">
          <input data-testid="research-question" value={question} placeholder="What outside signal do you need?"
                 onChange={e => setQuestion(e.target.value)}
                 onKeyDown={e => e.key === "Enter" && saveQuestion()} />
          <button className="thought-send-button send-holo-pill" type="button" data-testid="research-save" onClick={saveQuestion}><span>Save</span></button>
        </div>
        {savedRef && <p className="f4-privacy"><LensSeal size="nur-mini-12" /><span>Saved as an Orbit reference: <b dir="ltr">{savedRef}</b></span></p>}
        <div className="lens-card-list">
          {rows.map(row => (
            <div className="omega-card-row" key={row.id}>
              <b><BidiText>{row.question}</BidiText></b>
              <em>{statusLabel(row.status)} · {formatDate(row.created_at)}</em>
              <button type="button" data-testid="research-convert-reference" disabled={!orbit.activeOrbit} onClick={() => saveAsReference(row)}>
                {orbit.activeOrbit ? "turn into reference" : "choose an Orbit first"}
              </button>
            </div>
          ))}
        </div>
      </article>
    </section>
  );
}

export function UniverseCommunity() {
  const orbit = useOrbit();
  const [note, setNote] = useState("");
  const [rows, setRows] = useState<CommunityNoteRow[]>([]);
  useEffect(() => {
    void nur.listCommunityNotes().then(setRows).catch(() => undefined);
  }, []);
  async function saveLocalNote() {
    const text = note.trim();
    if (!text) return;
    const row = await nur.createCommunityNote("local consultation note", text, orbit.activeOrbit?.id ?? undefined, "future collaborator");
    setRows(r => [row, ...r]);
    setNote("");
  }
  return (
    <section className="nur-page active lens-page" id="page-universe-community" data-testid="universe-community-page">
      <p className="page-kicker">Community</p>
      <h1 className="page-title">Think with others<br /><em>without pretending they are here.</em></h1>
      <p className="page-sub">This is a local consultation note area. It does not fake users, counts, or live community intelligence.</p>
      <article className="nur-panel panel-pad">
        <div className="thought-composer">
          <input data-testid="community-note" value={note} placeholder="What would you ask a collaborator to inspect?"
                 onChange={e => setNote(e.target.value)}
                 onKeyDown={e => e.key === "Enter" && saveLocalNote()} />
          <button className="thought-send-button send-holo-pill" type="button" data-testid="community-save" onClick={saveLocalNote}><span>Save</span></button>
        </div>
        <p className="f4-privacy"><LensSeal size="nur-mini-12" /><span>Collaborator Capsules are created through Share Orbit, where source boundaries are explicit and revocable.</span></p>
        <div className="lens-card-list">
          {rows.map(row => <div className="omega-card-row" key={row.id}><b><BidiText>{row.title}</BidiText></b><span><BidiText>{row.note}</BidiText></span><em>{row.provenance_label.toLowerCase()} · {formatDate(row.created_at)}</em></div>)}
          {rows.length === 0 && <EmptyState title="No consultation note yet" body="Write one collaborator question to persist it locally." />}
        </div>
      </article>
    </section>
  );
}

export function UniverseWebSignals() {
  const orbit = useOrbit();
  const [question, setQuestion] = useState("");
  const [rows, setRows] = useState<WebSignalQuestionRow[]>([]);
  useEffect(() => {
    void nur.listWebSignalQuestions().then(setRows).catch(() => undefined);
  }, []);
  async function save() {
    const text = question.trim();
    if (!text) return;
    const row = await nur.createWebSignalQuestion(text, orbit.activeOrbit?.id ?? undefined);
    await nur.createResearchBrief(text, "Saved from Web Signals; no live web fetch performed.", orbit.activeOrbit?.id ?? undefined);
    setRows(r => [row, ...r]);
    setQuestion("");
  }
  return (
    <section className="nur-page active lens-page" id="page-universe-web-signals" data-testid="universe-web-signals-page">
      <p className="page-kicker">Web Signals</p>
      <h1 className="page-title">Name the outside signal<br /><em>without inventing a source.</em></h1>
      <p className="page-sub">No live web connector is enabled. This lens saves web-signal questions into your private ledger and Research queue.</p>
      <article className="nur-panel panel-pad">
        <div className="thought-composer">
          <input data-testid="web-signal-question" value={question} placeholder="What web signal should be checked later?"
                 onChange={e => setQuestion(e.target.value)}
                 onKeyDown={e => e.key === "Enter" && save()} />
          <button className="thought-send-button send-holo-pill" type="button" data-testid="web-signal-save" onClick={save}><span>Save</span></button>
        </div>
        <div className="lens-card-list">
          {rows.map(row => <div className="omega-card-row" key={row.id}><b>saved web-signal question</b><span><BidiText>{row.question}</BidiText></span><em>{row.provider_status.toLowerCase()} · {formatDate(row.created_at)}</em></div>)}
          {rows.length === 0 && <EmptyState title="No web signal saved yet" body="Save a question; NUR will not fetch or fabricate results." />}
        </div>
      </article>
    </section>
  );
}

export function Settings() {
  const [health, setHealth] = useState<{ status: string; ai_provider: string } | null>(null);
  const [ready, setReady] = useState<{ status: string; checks: Record<string, string> } | null>(null);
  const [metricsStatus, setMetricsStatus] = useState<string>("not checked");
  const [language, setLanguage] = useState(() => document.documentElement.lang || "en");
  const [writingPreference, setWritingPreference] = useState("default");
  const [sound, setSound] = useState(false);
  const [preferences, setPreferences] = useState<ProfilePreferences | null>(null);
  const [scheduler, setScheduler] = useState<string>("not checked");

  async function refresh() {
    const [h, r, p, s] = await Promise.all([nur.healthz(), nur.readyz(), nur.getPreferences(), nur.omegaSchedulerStatus()]);
    setHealth(h);
    setReady(r);
    setPreferences(p);
    setLanguage(p.locale || "en");
    setWritingPreference(p.writing_preference || "default");
    setSound(p.sound_enabled);
    setScheduler(`${s.worker_mode}; ${s.last_consolidation_status}`);
  }
  useEffect(() => { void refresh().catch(() => undefined); }, []);
  useEffect(() => {
    document.documentElement.lang = language;
    document.documentElement.dir = dirForLocale(language);
  }, [language]);

  async function checkMetrics() {
    const text = await nur.metricsText();
    setMetricsStatus(text.includes("nur_ai_provider_configured") ? "metrics reachable; provider label present" : "metrics reachable; provider metric missing");
  }

  async function savePreference(next: Partial<Pick<ProfilePreferences, "locale" | "writing_preference" | "sound_enabled">>) {
    const updated = await nur.patchPreferences(next);
    setPreferences(updated);
    setLanguage(updated.locale || "en");
    setWritingPreference(updated.writing_preference || "default");
    setSound(updated.sound_enabled);
  }

  const providerState = health?.ai_provider === "openai"
    ? "OPENAI_CONFIGURED"
    : health?.ai_provider === "disabled" ? "DISABLED" : "OPENAI_NOT_CONFIGURED";

  return (
    <section className="nur-page active lens-page" id="page-settings" data-testid="settings-page">
      <p className="page-kicker">Settings</p>
      <h1 className="page-title">Configure power<br /><em>without leaking the key.</em></h1>
      <p className="page-sub">Provider controls are server-only. The frontend never asks for, stores, imports, or displays an OpenAI key.</p>
      <div className="lens-settings-grid">
        <article className="nur-panel panel-pad">
          <h2 className="panel-title">AI provider status</h2>
          <div className="v172-now-row"><span>mode</span><b>{providerState}</b></div>
          <div className="v172-now-row"><span>API</span><b>{health?.status ?? "not checked"}</b></div>
          <div className="v172-now-row"><span>ready</span><b>{ready?.status ?? "not checked"}</b></div>
          <button className="f4-primary compact" type="button" data-testid="settings-refresh-provider" onClick={refresh}>Refresh provider status</button>
          <div className="settings-code">
            <code>bash infra/scripts/configure-openai-local.sh</code>
            <code>bash RUN_NUR.sh openai</code>
          </div>
        </article>
        <article className="nur-panel panel-pad">
          <h2 className="panel-title">Language and quiet sound</h2>
          <label className="settings-label">Language
            <select data-testid="settings-language-select" value={language} onChange={e => savePreference({ locale: e.target.value })}>
              {LOCALE_META.map(meta => (
                <option key={meta.locale} value={meta.locale}>
                  {meta.label} — {meta.status === "polished_beta" ? "polished beta" : "draft / unreviewed"}
                </option>
              ))}
            </select>
          </label>
          <label className="settings-label">Writing preference
            <select data-testid="settings-writing-preference" value={writingPreference} onChange={e => savePreference({ writing_preference: e.target.value })}>
              <option value="default">Default for selected language</option>
              <option value="roman">Roman Urdu / Latin-script preference</option>
              <option value="script">Native script preference</option>
            </select>
          </label>
          {language === "ur" && writingPreference === "roman" && (
            <p className="panel-sub" data-testid="roman-urdu-law">Roman Urdu is locale=ur plus writing_preference=roman, not a separate locale.</p>
          )}
          <button className={`settings-toggle ${sound ? "active" : ""}`} type="button" data-testid="settings-quiet-sound" aria-pressed={sound}
                  onClick={() => savePreference({ sound_enabled: !sound })}>
            Quiet sound {sound ? "on" : "off"}
          </button>
          <p className="panel-sub">Preferences persist after refresh. Last saved: {preferences ? formatDate(preferences.updated_at) : "not loaded"}</p>
        </article>
        <article className="nur-panel panel-pad">
          <h2 className="panel-title">Omega and safety</h2>
          <div className="v172-now-row"><span>Omega flag</span><b>{import.meta.env.VITE_NUR_ENABLE_OMEGA_RESEARCH === "true" ? "enabled" : "hidden"}</b></div>
          <div className="v172-now-row"><span>scheduler</span><b>{scheduler}</b></div>
          <button className="soft-button" type="button" data-testid="settings-check-metrics" onClick={checkMetrics}>Check metrics</button>
          <p className="panel-sub">{metricsStatus}</p>
        </article>
        <article className="nur-panel panel-pad">
          <h2 className="panel-title">Exports and deletion</h2>
          <p className="panel-sub">Owner export lives in Omega. Account deletion is intentionally not exposed in this local beta.</p>
          <button className="soft-button" type="button" data-testid="settings-delete-disabled" disabled>Delete account unavailable in local beta</button>
        </article>
      </div>
    </section>
  );
}

export function OmegaWhyChangedRoute() {
  const { claimId = "" } = useParams();
  const [why, setWhy] = useState<OmegaWhyChanged | null>(null);
  const [evidence, setEvidence] = useState<OmegaEvidence[]>([]);
  const nav = useNavigate();
  useEffect(() => {
    if (!claimId) return;
    void Promise.all([nur.omegaWhyChanged(claimId), nur.omegaClaimEvidence(claimId)])
      .then(([w, e]) => { setWhy(w); setEvidence(e); })
      .catch(() => undefined);
  }, [claimId]);
  return (
    <section className="nur-page active lens-page" id="page-omega-why-changed" data-testid="omega-why-changed-route">
      <p className="page-kicker">Why changed</p>
      <h1 className="page-title">Why NUR changed<br /><em>its confidence.</em></h1>
      <p className="page-sub">This route explains the evidence edges behind one claim. It is a proof surface, not a hidden reasoning dump.</p>
      <article className="nur-panel panel-pad">
        {why ? (
          <>
            <div className="panel-top">
              <div>
                <h2 className="panel-title"><BidiText>{why.claim_text}</BidiText></h2>
                <p className="panel-sub">{why.current_truth_status} · {Math.round(why.current_confidence * 100)}%</p>
              </div>
              <button className="soft-button" type="button" onClick={() => nav("/universe/omega")}>Open Omega</button>
            </div>
            <div className="lens-card-list">
              {why.changed_because.map(line => <div className="v172-now-row" key={line}><span>because</span><b><BidiText>{line}</BidiText></b></div>)}
              {why.supporting_edges.map(line => <div className="v172-now-row" key={line}><span>supports</span><b><BidiText>{line}</BidiText></b></div>)}
              {why.contradicting_edges.map(line => <div className="v172-now-row" key={line}><span>contradicts</span><b><BidiText>{line}</BidiText></b></div>)}
            </div>
            <h2 className="panel-title" style={{ marginTop: 18 }}>Evidence edges</h2>
            {evidence.map(edge => (
              <div className="omega-card-row" key={edge.id}>
                <b>{edge.relation} · {edge.evidence_kind}</b>
                <span>strength {edge.strength} · {edge.note ?? "no note"}</span>
              </div>
            ))}
          </>
        ) : <EmptyState title="Claim evidence loading" body="Open this route from an Omega claim for a concrete claim id." />}
      </article>
    </section>
  );
}
