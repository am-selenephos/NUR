/* V183 Today: orbit-hero with the master star, readings panel, recent glows,
   talk-mini composer. Greets the real chosen_name from /auth/me. */
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import MasterStar from "../../components/MasterStar";
import ExactMiniStar from "../../components/ExactMiniStar";
import { useAuth } from "../../app/AuthProvider";
import { useOrbit } from "../../lib/orbitState";
import { useDirector } from "../../app/TransitionDirector";
import { nur, type OrbitStateRow } from "../../lib/api";

export default function Today() {
  const { user } = useAuth();
  const orbit = useOrbit();
  const director = useDirector();
  const nav = useNavigate();
  const name = user?.profile.chosen_name ?? "traveller";
  const [state, setState] = useState<OrbitStateRow | null>(null);
  useEffect(() => { void nur.orbitState().then(setState).catch(() => undefined); }, []);
  const readings = useMemo(() => [
    { k: "Talk", v: Math.min(100, orbit.thread.length * 12), label: `${orbit.thread.length} persisted turn${orbit.thread.length === 1 ? "" : "s"}` },
    { k: "Journal", v: Math.min(100, orbit.journal.length * 18), label: `${orbit.journal.length} kept trace${orbit.journal.length === 1 ? "" : "s"}` },
    { k: "Outcome", v: Math.min(100, (state?.outcomes_returned ?? orbit.glows) * 22), label: `${state?.outcomes_returned ?? orbit.glows} returned` },
  ], [orbit.thread.length, orbit.journal.length, orbit.glows, state?.outcomes_returned]);

  return (
    <section className="nur-page active" id="page-today" data-testid="today-root">
      <div className="orbit-hero">
        <div>
          <p className="page-kicker">Your personal orbit</p>
          <h1 className="page-title" id="today-title">You are here, {name}.<br /><em>Start from what is real.</em></h1>
          <p className="page-sub">Not a dashboard. Not a performance. One honest reading, one real move.</p>
        </div>
        <div className="orbit-star-zone" aria-label="NUR master star" data-testid="today-orbit">
          <span className="orbit-annotation a">mind</span>
          <span className="orbit-annotation b">intention</span>
          <span className="orbit-annotation c">one move</span>
          <div className="f4-core"><MasterStar variant="hero" /></div>
        </div>
      </div>

      <div className="today-grid">
        <article className="nur-panel panel-pad">
          <div className="panel-top">
            <div>
              <h2 className="panel-title">Where are you right now?</h2>
              <p className="panel-sub">Owner-ledger signals. No fake score.</p>
            </div>
            <button className="tiny-link" type="button" onClick={() => director.go("/settings")}>settings →</button>
          </div>
          <div className="reading-lines">
            {readings.map(r => (
              <div className="reading-line" key={r.k}>
                <span>{r.k}</span>
                <span className="reading-bar"><i style={{ width: `${r.v}%` }} /></span>
                <strong>{r.label}</strong>
              </div>
            ))}
          </div>
          <div className="next-move">
            <p className="move-kicker">One real next move</p>
            <h3>Make the NUR interior feel like the same universe.</h3>
            <p>Keep the visual language exact, then move one real thing.</p>
            <div className="move-actions">
              <button className="f4-primary compact" type="button" onClick={() => director.go("/plan")}>Open the plan <span>→</span></button>
              <button className="soft-button" type="button" onClick={() => director.go("/talk")}>Think with NUR</button>
            </div>
          </div>
        </article>

        <aside className="nur-panel panel-pad">
          <div className="panel-top">
            <div>
              <h2 className="panel-title">Recent Glows</h2>
              <p className="panel-sub">Evidence of movement, not points.</p>
            </div>
            <button className="tiny-link" type="button" onClick={() => director.go("/universe/timeline")}>quietly held · {state?.outcomes_returned ?? orbit.glows}</button>
          </div>
          <div className="glow-row">
            {[
              orbit.plan ? `Plan open: ${orbit.plan.title}` : "No plan yet. Begin one honest route.",
              orbit.journal[0]?.body ?? "No journal trace yet. Keep one line.",
              orbit.thread.at(-1)?.text ?? "No Talk turn yet. Say one true line.",
            ].map((g, i) => (
              <button className="glow-item" key={i} type="button"
                      onClick={() => director.go(i === 0 ? "/plan" : i === 1 ? "/journal" : "/talk")}>
                <span className="glow-icon nur-v136-v89-mini-host nur-exact-icon-shell"><ExactMiniStar size="nur-mini-16" /></span>
                <span>{g}</span>
                <time>{["plan", "journal", "talk"][i]}</time>
              </button>
            ))}
          </div>
        </aside>
      </div>

      <article className="nur-panel panel-pad talk-mini">
        <div className="panel-top">
          <div>
            <h2 className="panel-title">Say it plainly.</h2>
            <p className="panel-sub">NUR can help you separate signal, feeling and next move.</p>
          </div>
          <button className="tiny-link" type="button" onClick={() => director.go("/talk")}>open chamber →</button>
        </div>
        <p className="mini-thread">“I am trying to build something beautiful without losing the thread of why.”</p>
        <div className="thought-composer">
          <input id="today-input" placeholder="What is most alive in you right now?"
                 value={orbit.draft} onChange={e => orbit.setDraft(e.target.value)}
                 onKeyDown={e => { if (e.key === "Enter" && orbit.draft.trim()) { nav("/talk"); } }} />
          <button className="thought-send-button send-holo-pill" aria-label="Send reflection" type="button"
                  onClick={() => orbit.draft.trim() && nav("/talk")}>
            <span>Send</span>
            <svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true"><path d="M3 12h14" stroke="currentColor" strokeWidth="1.6" fill="none"/><path d="M13 6l6 6-6 6" stroke="currentColor" strokeWidth="1.6" fill="none"/></svg>
          </button>
        </div>
      </article>
    </section>
  );
}
