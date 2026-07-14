/* V183 Systems universe: hero + live stats, world-command modes, the
   constellation MAP (rings, orbit lines, seven system nodes, Add-system shape,
   mantra, legend, field readout, signal lane), candidate-insight panel, and
   the quiet-evidence glow audit. Node selection is live; joining/creating
   systems is honestly gated to Phase 3. */
import { useEffect, useState } from "react";
import MasterStar from "../../components/MasterStar";
import NURWordmark from "../../components/NURWordmark";
import { useOrbit } from "../../lib/orbitState";
import { nur, type OrbitStateRow, type ResearchBriefRow } from "../../lib/api";
import { CRITICAL_COPY, resolveLocale } from "../../lib/i18n";
import ShareOrbitSheet from "./shell/ShareOrbitSheet";
import { useDirector } from "../../app/TransitionDirector";
import { V197_SYSTEM_NODES, V197_WORLD_COMMANDS } from "../../v197/contract";

export default function Systems() {
  const orbit = useOrbit();
  const director = useDirector();
  const copy = CRITICAL_COPY[resolveLocale(navigator.language)].systems;
  const [active, setActive] = useState("quiet");
  const [mode, setMode] = useState(0);
  const [note, setNote] = useState<string | null>(null);
  const [researchQ, setResearchQ] = useState("");
  const [savedResearch, setSavedResearch] = useState<ResearchBriefRow[]>([]);
  const [ownerState, setOwnerState] = useState<OrbitStateRow | null>(null);
  const [shareOpen, setShareOpen] = useState(false);
  useEffect(() => {
    Promise.all([nur.listResearchBriefs(), nur.orbitState()])
      .then(([r, s]) => { setSavedResearch(r.slice(0, 5)); setOwnerState(s); })
      .catch(() => {});
  }, []);
  const stageResearch = async () => {
    const q = researchQ.trim();
    if (!q) return;
    setResearchQ("");
    const row = await nur.createResearchBrief(q, "Saved from Systems research field; not fetched or treated as truth.", orbit.activeOrbit?.id);
    setSavedResearch(x => [row, ...x].slice(0, 5));
  };
  const openMode = (index: number) => {
    setMode(index);
    const command = V197_WORLD_COMMANDS[index]?.key;
    if (command === "universe") return;
    if (command === "consult") { setNote("Consultation note is saved in Community."); setTimeout(() => director.go("/universe/community"), 260); return; }
    if (command === "research") { document.getElementById("universe-research")?.scrollIntoView({ block: "start", behavior: "smooth" }); return; }
    if (command === "community") { director.go("/universe/community"); return; }
    if (command === "insights") { director.go("/universe/insights"); }
  };

  return (
    <section className="nur-page active" id="page-systems">
      <section className="universe-page-shell">
        <header className="universe-hero-copy">
          <div>
            <p className="page-kicker">{copy.kicker} <span className="live-dot" /> owner ledger</p>
            <h1 className="page-title" id="systems-title">{copy.title}<br /><em>{copy.titleEmphasis}</em></h1>
            <p className="page-sub">{copy.subtitle}</p>
          </div>
          <div className="universe-hero-stats" aria-label="Current system state">
            <span data-testid="metric-active-systems"><b>{ownerState?.active_systems ?? orbit.projects.length}</b><em>{copy.activeSystems}</em></span>
            <span data-testid="metric-outcomes-returned"><b>{ownerState?.outcomes_returned ?? "—"}</b><em>{copy.outcomesReturned}</em></span>
            <span data-testid="metric-insights-evolving"><b>{ownerState?.insights_evolving ?? "—"}</b><em>{copy.insightsEvolving}</em></span>
          </div>
        </header>

        <div className="universe-command-row" aria-label="Universe modes">
          {V197_WORLD_COMMANDS.map((m, i) => (
            <button key={m.key} className={`world-command${mode === i ? " active" : ""}`} type="button"
                    data-world-focus={m.key}
                    onClick={() => openMode(i)}>{m.glyph} {m.label}</button>
          ))}
        </div>

        <div className="universe-main-grid">
          <section className="universe-map-panel nur-panel" aria-label={copy.mapLabel}>
            <div className="universe-map-fog" /><div className="universe-map-grain" />
            <div className="universe-rings ring-a" /><div className="universe-rings ring-b" /><div className="universe-rings ring-c" />
            <div className="universe-map-title">
              <b><NURWordmark variant="map" /></b>
              <small className="nur-master-subtitle" data-testid="map-subtitle">{copy.mapSubtitle}</small>
            </div>
            <div className="universe-master-star nur-v90-exact-center-host" aria-label="V90 master star" data-testid="map-master-star">
              <div className="f4-core"><MasterStar variant="hero" id="iSpark" /></div>
            </div>
            {["q","p","w","e","r","s"].map(l => <div key={l} className={`universe-orbit-line line-${l}`} />)}
            {V197_SYSTEM_NODES.map(n => (
              <button key={n.key} type="button" data-system={n.name}
                      className={`universe-system-node ${n.key}${active === n.key ? " active" : ""}`}
                      data-testid={`map-node-${n.key}`}
                      aria-pressed={active === n.key}
                      onClick={() => setActive(n.key)}>
                <i>{n.glyph}</i><span><b>{n.name}</b><small>{n.tag}</small></span>
              </button>
            ))}
            <button className="universe-add-system" type="button" data-testid="pw-add-system"
                    aria-label={copy.addSystem}
                    onClick={() => orbit.setAddSystemOpen(true)}>
              <span>+</span><b>{copy.addSystem}</b><small>{copy.addSystemHint}</small>
            </button>
            <div className="universe-map-mantra">We map the unseen.<br /><em>You become the inevitable.</em></div>
            <div className="universe-map-legend">
              <span><i className="legend-private" /> private orbit</span>
              <span><i className="legend-shared" /> shared system</span>
              <span><i className="legend-learning" /> learning candidate</span>
            </div>
            <div className="universe-field-readout" aria-label="System field status" data-testid="system-field-readout">
              <b>{copy.systemField} ·</b> <em>{copy.ownerLedger}</em>
              <span>{ownerState ? `${ownerState.active_systems} active systems · ${ownerState.outcomes_returned} returned outcomes` : "Waiting for owner-derived counts"}</span>
              <div className="universe-field-rule"><i /><i /><i /></div>
            </div>
            <div className="universe-scan-orb" />
            <div className="universe-sigil a" /><div className="universe-sigil b" /><div className="universe-sigil c" />
            <div className="universe-system-lane" aria-label="Universe signals">
              <article><small>owner systems</small><b>{ownerState?.active_systems ?? orbit.projects.length}</b><span /><em>private</em> by default</article>
              <article><small>open questions</small><b>{ownerState?.open_questions ?? "—"}</b><span />waiting for witness</article>
              <article><small>returned outcomes</small><b>{ownerState?.outcomes_returned ?? "—"}</b><span />from real owner entries</article>
            </div>
          </section>

          <aside className="universe-insight-panel nur-panel" aria-label="Candidate Insight">
            <div className="universe-panel-head">
              <span className="system-badge">✦ Candidate insight</span>
              <span className="live-label">OWNER LEDGER</span>
            </div>
            <div className="universe-insight-title"><small>Theme</small><h2>Identity expansion</h2></div>
            <p className="universe-insight-copy">You are stepping into a larger self-definition than your current containers were built for.</p>
            <div className="signal-list">
              <span>Increased discerning</span><span>Strong creative pull</span><span>Restlessness with old structures</span>
            </div>
            <div className="insight-opportunity"><small>Possible move</small><b>Build the container before the surge.</b></div>
            <div className="insight-uncertainty">
              <span>What NUR may be wrong about</span>
              <p>Whether this is expansion or simply escape from a hard middle.</p>
            </div>
            <button className="soft-button wide" type="button" onClick={() => director.go("/universe/insights")}>Open full analysis <span>→</span></button>
            <div className="insight-strength"><span>Evidence state</span><b>{ownerState?.insights_evolving ? `${ownerState.insights_evolving} candidates` : "not enough evidence yet"}</b><i /><em /></div>
            {orbit.activeOrbit ? (
              <button className="f4-primary compact" type="button" data-testid="share-orbit"
                      style={{ marginTop: 14 }} onClick={() => setShareOpen(true)}>
                {copy.shareOrbit} <span aria-hidden="true">→</span>
              </button>
            ) : (
              <p className="f4-privacy" style={{ marginTop: 14 }}><i>✦</i>
                <span>Save this System to your Orbit to make it shareable through a Capsule.</span></p>
            )}
          </aside>
        </div>

        <section id="universe-research" className="nur-panel panel-pad" aria-label="Research field">
          <div className="panel-top">
            <div>
              <h2 className="panel-title">{copy.researchField}</h2>
              <p className="panel-sub">Bring the outside world in as a saved question, sourced later, never treated as truth.</p>
            </div>
            <span className="tiny-link">outside context</span>
          </div>
          <div className="thought-composer">
            <input id="research-query" placeholder="What outside signal do you need?"
                   value={researchQ} onChange={e => setResearchQ(e.target.value)}
                   onKeyDown={e => e.key === "Enter" && stageResearch()} />
            <button className="thought-send-button send-holo-pill" type="button" aria-label="Save research question"
                    onClick={stageResearch}>
              <span>Save</span>
              <svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true"><path d="M3 12h14" stroke="currentColor" strokeWidth="1.6" fill="none"/><path d="M13 6l6 6-6 6" stroke="currentColor" strokeWidth="1.6" fill="none"/></svg>
            </button>
          </div>
          {savedResearch.map(q => (
            <div className="v172-now-row" key={q.id}><span>saved question</span><b>{q.question}</b></div>
          ))}
          <p className="f4-privacy"><i>✦</i><span>No external research engine is connected yet. Questions are saved privately; nothing is fetched, nothing is invented.</span></p>
        </section>
        <article className="clean-audit-card v172-glow-list">
          <div className="clean-card-heading">
            <span>Recent glows</span>
            <button type="button">view Orbit</button>
          </div>
          {[
            { g: "✦", t: "Returned instead of disappearing.", m: "Personal · today" },
            { g: "✣", t: "A useful condition was added.", m: "Shared · Quiet Ambition" },
            { g: "✧", t: "An outcome changed the map.", m: "System · candidate insight" },
          ].map((r, i) => (
            <button className="v172-glow-row" type="button" key={i}>
              <span>{r.g}</span><div><b>{r.t}</b><small>{r.m}</small></div>
            </button>
          ))}
        </article>
        <article className="clean-audit-card v172-glow-principle">
          <p className="context-title">Glows are not points.</p>
          <small>They are quiet evidence: you noticed, you moved, you returned. {orbit.glows} are still warm.</small>
        </article>
      </section>
      {note && <div className="sky-toast show" role="status">{note}</div>}
      {orbit.activeOrbit && (
        <ShareOrbitSheet orbitId={orbit.activeOrbit.id} orbitTitle={orbit.activeOrbit.title}
                         open={shareOpen} onClose={() => setShareOpen(false)} />
      )}
    </section>
  );
}
