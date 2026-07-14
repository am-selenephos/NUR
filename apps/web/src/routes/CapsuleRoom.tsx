/* Recipient room (amendment §6): a narrow, source-bound context space that
   never resembles chatting with a person. Distinct ACTIVE / REVOKED / EXPIRED
   states; every answer wears its mode and its sources. */
import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { ApiError, nur, type AnswerT, type CapsuleViewT } from "../lib/api";
import { CRITICAL_COPY, resolveLocale } from "../lib/i18n";

const MODE_COPY: Record<string, string> = {
  DIRECT_STATEMENT: "Direct statement — the owner's own written words.",
  APPROVED_CONTEXT_SUMMARY: "Approved context summary — assembled only from included sources.",
  INFERENCE: "Cautious inference from included sources.",
  NOT_AVAILABLE: "Not available in this capsule.",
};

export default function CapsuleRoom() {
  const { id = "" } = useParams();
  const copy = CRITICAL_COPY[resolveLocale(navigator.language)].capsule;
  const [view, setView] = useState<CapsuleViewT | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const [answers, setAnswers] = useState<AnswerT[]>([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    document.body.classList.add("universe-edition", "nur-universe-active");
    return () => document.body.classList.remove("universe-edition", "nur-universe-active");
  }, []);

  const load = useCallback(async () => {
    try { setView(await nur.capsuleView(id)); setError(null); }
    catch (e) { setError(e instanceof ApiError ? e.message : "This room could not be opened."); }
  }, [id]);
  useEffect(() => { load(); }, [load]);

  async function ask() {
    const q = question.trim();
    if (!q || !view) return;
    setBusy(true);
    try {
      const a = await nur.askCapsule(id, q);
      setAnswers(x => [a, ...x]);
      setQuestion("");
    } catch (e) {
      if (e instanceof ApiError && e.status === 410) { setAnswers([]); await load(); }
      else setError(e instanceof ApiError ? e.message : "The question could not be carried.");
    } finally { setBusy(false); }
  }

  if (error && !view) {
    return (
      <div className="nur-interior" style={{ minHeight: "100vh", display: "grid", placeItems: "center" }}>
        <article className="nur-panel panel-pad" style={{ maxWidth: 480 }}>
          <h2 className="panel-title">No room here.</h2>
          <p className="panel-sub">{error}</p>
        </article>
      </div>
    );
  }
  if (!view) return <div className="nur-splash"><p>Opening the shared room…</p></div>;

  const inactive = view.state !== "ACTIVE";

  return (
    <div className="nur-interior" style={{ minHeight: "100vh", overflowY: "auto" }} data-testid="capsule-room">
      <div style={{ maxWidth: 720, margin: "0 auto", padding: "56px 22px 80px" }}>
        <p className="page-kicker">{copy.kicker}</p>
        <h1 className="page-title" style={{ fontSize: 44 }}>
          {view.owner_display}'s shared context<br />
          <em>{view.state === "ACTIVE" ? copy.activeLine :
               view.state === "REVOKED" ? copy.revokedLine : copy.expiredLine}</em>
        </h1>
        <p className="page-sub" data-testid="safety-copy">{view.safety_copy}</p>

        <article className="nur-panel panel-pad capsule-top-card" style={{ marginTop: 22 }} data-testid="capsule-top-card">
          <div className="panel-top">
            <div>
              <h2 className="panel-title">{view.title}</h2>
              <p className="panel-sub">{copy.purpose}: {view.purpose}</p>
            </div>
            <span className={`system-badge${inactive ? "" : " live"}`} data-testid="capsule-state">
              {view.state}
            </span>
          </div>
          <div className="v172-now-row"><span>{copy.access}</span>
            <b>{view.capability === "ASK_SCOPED_QUESTIONS" ? "Scoped questions" : "Read only"}</b></div>
          <div className="v172-now-row"><span>{copy.expires}</span>
            <b>{view.expires_at ? new Date(view.expires_at).toLocaleDateString() : copy.noExpiry}</b></div>
          {view.recipient_instructions && (
            <div className="v172-now-row"><span>From the owner</span><b>{view.recipient_instructions}</b></div>
          )}
        </article>

        {inactive ? (
          <article className="clean-audit-card" style={{ marginTop: 16, padding: 18 }} data-testid="inactive-note">
            <p className="v172-eyebrow">{view.state}</p>
            <p>{copy.inactiveNote}</p>
          </article>
        ) : (
          <>
            <article className="nur-panel panel-pad" style={{ marginTop: 16 }}>
              <h2 className="panel-title">{copy.included}</h2>
              <p className="panel-sub">{copy.includedSub}</p>
              {view.included.map(s => (
                <div key={s.source_id} className="v172-fragment" style={{ width: "100%", textAlign: "left" }}>
                  <span>✦</span>
                  <p>
                    <b>{s.source_kind.replace("_", " ").toLowerCase()}</b>
                    {" · "}<em>{s.representation.replace(/_/g, " ").toLowerCase()}</em>
                    <span style={{ display: "block" }}>{s.title}</span>
                    {s.body && <small style={{ opacity: .85 }}>{s.body.slice(0, 180)}</small>}
                  </p>
                </div>
              ))}
              <h2 className="panel-title" style={{ marginTop: 16 }}>{copy.excluded}</h2>
              {view.excluded_summary.length === 0
                ? <p className="panel-sub">Nothing else exists in this Orbit's shareable set.</p>
                : view.excluded_summary.map((e, i) => (
                    <div key={i} className="v172-now-row" data-testid="excluded-row">
                      <span>{e.count}×</span><b>{e.source_kind.replace("_", " ").toLowerCase()} — {e.note}</b>
                    </div>
                  ))}
            </article>

            {view.capability === "ASK_SCOPED_QUESTIONS" && (
              <article className="nur-panel panel-pad" style={{ marginTop: 16 }}>
                <h2 className="panel-title">{copy.askTitle}</h2>
                <p className="panel-sub">{copy.askSub}</p>
                <div className="thought-composer">
                  <input id="capsule-question" data-testid="capsule-question" value={question}
                         placeholder={copy.askPlaceholder}
                         onChange={e => setQuestion(e.target.value)}
                         onKeyDown={e => e.key === "Enter" && ask()} />
                  <button className="thought-send-button send-holo-pill" type="button" aria-label="Ask"
                          disabled={busy} data-testid="capsule-ask" onClick={ask}>
                    <span>{copy.ask}</span>
                  </button>
                </div>
                {answers.map((a, i) => (
                  <div key={i} className="clean-audit-card" style={{ marginTop: 12, padding: 14 }}
                       data-testid="capsule-answer">
                    <p className="v172-eyebrow">{a.question}</p>
                    <p style={{ whiteSpace: "pre-line", margin: "8px 0" }}>{a.answer_text}</p>
                    <div className="v172-now-row"><span>mode</span>
                      <b data-testid="answer-mode">{MODE_COPY[a.answer_mode] ?? a.answer_mode}</b></div>
                    {a.source_refs.length > 0 && (
                      <div className="v172-now-row"><span>sources</span>
                        <b>{a.source_refs.map(r => `${r.source_kind.toLowerCase()} (${r.representation.toLowerCase()})`).join(" · ")}</b></div>
                    )}
                    {a.policy_explanation && (
                      <p className="f4-privacy"><i>✦</i><span>{a.policy_explanation}</span></p>
                    )}
                  </div>
                ))}
              </article>
            )}
          </>
        )}
      </div>
    </div>
  );
}
