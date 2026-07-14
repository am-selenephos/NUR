import { useEffect, useMemo, useState } from "react";
import BidiText from "../../components/BidiText";
import {
  nur,
  type OmegaClaim,
  type OmegaDashboard,
  type OmegaEvidence,
  type OmegaWhyChanged,
} from "../../lib/api";

export default function Omega({ initialPanel = "dashboard" }: { initialPanel?: "dashboard" | "review" }) {
  const [data, setData] = useState<OmegaDashboard | null>(null);
  const [selectedClaimId, setSelectedClaimId] = useState<string | null>(null);
  const [evidence, setEvidence] = useState<OmegaEvidence[]>([]);
  const [whyChanged, setWhyChanged] = useState<OmegaWhyChanged | null>(null);
  const [exportCount, setExportCount] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const selectedClaim = useMemo(
    () => data?.claims.find(c => c.id === selectedClaimId) ?? data?.claims[0] ?? null,
    [data, selectedClaimId],
  );

  async function refresh() {
    const next = await nur.omegaDashboard();
    setData(next);
    setSelectedClaimId(id => id ?? next.claims[0]?.id ?? null);
  }

  useEffect(() => { void refresh(); }, []);
  useEffect(() => {
    if (!selectedClaim) { setEvidence([]); setWhyChanged(null); return; }
    void nur.omegaClaimEvidence(selectedClaim.id).then(setEvidence);
    void nur.omegaWhyChanged(selectedClaim.id).then(setWhyChanged);
  }, [selectedClaim?.id]);

  async function runConsolidation() {
    setBusy(true);
    try {
      await nur.omegaConsolidate();
      await refresh();
    } finally {
      setBusy(false);
    }
  }

  async function refreshExport() {
    const exported = await nur.omegaExport();
    setExportCount(Object.values(exported.counts).reduce((total, value) => total + Number(value || 0), 0));
  }

  if (!data) {
    return (
      <section className="nur-page active omega-page" id="page-omega">
        <p className="page-kicker">NUR-Omega Research</p>
        <h1 className="page-title">Private cognition substrate<br /><em>loading softly.</em></h1>
      </section>
    );
  }

  return (
    <section className="nur-page active omega-page" id="page-omega" data-testid="omega-research-page">
      <p className="page-kicker">NUR-Omega Research</p>
      <h1 className="page-title">A private evidence layer<br /><em>for becoming less wrong.</em></h1>
      <p className="page-sub">
        NUR-Omega tracks evidence, claims, contradictions, predictions, corrections, and governed learning proposals.
        It is not a sentience, AGI, soul, or consciousness claim.
      </p>

      <div className="omega-status-strip" aria-label="Omega implementation status">
        {Object.entries(data.statuses).slice(0, 6).map(([key, value]) => (
          <span key={key}><b>{value}</b><em>{key.replaceAll("_", " ")}</em></span>
        ))}
      </div>

      <div className="omega-grid">
        <article className="nur-panel omega-panel omega-learning">
          <div className="omega-panel-head">
            <span>What NUR is learning</span>
            <button type="button" onClick={runConsolidation} disabled={busy} data-testid="omega-run-consolidation">
              {busy ? "Consolidating..." : "Run quiet consolidation"}
            </button>
          </div>
          <OmegaMetric label="Claims strengthened" value={data.claims.filter(c => c.support_count > 0).length} />
          <OmegaMetric label="Claims weakened" value={data.claims.filter(c => c.contradiction_count > 0).length} />
          <OmegaMetric label="Open contradictions" value={data.contradictions.length} />
          <OmegaMetric label="Open predictions" value={data.predictions.filter(p => p.status === "OPEN").length} />
          <OmegaMetric label="Recent corrections" value={data.recent_experiences.filter(e => e.provenance_label === "USER_CORRECTION").length} />
          <OmegaMetric label="Consolidation runs" value={data.consolidation_runs.length} />
          <OmegaMetric label="Review queue" value={data.review_queue.length} />
        </article>

        <article className="nur-panel omega-panel omega-evidence" data-testid="omega-evidence-graph">
          <div className="omega-panel-head">
            <span>Evidence Graph</span>
            <small>{selectedClaim ? selectedClaim.truth_status : "No claim yet"}</small>
          </div>
          <div className="omega-claim-list">
            {data.claims.length === 0 && <p>No Omega claims yet. Run consolidation after real owner events.</p>}
            {data.claims.map(claim => (
              <button key={claim.id} type="button" className={selectedClaim?.id === claim.id ? "active" : ""}
                      onClick={() => setSelectedClaimId(claim.id)}>
                <b><BidiText>{claim.claim_text}</BidiText></b>
                <em>{claim.claim_type} · {Math.round(claim.confidence * 100)}%</em>
              </button>
            ))}
          </div>
          {selectedClaim && (
            <div className="omega-claim-detail">
              <ClaimActions claim={selectedClaim} onRefresh={refresh} />
              <p><BidiText>{selectedClaim.claim_text}</BidiText></p>
              <div className="omega-edge-list">
                {evidence.length === 0 && <span>No evidence edge loaded yet.</span>}
                {evidence.map(edge => (
                  <span key={edge.id} className={edge.relation.toLowerCase()}>
                    {edge.relation} · {edge.evidence_kind} · strength {edge.strength}
                  </span>
                ))}
              </div>
              {whyChanged && (
                <div className="omega-why-changed" data-testid="omega-why-changed">
                  <b>Why NUR changed its mind</b>
                  {whyChanged.changed_because.map((line, index) => <span key={index}><BidiText>{line}</BidiText></span>)}
                  {whyChanged.supporting_edges.slice(0, 3).map((line, index) => <em key={`s-${index}`}>{line}</em>)}
                  {whyChanged.contradicting_edges.slice(0, 3).map((line, index) => <em key={`c-${index}`}>{line}</em>)}
                  {whyChanged.unresolved_note && <small>{whyChanged.unresolved_note}</small>}
                </div>
              )}
            </div>
          )}
        </article>

        <article className={`nur-panel omega-panel ${initialPanel === "review" ? "omega-panel-focus" : ""}`} data-testid="omega-review-queue">
          <div className="omega-panel-head">
            <span>Sensitive Claim Review</span>
            <small>owner confirmation gate</small>
          </div>
          {data.review_queue.map(item => (
            <div className="omega-card-row" key={item.id}>
              <b>{item.sensitivity} · {item.candidate_claim_type}</b>
              <span><BidiText>{item.candidate_claim_text}</BidiText></span>
              <em>{item.reason}</em>
              <div className="omega-button-row">
                <button type="button" data-testid="omega-review-approve" onClick={async () => { await nur.omegaReviewAction(item.id, "approve"); await refresh(); }}>Approve as inferred</button>
                <button type="button" data-testid="omega-review-reject" onClick={async () => { await nur.omegaReviewAction(item.id, "reject"); await refresh(); }}>Reject</button>
              </div>
            </div>
          ))}
          {data.review_queue.length === 0 && <p>No sensitive inferred claim is waiting. That is allowed.</p>}
        </article>

        <article className="nur-panel omega-panel" data-testid="omega-open-predictions">
          <div className="omega-panel-head"><span>Open Predictions</span><small>return outcome</small></div>
          {data.predictions.map(p => (
            <div className="omega-card-row" key={p.id}>
              <b><BidiText>{p.prediction_text}</BidiText></b>
              <span>Expected: <BidiText>{p.expected_observation}</BidiText></span>
              <em>{p.status} · {Math.round(p.confidence * 100)}%</em>
            </div>
          ))}
          {data.predictions.length === 0 && <p>No predictions yet.</p>}
        </article>

        <article className="nur-panel omega-panel" data-testid="omega-contradiction-review">
          <div className="omega-panel-head"><span>Contradictions</span><small>review gently</small></div>
          {data.contradictions.map(c => (
            <div className="omega-card-row contradiction" key={c.id}>
              <b>{c.severity} · {c.status}</b>
              <span><BidiText>{c.description}</BidiText></span>
              <button type="button" data-testid="omega-resolve-contradiction" onClick={async () => { await nur.omegaResolveContradiction(c.id); await refresh(); }}>
                Resolve
              </button>
            </div>
          ))}
          {data.contradictions.length === 0 && <p>No open contradiction.</p>}
        </article>

        <article className="nur-panel omega-panel" data-testid="omega-consolidation-run">
          <div className="omega-panel-head"><span>Consolidation</span><small>count-only summaries</small></div>
          {data.consolidation_runs.map(run => (
            <div className="omega-card-row" key={run.id}>
              <b>{run.status} · {run.run_kind}</b>
              <span>{run.created_claims} claims, {run.contradictions_found} contradictions, {run.predictions_resolved} predictions resolved.</span>
              <em>{new Date(run.created_at).toLocaleString()}</em>
            </div>
          ))}
          {data.consolidation_runs.length === 0 && <p>No consolidation run yet.</p>}
        </article>

        <article className="nur-panel omega-panel" data-testid="omega-learning-proposals">
          <div className="omega-panel-head">
            <span>Learning Proposals</span>
            <button type="button" onClick={refreshExport} data-testid="omega-export-owner">Owner export</button>
          </div>
          {exportCount !== null && <p data-testid="omega-export-status">Owner export prepared with {exportCount} structured row(s); raw dumps and chain-of-thought excluded.</p>}
          {data.learning_proposals.map(p => (
            <div className="omega-card-row" key={p.id}>
              <b>{p.proposal_kind} · {p.risk_level}</b>
              <span><BidiText>{p.description}</BidiText></span>
              <div className="omega-button-row">
                <button type="button" data-testid="omega-learning-approve" onClick={async () => { await nur.omegaLearningAction(p.id, "approve"); await refresh(); }}>Approve</button>
                <button type="button" data-testid="omega-learning-reject" onClick={async () => { await nur.omegaLearningAction(p.id, "reject"); await refresh(); }}>Reject</button>
                <button type="button" data-testid="omega-learning-rollback" onClick={async () => { await nur.omegaLearningAction(p.id, "rollback"); await refresh(); }}>Rollback</button>
              </div>
            </div>
          ))}
          {data.learning_proposals.length === 0 && <p>No learning proposal yet. Omega cannot rewrite itself.</p>}
        </article>
      </div>
    </section>
  );
}

function OmegaMetric({ label, value }: { label: string; value: number }) {
  return <div className="omega-metric"><b>{value}</b><span>{label}</span></div>;
}

function ClaimActions({ claim, onRefresh }: { claim: OmegaClaim; onRefresh: () => Promise<void> }) {
  return (
    <div className="omega-button-row">
      <button type="button" data-testid="omega-claim-confirm" onClick={async () => { await nur.omegaConfirmClaim(claim.id); await onRefresh(); }}>Confirm</button>
      <button type="button" data-testid="omega-claim-retire" onClick={async () => { await nur.omegaRetireClaim(claim.id); await onRefresh(); }}>Retire</button>
      <button type="button" data-testid="omega-claim-mark-wrong" onClick={async () => { await nur.omegaRetireClaim(claim.id); await onRefresh(); }}>Mark wrong</button>
    </div>
  );
}
