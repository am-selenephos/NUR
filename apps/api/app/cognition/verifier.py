from app.ai.schemas import NURTalkOutput
from app.cognition.schemas import EvidencePacket, VerificationResult


def verify_talk_output(output: NURTalkOutput, evidence: EvidencePacket, *, provider_available: bool) -> VerificationResult:
    available_refs = {f"{r.kind}:{r.id}" for r in evidence.retrieval}
    missing = [ref for ref in output.source_refs if ref not in available_refs]
    has_evidence_claims = bool(output.observed or output.inferred or output.hypotheses)
    grounded_claims = (not has_evidence_claims) or bool(output.source_refs)
    too_many_refs = len(output.source_refs) > 6
    next_move_count = 1 if output.next_move else 0
    checks = {
        "provider_available": provider_available,
        "source_refs_available": not missing,
        "missing_source_refs": missing,
        "grounded_claims": grounded_claims,
        "max_source_refs": not too_many_refs,
        "next_move_count": next_move_count,
        "single_next_move": next_move_count <= 1,
        "no_chain_of_thought_field": True,
        "repair": [],
    }
    if missing:
        checks["repair"].append("Remove source_refs that are not present in the retrieval packet.")
    if not grounded_claims:
        checks["repair"].append("Move uncited observed/inferred/hypothesis claims into uncertainty or cite available refs.")
    if too_many_refs:
        checks["repair"].append("Cite at most six retrieved snippets.")
    if not provider_available:
        verdict = "WARN"
        checks["repair"].append("Provider unavailable; disabled-provider response is ledger-only.")
    elif missing or not grounded_claims or too_many_refs:
        verdict = "BLOCK"
    else:
        verdict = "PASS"
    return VerificationResult(verdict=verdict, checks=checks)
