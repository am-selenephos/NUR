/* V183 Talk chamber, now server-backed: every user line persists as TALK_TURN
   and every answer persists as MODEL_RESPONSE/model_run. Disabled provider
   states are surfaced honestly; no fake AI copy is generated in the client. */
import { useEffect, useRef, useState } from "react";
import { useOrbit } from "../../lib/orbitState";
import { ApiError, nur } from "../../lib/api";
import { useGalaxy } from "../../galaxy/GalaxyProvider";
import { useAuth } from "../../app/AuthProvider";
import BidiText from "../../components/BidiText";
import { CORE_COPY, CRITICAL_COPY, resolveLocale } from "../../lib/i18n";
import { queueEncryptedDraft } from "../../lib/offlineDrafts";
import { playQuietEvent } from "../../lib/quietSound";
import { V197_TALK_THREAD_ACTIONS } from "../../v197/contract";

const BOUNDARIES = ["Private", "Ephemeral", "System Shared", "Learning Candidate"] as const;

export default function Talk() {
  const orbit = useOrbit();
  const auth = useAuth();
  const galaxy = useGalaxy();
  const locale = resolveLocale(auth.user?.profile.locale ?? navigator.language);
  const copy = CORE_COPY[locale];
  const critical = CRITICAL_COPY[locale].talk;
  const [text, setText] = useState(orbit.draft);
  const [mode, setMode] = useState<"talk" | "reflect" | "challenge" | "summarize">("talk");
  const [correction, setCorrection] = useState("");
  const [recordingOutcome, setRecordingOutcome] = useState(false);
  const [outcomeDraft, setOutcomeDraft] = useState("");
  const [outcomeBusy, setOutcomeBusy] = useState(false);
  const [busy, setBusy] = useState(false);
  const streamRef = useRef<HTMLDivElement>(null);
  useEffect(() => { orbit.setDraft(""); }, []); // consumed the Today draft
  useEffect(() => { void orbit.loadThread(orbit.activeOrbit?.id ?? undefined); }, [orbit.activeOrbit?.id]);
  useEffect(() => { streamRef.current?.scrollTo({ top: 1e9, behavior: "smooth" }); }, [orbit.thread.length]);

  async function send(modeOverride?: typeof mode) {
    const line = text.trim();
    if (!line || busy) return;
    const requestedMode = modeOverride ?? mode;
    setBusy(true);
    setText("");
    orbit.setDraft("");
    orbit.say({ id: `u${Date.now()}`, who: "user", text: line });
    galaxy?.burst(innerWidth * 0.7, innerHeight * 0.45, 0.6);
    playQuietEvent("talk_send", auth.user?.profile.sound_enabled === true);
    try {
      const result = await nur.talk(
        line,
        orbit.activeOrbit?.id ?? undefined,
        requestedMode === "talk" ? undefined : requestedMode,
        locale,
        auth.user?.profile.writing_preference ?? "default",
      );
      orbit.say({
        id: result.response_event_id,
        who: "nur",
        text: result.output.direct_response,
        output: result.output,
        omega: result.omega,
        refs: result.evidence.retrieval.slice(0, 3).map(r => ({ kind: r.kind, excerpt: r.excerpt })),
        note: result.provider_available ? undefined : result.provider_reason ?? "AI provider unavailable.",
      });
      playQuietEvent("model_response", auth.user?.profile.sound_enabled === true);
      await orbit.loadThread(orbit.activeOrbit?.id ?? undefined);
    } catch (e) {
      await queueEncryptedDraft(line);
      orbit.say({ id: `e${Date.now()}`, who: "nur",
        text: e instanceof ApiError ? e.message : "The ledger could not be reached.",
        note: "Your draft was queued locally in encrypted browser storage for this session." });
    } finally { setBusy(false); }
  }

  function cycleBoundary() {
    const index = BOUNDARIES.indexOf(orbit.boundary as typeof BOUNDARIES[number]);
    orbit.setBoundary(BOUNDARIES[(index + 1) % BOUNDARIES.length]);
  }

  async function submitTalkOutcome() {
    const line = outcomeDraft.trim();
    if (!line || outcomeBusy) return;
    setOutcomeBusy(true);
    try {
      const step = await orbit.addStep("Record what changed from Talk", "Outcome returned from a Talk follow-up.");
      await orbit.recordOutcome(step.id, line);
      setOutcomeDraft("");
      setRecordingOutcome(false);
      galaxy?.burst(undefined, undefined, 0.4);
      playQuietEvent("outcome_kept", auth.user?.profile.sound_enabled === true);
    } finally {
      setOutcomeBusy(false);
    }
  }

  const threadActionLabels: Record<typeof V197_TALK_THREAD_ACTIONS[number]["key"], string> = {
    private: critical.keepPrivate,
    journal: critical.saveToJournal,
    plan: critical.makePlan,
    outcome: critical.recordWhatChanged,
  };
  const threadActionHandlers: Record<typeof V197_TALK_THREAD_ACTIONS[number]["key"], () => void | Promise<void>> = {
    private: () => orbit.setBoundary("Private"),
    journal: () => {
      const last = [...orbit.thread].reverse().find(m => m.who === "user");
      if (last) orbit.keepEntry(last.text);
    },
    plan: async () => {
      const last = [...orbit.thread].reverse().find(m => m.who === "user");
      if (!last) return;
      if (!orbit.plan) await orbit.beginRoute();
      await nur.createPlan(last.text.slice(0, 64), []);
    },
    outcome: () => setRecordingOutcome(v => !v),
  };

  return (
    <section className="nur-page active" id="page-talk">
      <p className="page-kicker">{critical.kicker}</p>
      <h1 className="page-title talk-page-title" id="talk-title">{critical.title}<br /><em>{critical.titleEmphasis}</em></h1>
      <p className="page-sub"><BidiText>{critical.subtitle}</BidiText></p>
      {critical.intentionalMixedRomanUrdu && (
        <p className="talk-language-note" data-testid="talk-language-note"><BidiText>{critical.intentionalMixedRomanUrdu}</BidiText></p>
      )}
      <div className="page-grid">
        <article className="nur-panel talk-chamber">
          <div className="talk-stream" id="talk-stream" ref={streamRef}>
            <div className="talk-message nur">
              <div className="talk-meta">NUR<span>✦</span></div>
              <BidiText>{critical.seed}</BidiText>
            </div>
            {orbit.thread.map(m => (
              <div key={m.id} className={`talk-message ${m.who}`}>
                {m.who === "nur" && <div className="talk-meta">NUR<span>✦</span></div>}
                <p><BidiText>{m.text}</BidiText></p>
                {m.output && (
                  <div className="talk-structured" aria-label="Structured NUR response">
                    {m.output.observed.length > 0 && <TalkList title={critical.observed} rows={m.output.observed} />}
                    {m.output.inferred.length > 0 && <TalkList title={critical.inferred} rows={m.output.inferred} />}
                    {m.output.hypotheses.length > 0 && <TalkList title={critical.hypotheses} rows={m.output.hypotheses} />}
                    {m.output.uncertainty.length > 0 && <TalkList title={critical.uncertainty} rows={m.output.uncertainty} />}
                    {m.output.next_move && (
                      <div className="talk-next-move">
                        <span>{critical.nextMove}</span><b><BidiText>{m.output.next_move}</BidiText></b>
                        <button type="button" data-testid="use-next-move-plan"
                                onClick={() => nur.createPlan(m.output!.next_move!.slice(0, 96), [{ title: m.output!.next_move! }])}>
                          {critical.useMoveInPlan}
                        </button>
                      </div>
                    )}
                  </div>
                )}
                {m.omega && (
                  <details className="talk-omega-holding" data-testid="talk-omega-holding">
                    <summary>NUR is holding</summary>
                    <p><BidiText>{m.omega.memory_note}</BidiText></p>
                    {m.omega.what_changed.length > 0 && <TalkList title="What changed" rows={m.omega.what_changed} />}
                    {m.omega.open_contradictions.length > 0 && <TalkList title="Open contradictions" rows={m.omega.open_contradictions} />}
                    {m.omega.unresolved_predictions.length > 0 && <TalkList title="Unresolved predictions" rows={m.omega.unresolved_predictions} />}
                  </details>
                )}
                {m.note && <small className="talk-note"><BidiText>{m.note}</BidiText></small>}
              </div>
            ))}
          </div>
          <div className="talk-composer">
            <div className="thought-composer">
              <input id="talk-input" placeholder={copy.askPlaceholder} value={text}
                     onChange={e => setText(e.target.value)}
                     onKeyDown={e => e.key === "Enter" && send()} />
              <button className="thought-send-button send-holo-pill" aria-label="Send to NUR" type="button" onClick={() => send()} disabled={busy}>
                <span>{busy ? critical.holding : critical.send}</span>
                <svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true"><path d="M3 12h14" stroke="currentColor" strokeWidth="1.6" fill="none"/><path d="M13 6l6 6-6 6" stroke="currentColor" strokeWidth="1.6" fill="none"/></svg>
              </button>
            </div>
            <div className="talk-mode-row" aria-label="Talk mode">
              {(["talk", "reflect", "challenge", "summarize"] as const).map(m => (
                <button key={m} type="button" className={mode === m ? "active" : ""} onClick={() => setMode(m)}>
                  {m === "reflect" ? critical.thinkDeeper : m === "challenge" ? critical.challenge : m === "summarize" ? critical.summarize : critical.modeTalk}
                </button>
              ))}
            </div>
            <div className="scope-row">
              <span className="scope-chip" /><strong>{orbit.boundary}</strong> · {critical.onlyThisOrbit}
              <button id="talk-scope" className="soft-button" type="button" onClick={cycleBoundary}>{critical.changeBoundary}</button>
            </div>
          </div>
        </article>
        <aside>
          <div className="context-rail-card">
            <h3>{critical.currentThread}</h3>
            <p><BidiText>{critical.currentThreadSub}</BidiText></p>
            <div className="context-list" aria-label="Thread actions">
              {V197_TALK_THREAD_ACTIONS.map(action => (
                <button key={action.key} type="button" data-thread-action={action.key}
                        data-testid={action.key === "outcome" ? "talk-record-outcome" : undefined}
                        onClick={() => { void threadActionHandlers[action.key](); }}>
                  {threadActionLabels[action.key]}
                </button>
              ))}
            </div>
            {recordingOutcome && (
              <div className="task-add-row talk-outcome-row" data-testid="talk-outcome-form">
                <input data-testid="talk-outcome-input" placeholder={critical.outcomePlaceholder}
                       value={outcomeDraft}
                       onChange={e => setOutcomeDraft(e.target.value)}
                       onKeyDown={e => e.key === "Enter" && submitTalkOutcome()} />
                <button type="button" data-testid="talk-submit-outcome" disabled={outcomeBusy || !outcomeDraft.trim()}
                        onClick={submitTalkOutcome}>{outcomeBusy ? critical.outcomeSaving : critical.outcomeSave}</button>
              </div>
            )}
          </div>
          <div className="context-rail-card">
            <h3>{critical.whatNurHolding}</h3>
            <p><BidiText>{orbit.thread.length ? critical.holdingPopulated(orbit.thread.length) : critical.holdingEmpty}</BidiText></p>
          </div>
          <div className="context-rail-card">
            <h3>{critical.correctModel}</h3>
            <p><BidiText>{critical.correctionSub}</BidiText></p>
            <div className="talk-correction-row">
              <input data-testid="talk-correction" value={correction} placeholder={critical.correctionPlaceholder}
                     onChange={e => setCorrection(e.target.value)} />
              <button type="button" data-testid="submit-correction" onClick={async () => {
                const line = correction.trim();
                if (!line) return;
                await nur.correct(line);
                setCorrection("");
              }}>{critical.saveCorrection}</button>
            </div>
          </div>
        </aside>
      </div>
    </section>
  );
}

function TalkList({ title, rows }: { title: string; rows: string[] }) {
  return (
    <section>
      <span>{title}</span>
      <ul>{rows.slice(0, 4).map(row => <li key={row}><BidiText>{row}</BidiText></li>)}</ul>
    </section>
  );
}
