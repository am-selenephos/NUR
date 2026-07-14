/* V183 Plan on the real substrate: the plan and its steps live in Postgres;
   the CHECKBOX_TICK behavior V197 restored is a PATCH; a finished step asks
   for one observed outcome (mandate F4) — the glow arrives only when the
   outcome is real. */
import { useState } from "react";
import ExactMiniStar from "../../components/ExactMiniStar";
import { useOrbit } from "../../lib/orbitState";
import { useGalaxy } from "../../galaxy/GalaxyProvider";
import { useDirector } from "../../app/TransitionDirector";
import type { StepRow } from "../../lib/api";

export default function Plan() {
  const orbit = useOrbit();
  const galaxy = useGalaxy();
  const director = useDirector();
  const [observingFor, setObservingFor] = useState<string | null>(null);
  const [observed, setObserved] = useState("");
  const [busy, setBusy] = useState(false);

  async function toggle(s: StepRow) {
    if (busy) return;
    setBusy(true);
    try {
      const next = await orbit.toggleStep(s.id, !s.done);
      if (next.done) {
        galaxy?.addEvent({ id: `task-${s.id}-${Date.now()}`, type: "task_completed" });
        galaxy?.burst(innerWidth * 0.4, innerHeight * 0.5, 0.45);
        setObservingFor(s.id);
        setObserved("");
      } else if (observingFor === s.id) {
        setObservingFor(null);
      }
    } finally { setBusy(false); }
  }

  async function keepOutcome(stepId: string) {
    const text = observed.trim();
    if (!text) return;
    await orbit.recordOutcome(stepId, text);
    setObservingFor(null);
    setObserved("");
  }

  async function makeEasier() {
    if (busy) return;
    setBusy(true);
    try {
      await orbit.addStep(
        "Reduce the next move to one visible pass",
        "Name the smallest version that still counts, then do only that.",
      );
    } finally { setBusy(false); }
  }

  const plan = orbit.plan;

  return (
    <section className="nur-page active" id="page-plan">
      <p className="page-kicker">Move</p>
      <h1 className="page-title" id="plan-title">Make one pattern<br /><em>into movement.</em></h1>
      <p className="page-sub">No task avalanche. This plan exists to move one real thing.</p>
      <div className="today-grid">
        <article className="nur-panel panel-pad">
          <div className="panel-top">
            <div>
              <h2 className="panel-title">{plan ? plan.title : "No route yet"}</h2>
              <p className="panel-sub">{plan ? "A short plan for the current NUR build." : "Begin one honest route — three finishable moves."}</p>
            </div>
            <span className="tiny-link">{plan ? "held in your Orbit" : "nothing invented"}</span>
          </div>
          {!plan && (
            <button className="f4-primary" type="button" data-testid="begin-route"
                    onClick={() => orbit.beginRoute()}>
              Begin tonight's route <span aria-hidden="true">→</span>
            </button>
          )}
          {plan && (
            <div className="plan-list">
              {plan.steps.map(s => (
                <div className={`plan-step${s.done ? " done" : ""}`} key={s.id}>
                  <button className="plan-check nur-v136-v89-mini-host nur-exact-icon-shell" aria-label="Complete" type="button"
                          aria-pressed={s.done} onClick={() => toggle(s)}>
                    <ExactMiniStar size="nur-mini-16" />
                  </button>
                  <div>
                    <h3>{s.title}</h3>
                    {s.body && <p>{s.body}</p>}
                    {observingFor === s.id && (
                      <div className="task-add-row" style={{ marginTop: 8 }}>
                        <input placeholder="what actually happened? one honest line…" value={observed}
                               autoFocus onChange={e => setObserved(e.target.value)}
                               onKeyDown={e => e.key === "Enter" && keepOutcome(s.id)} />
                        <button className="soft-btn" type="button" onClick={() => keepOutcome(s.id)}>keep outcome</button>
                      </div>
                    )}
                  </div>
                  <time>{s.done ? "held" : "open"}</time>
                </div>
              ))}
            </div>
          )}
          <div className="move-actions">
            <button className="f4-primary compact" type="button" disabled={busy} onClick={makeEasier}>Make this easier <span>→</span></button>
            <button className="soft-button" type="button" onClick={() => director.go("/universe/map")}>See systems map</button>
          </div>
        </article>
        <aside className="nur-panel panel-pad">
          <h2 className="panel-title">Blocker</h2>
          <p className="panel-sub">The original front visual language is the contract.</p>
          <div className="next-move">
            <p className="move-kicker">Ease the move</p>
            <h3>Build fresh interiors, not patch piles.</h3>
            <p>Use the front page as the aesthetic source of truth.</p>
          </div>
          <div className="next-move" style={{ marginTop: 14 }}>
            <p className="move-kicker">Why outcomes</p>
            <h3>A glow is quiet evidence.</h3>
            <p>It arrives only when you name what actually happened — never for the tick alone.</p>
          </div>
        </aside>
      </div>
    </section>
  );
}
