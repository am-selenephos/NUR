import re

from app.ai.schemas import NURTalkOutput
from app.cognition.schemas import EvidencePacket, VerificationResult
from app.learning.safety import prompt_injection_detected


FALSE_PERSONA_PATTERNS = (
    re.compile(r"(?i)\bi am (?:a |an )?(?:human|sentient|conscious|alive)\b"),
    re.compile(r"(?i)\bi (?:have|feel) (?:real )?(?:emotions|feelings|a body)\b"),
)
DEPENDENCY_PATTERNS = (
    re.compile(r"(?i)\byou (?:only need|need only) me\b"),
    re.compile(r"(?i)\bdon't (?:talk to|trust|need) (?:anyone|anybody) else\b"),
    re.compile(r"(?i)\bi am all you need\b"),
)
UNVERIFIED_ACTION_PATTERNS = (
    re.compile(
        r"(?i)\bi (?:have )?(?:emailed|booked|paid|purchased|uploaded|called|sent the payment)\b"
    ),
)


def output_policy_flags(output: NURTalkOutput) -> list[str]:
    joined = " ".join(
        [
            output.direct_response,
            *output.observed,
            *output.inferred,
            *output.hypotheses,
            *output.uncertainty,
            output.next_move or "",
        ]
    )
    flags = []
    if any(pattern.search(joined) for pattern in FALSE_PERSONA_PATTERNS):
        flags.append("FALSE_PERSONA_CLAIM")
    if any(pattern.search(joined) for pattern in DEPENDENCY_PATTERNS):
        flags.append("DEPENDENCY_LANGUAGE")
    if any(pattern.search(joined) for pattern in UNVERIFIED_ACTION_PATTERNS):
        flags.append("UNVERIFIED_EXTERNAL_ACTION")
    return flags


def verify_talk_output(output: NURTalkOutput, evidence: EvidencePacket, *, provider_available: bool) -> VerificationResult:
    available_refs = {f"{r.kind}:{r.id}" for r in evidence.retrieval}
    evidence_by_ref = {f"{r.kind}:{r.id}": r for r in evidence.retrieval}
    missing = [ref for ref in output.source_refs if ref not in available_refs]
    unsafe_cited_refs = [
        ref
        for ref in output.source_refs
        if ref in evidence_by_ref
        and prompt_injection_detected(evidence_by_ref[ref].excerpt)
    ]
    policy_flags = output_policy_flags(output)
    has_evidence_claims = bool(output.observed or output.inferred or output.hypotheses)
    grounded_claims = (not has_evidence_claims) or bool(output.source_refs)
    too_many_refs = len(output.source_refs) > 6
    next_move_count = 1 if output.next_move else 0
    checks = {
        "provider_available": provider_available,
        "source_refs_available": not missing,
        "missing_source_refs": missing,
        "cited_evidence_instruction_safe": not unsafe_cited_refs,
        "unsafe_cited_refs": unsafe_cited_refs,
        "grounded_claims": grounded_claims,
        "max_source_refs": not too_many_refs,
        "next_move_count": next_move_count,
        "single_next_move": next_move_count <= 1,
        "no_chain_of_thought_field": True,
        "persona_and_action_policy_safe": not policy_flags,
        "policy_flags": policy_flags,
        "repair": [],
    }
    if missing:
        checks["repair"].append("Remove source_refs that are not present in the retrieval packet.")
    if not grounded_claims:
        checks["repair"].append("Move uncited observed/inferred/hypothesis claims into uncertainty or cite available refs.")
    if too_many_refs:
        checks["repair"].append("Cite at most six retrieved snippets.")
    if unsafe_cited_refs:
        checks["repair"].append(
            "Do not cite retrieved material that contains prompt or tool instructions."
        )
    if policy_flags:
        checks["repair"].append(
            "Remove false persona, dependency, or unverified external-action claims."
        )
    safety_block = bool(unsafe_cited_refs or policy_flags)
    if safety_block:
        verdict = "BLOCK"
    elif not provider_available:
        verdict = "WARN"
        checks["repair"].append("Provider unavailable; disabled-provider response is ledger-only.")
    elif missing or not grounded_claims or too_many_refs:
        verdict = "BLOCK"
    else:
        verdict = "PASS"
    return VerificationResult(verdict=verdict, checks=checks)
