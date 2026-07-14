/* V183 Journal: the writing field is the hero; gentle doors; kept traces land
   as REAL persistent event-stars in the galaxy (nurGalaxy.addEvent). */
import { useState } from "react";
import { useOrbit } from "../../lib/orbitState";
import { useGalaxy } from "../../galaxy/GalaxyProvider";
import { nur } from "../../lib/api";

const DOORS = ["What happened?", "What do I need?", "What am I avoiding?", "What am I proud of?", "Do not analyze it."];

export default function Journal() {
  const orbit = useOrbit();
  const galaxy = useGalaxy();
  const [text, setText] = useState("");
  const [kept, setKept] = useState(false);
  const [converted, setConverted] = useState<string | null>(null);

  async function keep() {
    const t = text.trim();
    if (!t) return;
    await orbit.keepEntry(t);
    galaxy?.addEvent({ id: `journal-${Date.now()}`, type: t.length > 280 ? "journal_saved_long_reflection" : "journal_saved" });
    galaxy?.burst(innerWidth * 0.5, innerHeight * 0.35, 0.35);
    setText(""); setKept(true); setTimeout(() => setKept(false), 2200);
  }

  async function convert(kind: "decision" | "reference" | "constraint", entryId: string) {
    if (!orbit.activeOrbit) return;
    const targetKind = kind === "decision" ? "DECISION" : kind === "constraint" ? "CONSTRAINT" : "REFERENCE";
    await nur.convertJournal(entryId, orbit.activeOrbit.id, targetKind);
    setConverted(kind);
  }

  return (
    <section className="nur-page active" id="page-journal">
      <p className="page-kicker">Keep</p>
      <h1 className="page-title" id="journal-title">Let the thought<br /><em>leave a trace.</em></h1>
      <p className="page-sub">Writing is the hero here. No dashboards watching over your shoulder.</p>
      <div className="journal-layout">
        <article className="nur-panel journal-pad">
          <p className="journal-prompt">What are you trying not to lose?</p>
          <textarea id="journal-input" placeholder="Write without making it useful yet..."
                    value={text} onChange={e => setText(e.target.value)} />
          <div className="journal-tools">
            <div className="journal-tags">
              <span className="journal-tag">private</span>
              <span className="journal-tag">no analysis</span>
              <span className="journal-tag">today</span>
            </div>
            <button id="journal-save" className="f4-primary compact" type="button" onClick={keep}>
              {kept ? "Held ✦" : <>Keep this <span>→</span></>}
            </button>
          </div>
          {converted && <p className="f4-privacy"><i>✦</i><span>Converted to {converted} in {orbit.activeOrbit?.title}.</span></p>}
          {orbit.journal.length > 0 && (
            <div className="entry-list" style={{ marginTop: 18 }}>
              {orbit.journal.map(e => (
                <div className="entry-card" key={e.id}>
                  <div className="entry-date">{new Date(e.created_at).toLocaleDateString()} · private</div>
                  <div className="entry-body">{e.body}</div>
                  <div className="journal-convert-row">
                    <button type="button" disabled={!orbit.activeOrbit} onClick={() => convert("decision", e.id)}>convert to decision</button>
                    <button type="button" disabled={!orbit.activeOrbit} onClick={() => convert("reference", e.id)}>convert to reference</button>
                    <button type="button" disabled={!orbit.activeOrbit} onClick={() => convert("constraint", e.id)}>convert to constraint</button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </article>
        <aside className="nur-panel panel-pad">
          <h2 className="panel-title">Gentle doors</h2>
          <p className="panel-sub">Use one only if it opens something real.</p>
          <div className="context-list">
            {DOORS.map(d => (
              <button key={d} type="button" onClick={() => setText(t => (t ? t + "\n\n" : "") + d + " ")}>{d}</button>
            ))}
          </div>
        </aside>
      </div>
    </section>
  );
}
