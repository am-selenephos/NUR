/* Exact V197 right context rail (mandate B7): v172 header, Boundary /
   Continuity / Glows tabs and panes, source card hierarchy, star shells. */
import { useState } from "react";
import MasterStar from "../../../components/MasterStar";
import { useDirector } from "../../../app/TransitionDirector";
import { useOrbit } from "../../../lib/orbitState";
import { V197_CONTEXT_PANES } from "../../../v197/contract";

type Pane = typeof V197_CONTEXT_PANES[number]["key"];

export default function UniverseContextRail({ onScopeOpen }: { onScopeOpen: () => void }) {
  const [pane, setPane] = useState<Pane>("boundary");
  const director = useDirector();
  const orbit = useOrbit();

  return (
    <>
      <header className="clean-audit-header v172-context-header">
        <div>
          <p className="v172-eyebrow">YOUR ORBIT</p>
          <h2 className="v172-context-title">Context, held gently.</h2>
        </div>
        <span className="v172-live-mark" aria-label="Owner ledger is current"><i />OWNER LEDGER</span>
      </header>

      <div className="audit-tabs clean-audit-tabs v172-tabs" role="tablist" aria-label="Orbit context views">
        {V197_CONTEXT_PANES.map(p => (
          <button key={p.key} type="button" role="tab" aria-selected={pane === p.key}
                  className={pane === p.key ? "active" : ""} onClick={() => setPane(p.key)}>
            {p.label}
          </button>
        ))}
      </div>

      <section className={`v172-context-pane${pane === "boundary" ? " active" : ""}`} data-context-pane="boundary">
        <article className="clean-audit-card v172-privacy-overview">
          <div className="v172-card-kicker">
            <span>Current boundary</span>
            <button className="v172-edit-boundary" type="button" onClick={onScopeOpen}>choose</button>
          </div>
          <div className="v172-boundary-current">
            <span className="v172-boundary-orb v172-exact-star-shell v172-rainbow-exact-star-shell">
              <MasterStar variant="hero" />
            </span>
            <div>
              <b>{orbit.boundary === "Private" ? "Private Orbit" : orbit.boundary}</b>
              <small>Held for you. Nothing moves without a clear choice.</small>
            </div>
          </div>
          <div className="v172-boundary-note">
            <span>Scope check</span>
            <p>Every share begins with a visible boundary. You choose whether a thought stays, travels, or becomes evidence.</p>
          </div>
        </article>
        <article className="clean-audit-card audit-permission v172-scope-stack">
          <div className="clean-card-heading">
            <span>Where this can live</span>
            <button type="button" onClick={onScopeOpen}>see all</button>
          </div>
          {[
            { k: "Private", b: "Private Orbit", e: "Only you can return here.", cls: "" },
            { k: "Ephemeral", b: "Ephemeral", e: "Used for this moment only.", cls: "" },
            { k: "System Shared", b: "System Shared", e: "Shared pseudonymously in one System.", cls: "" },
            { k: "Learning Candidate", b: "Learning Candidate", e: "Reviewed evidence for a Candidate Insight.", cls: " learning" },
          ].map(o => (
            <button key={o.k} type="button"
                    className={`audit-scope clean-scope v172-scope-option${o.cls}${orbit.boundary === o.k ? " selected" : ""}`}
                    onClick={() => orbit.setBoundary(o.k as never)}>
              <span><b>{o.b}</b><em>{o.e}</em></span>
            </button>
          ))}
        </article>
        <article className="clean-audit-card v172-now-card">
          <div className="clean-card-heading">
            <span>Available to this moment</span>
            <button type="button">why?</button>
          </div>
          <div className="v172-now-row"><span>Thread</span><b>Today / private reflection</b></div>
          <div className="v172-now-row"><span>Recall</span><b>Selected only</b></div>
          <div className="v172-now-row"><span>Sharing</span><b>Ask first</b></div>
        </article>
      </section>

      <section className={`v172-context-pane${pane === "continuity" ? " active" : ""}`} data-context-pane="continuity">
        <article className="clean-audit-card v172-bridge-card">
          <div className="clean-card-heading">
            <span>What is being held</span>
            <button data-page="journal" type="button" onClick={() => director.go("/journal")}>open journal</button>
          </div>
          <div className="v172-held-line">
            <span>“</span>
            <p>{orbit.journal[0]?.body.slice(0, 96) || "I do not need to solve everything tonight."}</p>
          </div>
          <div className="v172-held-meta"><span>Private note</span><time>today</time></div>
        </article>
        <article className="clean-audit-card v172-return-card">
          <div className="v172-card-kicker">
            <span>Next return</span>
            <span className="v172-return-state">IN MOTION</span>
          </div>
          <h3>Make one visible pass on the interior.</h3>
          <p>Small enough to return to. Clear enough to finish.</p>
          <div className="v172-route-progress" aria-label="Route progress"><i /><i className="done" /><i /><i /></div>
          <button className="v172-inline-action" data-page="plan" type="button" onClick={() => director.go("/plan")}>
            Open route <span>→</span>
          </button>
        </article>
        <article className="clean-audit-card v172-memory-card">
          <div className="clean-card-heading">
            <span>Continuity fragments</span>
            <button data-page="talk" type="button" onClick={() => director.go("/talk")}>use in Talk</button>
          </div>
          <button className="v172-fragment" type="button"><span>✦</span><p>One honest return changes the direction of a week.</p></button>
          <button className="v172-fragment" type="button"><span>◌</span><p>Quiet Ambition is open when you want a shared sky.</p></button>
        </article>
      </section>

      <section className={`v172-context-pane${pane === "glows" ? " active" : ""}`} data-context-pane="glows">
        <article className="clean-audit-card v172-glow-hero">
          <div className="v172-glow-orb v172-exact-star-shell"><MasterStar variant="hero" /></div>
          <div>
            <p className="v172-eyebrow">QUIET EVIDENCE</p>
            <h3>{orbit.glows} glows are still warm.</h3>
            <span>Nothing to maintain. Just proof that something moved.</span>
          </div>
        </article>
        <article className="clean-audit-card v172-glow-list">
          <div className="clean-card-heading">
            <span>Recent glows</span>
            <button data-page="today" type="button" onClick={() => director.go("/today")}>view Orbit</button>
          </div>
          <button className="v172-glow-row" type="button"><span>✦</span><div><b>Returned instead of disappearing.</b><small>Personal · today</small></div></button>
          <button className="v172-glow-row" type="button"><span>✣</span><div><b>A useful condition was added.</b><small>Shared · Quiet Ambition</small></div></button>
          <button className="v172-glow-row" type="button"><span>✧</span><div><b>An outcome changed the map.</b><small>System · candidate insight</small></div></button>
        </article>
        <article className="clean-audit-card v172-glow-principle">
          <p className="context-title">Glows are not points.</p>
          <small>They are quiet evidence: you noticed, moved, returned.</small>
        </article>
      </section>

      <footer className="v172-context-footer">
        <span className="v172-footer-dot" />
        <p>Private by default. Shared only by choice.</p>
      </footer>
    </>
  );
}
