import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import OmegaClaim, OmegaExperience
from app.omega.claim_service import create_claim
from app.omega.confirmation_policy import confirmation_reason
from app.omega.review_queue_service import queue_claim_candidate
from app.omega.schemas import OmegaClaimCandidate, OmegaClaimIn


def extract_claim_candidates(experience: OmegaExperience) -> list[OmegaClaimCandidate]:
    if experience.sensitivity == "SECRET_EXCLUDED":
        return []
    claim_type = _claim_type(experience.event_kind, experience.summary)
    if claim_type is None:
        return []
    claim_text = _normalize_claim_text(experience.summary)
    provenance = experience.provenance_label
    truth_status = _truth_status_for_experience(experience)
    reason = confirmation_reason(experience, claim_text=claim_text, truth_status=truth_status)
    return [
        OmegaClaimCandidate(
            claim_text=claim_text,
            claim_type=claim_type,
            truth_status=truth_status,
            confidence=float(experience.confidence or 0.5),
            sensitivity=experience.sensitivity,
            requires_owner_confirmation=reason is not None,
            confirmation_reason=reason,
            source_experience_id=experience.id,
            provenance_label=provenance,
        )
    ]


async def extract_or_queue_claims(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    experience: OmegaExperience,
) -> tuple[int, int]:
    created = 0
    queued = 0
    for candidate in extract_claim_candidates(experience):
        if await _claim_exists(db, owner_user_id=owner_user_id, claim_text=candidate.claim_text):
            continue
        if candidate.requires_owner_confirmation:
            await queue_claim_candidate(
                db,
                owner_user_id=owner_user_id,
                candidate=candidate,
                orbit_id=experience.orbit_id,
                reason=candidate.confirmation_reason or "owner confirmation required",
            )
            queued += 1
            continue
        await create_claim(
            db,
            owner_user_id=owner_user_id,
            payload=OmegaClaimIn(
                claim_text=candidate.claim_text,
                claim_type=candidate.claim_type,
                truth_status=candidate.truth_status,
                provenance_label=candidate.provenance_label,
                orbit_id=experience.orbit_id,
                confidence=candidate.confidence,
                evidence_id=experience.id,
                evidence_kind="EXPERIENCE",
            ),
        )
        created += 1
    return created, queued


async def _claim_exists(db: AsyncSession, *, owner_user_id: uuid.UUID, claim_text: str) -> bool:
    row = (await db.execute(select(OmegaClaim.id).where(
        OmegaClaim.owner_user_id == owner_user_id,
        OmegaClaim.claim_text == claim_text,
    ).limit(1))).scalar_one_or_none()
    return row is not None


def _normalize_claim_text(summary: str) -> str:
    return re.sub(r"\s+", " ", summary).strip()[:1600]


def _truth_status_for_experience(experience: OmegaExperience) -> str:
    if experience.provenance_label in {"OWNER_WRITTEN", "OBSERVED_OUTCOME", "SYSTEM_MEASURED"}:
        return "OBSERVED"
    if experience.provenance_label == "USER_CORRECTION":
        return "OBSERVED"
    if experience.provenance_label == "MODEL_GENERATED":
        return "INFERRED"
    return "HYPOTHESIS"


def _claim_type(event_kind: str, summary: str) -> str | None:
    lowered = f"{event_kind} {summary}".lower()
    if "constraint" in lowered or "must not" in lowered or "never" in lowered:
        return "CONSTRAINT"
    if event_kind in {"PLAN_CREATED", "PLAN_STEP"}:
        return "DECISION"
    if "decision" in lowered or "decide" in lowered:
        return "DECISION"
    if event_kind == "OUTCOME_REPORTED":
        return "PATTERN"
    if event_kind == "USER_CORRECTION":
        return "RISK"
    if event_kind == "MODEL_RESPONSE":
        return "HYPOTHESIS"
    if "prefer" in lowered or "preference" in lowered:
        return "PREFERENCE"
    return None
