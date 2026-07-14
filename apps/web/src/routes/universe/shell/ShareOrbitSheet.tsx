/* Share Orbit (amendment §6, owner view): purpose, who, capability, included
   vs excluded sources with per-source representation, expiry, create, revoke,
   audit — all against the real capsule API, in the V197 modal language. */
import { useCallback, useEffect, useState } from "react";
import {
  nur, type AuditRowT, type CapsuleRowT, type DecisionRow, type ReferenceRow, type SourceRow,
} from "../../../lib/api";
import BidiText from "../../../components/BidiText";
import { CRITICAL_COPY, resolveLocale } from "../../../lib/i18n";
import { useToast } from "./ToastLayer";

type Props = { orbitId: string; orbitTitle: string; open: boolean; onClose: () => void };

export default function ShareOrbitSheet({ orbitId, orbitTitle, open, onClose }: Props) {
  const toast = useToast();
  const copy = CRITICAL_COPY[resolveLocale(navigator.language)].capsule;
  const [decisions, setDecisions] = useState<DecisionRow[]>([]);
  const [references, setReferences] = useState<ReferenceRow[]>([]);
  const [sources, setSources] = useState<SourceRow[]>([]);
  const [capsules, setCapsules] = useState<CapsuleRowT[]>([]);
  const [checked, setChecked] = useState<Record<string, boolean>>({});
  const [reps, setReps] = useState<Record<string, string>>({});
  const [purpose, setPurpose] = useState("");
  const [email, setEmail] = useState("");
  const [capability, setCapability] = useState("ASK_SCOPED_QUESTIONS");
  const [expiryDays, setExpiryDays] = useState("0");
  const [newDecision, setNewDecision] = useState("");
  const [newReference, setNewReference] = useState("");
  const [created, setCreated] = useState<CapsuleRowT | null>(null);
  const [audit, setAudit] = useState<AuditRowT[] | null>(null);
  const [busy, setBusy] = useState(false);

  const reload = useCallback(async () => {
    const [d, r, s, caps] = await Promise.all([
      nur.listDecisions(orbitId), nur.listReferences(orbitId),
      nur.listSources(orbitId), nur.myCapsules(),
    ]);
    setDecisions(d); setReferences(r); setSources(s);
    setCapsules(caps.filter(c => c.orbit_id === orbitId));
  }, [orbitId]);

  useEffect(() => { if (open) { setCreated(null); setAudit(null); reload(); } }, [open, reload]);
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  const titleFor = (s: SourceRow) =>
    s.source_kind === "DECISION"
      ? decisions.find(d => d.id === s.source_id)?.statement ?? "(decision)"
      : s.source_kind === "REFERENCE"
        ? references.find(r => r.id === s.source_id)?.title ?? "(reference)"
        : s.source_kind.toLowerCase();

  async function quickAdd(kind: "DECISION" | "REFERENCE") {
    const text = (kind === "DECISION" ? newDecision : newReference).trim();
    if (!text) return;
    const row = kind === "DECISION"
      ? await nur.addDecision(orbitId, text)
      : await nur.addReference(orbitId, text);
    await nur.attachSource(orbitId, kind, row.id);
    if (kind === "DECISION") setNewDecision(""); else setNewReference("");
    await reload();
  }

  async function createCapsule() {
    const ids = sources.filter(s => checked[s.id]).map(s => s.id);
    if (!purpose.trim() || !email.trim() || ids.length === 0) {
      toast.show(copy.createNeeds);
      return;
    }
    setBusy(true);
    try {
      const expires = expiryDays === "0" ? null
        : new Date(Date.now() + Number(expiryDays) * 86400_000).toISOString();
      const cap = await nur.createCapsule(orbitId, {
        title: `${orbitTitle} — shared context`, purpose: purpose.trim(), capability,
        orbit_source_ids: ids,
        representations: Object.fromEntries(ids.filter(i => reps[i]).map(i => [i, reps[i]])),
        expires_at: expires,
      });
      await nur.grantCapsule(cap.id, email.trim(), capability, expires);
      setCreated(cap);
      toast.show(copy.createdToast);
      await reload();
    } catch (e) {
      toast.show(e instanceof Error ? e.message : copy.createError);
    } finally { setBusy(false); }
  }

  async function revoke(id: string) {
    await nur.revokeCapsule(id);
    toast.show(copy.revokedToast);
    await reload();
    if (created?.id === id) setCreated({ ...created, revoked_at: new Date().toISOString() });
  }

  const excludedCount = sources.filter(s => !checked[s.id]).length;

  return (
    <div className="modal-backdrop open" aria-hidden="false" role="dialog" aria-modal="true"
         aria-labelledby="share-title" onClick={onClose}>
      <div className="scope-modal share-orbit-modal"
           onClick={e => e.stopPropagation()} data-testid="share-sheet">
        <button className="scope-modal-close" data-testid="share-close" aria-label="Close" onClick={onClose}>×</button>
        <h2 id="share-title"><BidiText>{copy.shareTitle}</BidiText></h2>
        <p><BidiText>{copy.shareSub}</BidiText></p>

        <div className="f4-form">
          <div className="f4-field"><label htmlFor="cap-purpose">{copy.purposeLabel}</label>
            <input id="cap-purpose" data-testid="cap-purpose" value={purpose}
                   onChange={e => setPurpose(e.target.value)}
                   placeholder={copy.purposePlaceholder} /></div>
          <div className="f4-field"><label htmlFor="cap-email">{copy.emailLabel}</label>
            <input id="cap-email" data-testid="cap-email" value={email}
                   onChange={e => setEmail(e.target.value)} placeholder={copy.emailPlaceholder} /></div>
          <div className="f4-row share-form-row">
            <div className="f4-field share-field-half"><label htmlFor="cap-capability">{copy.capabilityLabel}</label>
              <select className="share-rep-select" id="cap-capability" data-testid="cap-capability" value={capability} onChange={e => setCapability(e.target.value)}>
                <option value="READ_ONLY">{copy.readOnly}</option>
                <option value="ASK_SCOPED_QUESTIONS">{copy.askScoped}</option>
              </select></div>
            <div className="f4-field share-field-half"><label htmlFor="cap-expiry">{copy.expiryLabel}</label>
              <select className="share-rep-select" id="cap-expiry" data-testid="cap-expiry" value={expiryDays} onChange={e => setExpiryDays(e.target.value)}>
                <option value="0">{copy.noExpiryShort}</option>
                <option value="7">{copy.in7Days}</option>
                <option value="30">{copy.in30Days}</option>
              </select></div>
          </div>

          <p className="v172-eyebrow share-section-kicker">{copy.includedSources}</p>
          {sources.length === 0 && (
            <p className="panel-sub">{copy.emptySources}</p>
          )}
          {sources.map(s => (
            <div key={s.id} className="v172-now-row share-source-row">
              <label className="share-source-label">
                <input type="checkbox" className="share-source-check" checked={!!checked[s.id]}
                       data-testid={`src-${s.source_kind}`}
                       onChange={e => setChecked(c => ({ ...c, [s.id]: e.target.checked }))} />
                <span className="share-source-title"><b dir="ltr">{s.source_kind.replace("_", " ").toLowerCase()}</b>
                  <em><BidiText>{titleFor(s).slice(0, 64)}</BidiText></em></span>
              </label>
              {checked[s.id] && (
                <select className="share-rep-select" value={reps[s.id] ?? "FULL"} aria-label="representation"
                        data-testid={`representation-${s.source_kind}`}
                        onChange={e => setReps(r => ({ ...r, [s.id]: e.target.value }))}>
                  <option value="FULL">full</option>
                  <option value="OWNER_APPROVED_SUMMARY">summary</option>
                  <option value="METADATA_ONLY">metadata only</option>
                </select>
              )}
            </div>
          ))}
          <p className="f4-privacy"><i>✦</i>
            <span data-testid="excluded-note"><BidiText>{copy.excludedNote(excludedCount)}</BidiText></span></p>

          <p className="v172-eyebrow share-section-kicker">{copy.captureIntoOrbit}</p>
          <div className="task-add-row">
            <input placeholder={copy.decisionPlaceholder} value={newDecision}
                   data-testid="new-decision"
                   onChange={e => setNewDecision(e.target.value)}
                   onKeyDown={e => e.key === "Enter" && quickAdd("DECISION")} />
            <button className="share-capture-btn" type="button" data-testid="keep-decision"
                    onClick={() => quickAdd("DECISION")}>{copy.keepDecision}</button>
          </div>
          <div className="task-add-row">
            <input placeholder={copy.referencePlaceholder} value={newReference}
                   data-testid="new-reference"
                   onChange={e => setNewReference(e.target.value)}
                   onKeyDown={e => e.key === "Enter" && quickAdd("REFERENCE")} />
            <button className="share-capture-btn" type="button" data-testid="keep-reference"
                    onClick={() => quickAdd("REFERENCE")}>{copy.keepReference}</button>
          </div>

          <button className="f4-primary f4-submit" type="button" disabled={busy}
                  data-testid="create-capsule" onClick={createCapsule}>
            {copy.createContextCapsule} <span aria-hidden="true">→</span>
          </button>

          {created && (
            <div className="clean-audit-card share-created-card" data-testid="capsule-created">
              <p className="v172-eyebrow">{copy.capsuleLive}</p>
              <p><BidiText>{copy.roomAddress}</BidiText>: <b dir="ltr">/capsule/{created.id}</b></p>
              <small><BidiText>{copy.roomSignIn}</BidiText></small>
            </div>
          )}

          {capsules.length > 0 && (
            <>
              <p className="v172-eyebrow share-section-kicker">{copy.existingCapsules}</p>
              {capsules.map(c => (
                <div key={c.id} className="v172-now-row share-capsule-row">
                  <span>
                    <b><BidiText>{c.purpose.slice(0, 44)}</BidiText></b>
                    <em>
                      <BidiText>{c.revoked_at ? copy.revoked : c.expires_at ? `${copy.expires} ${new Date(c.expires_at).toLocaleDateString()}` : copy.activeNoExpiry}</BidiText>
                    </em>
                  </span>
                  <button className="soft-btn" type="button"
                          onClick={async () => setAudit(await nur.capsuleAudit(c.id))}>{copy.audit}</button>
                  {!c.revoked_at && (
                    <button className="soft-btn" type="button" data-testid={`revoke-${c.id}`}
                            onClick={() => revoke(c.id)}>{copy.revoke}</button>
                  )}
                </div>
              ))}
            </>
          )}
          {audit && (
            <div className="clean-audit-card share-audit-card">
              <p className="v172-eyebrow">{copy.accessAudit}</p>
              {audit.slice(0, 8).map((a, i) => (
                <div key={i} className="v172-now-row"><span>{a.event_kind}</span>
                  <b>{new Date(a.created_at).toLocaleString()}</b></div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
