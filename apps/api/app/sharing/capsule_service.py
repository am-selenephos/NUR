"""Context Capsule engine (amendment §3/§4): versioned source snapshots,
recipient-grant access, source-bound answers, immediate revocation, and a
complete audit trail.

`answer_from_capsule` is the constrained gateway method the amendment demands:
it may fetch ONLY the current version's capsule_sources representations —
never general owner retrieval, never hidden context. Answering is
deterministic extractive matching over those representations; INFERENCE mode
stays disabled until the model gateway phase and says so in
policy_explanation."""
import datetime as dt
import hashlib
import uuid
from dataclasses import dataclass

from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    CapsuleAccessEvent, CapsuleAnswer, CapsuleGrant, CapsuleQuestion,
    CapsuleSource, ContextCapsule, OrbitSource,
)

UTC = dt.timezone.utc


def email_hash(email: str) -> str:
    return hashlib.sha256(email.strip().lower().encode()).hexdigest()


def _now() -> dt.datetime:
    return dt.datetime.now(UTC)


def grant_active(grant: CapsuleGrant, capsule: ContextCapsule) -> tuple[bool, str]:
    now = _now()
    if capsule.revoked_at is not None or grant.revoked_at is not None:
        return False, "REVOKED"
    if capsule.expires_at is not None and capsule.expires_at <= now:
        return False, "EXPIRED"
    if grant.expires_at is not None and grant.expires_at <= now:
        return False, "EXPIRED"
    return True, "ACTIVE"


async def log_access(
    db: AsyncSession, *, capsule_id: uuid.UUID, actor_user_id: uuid.UUID,
    event_kind: str, grant_id: uuid.UUID | None = None, meta: dict | None = None,
) -> None:
    db.add(CapsuleAccessEvent(
        capsule_id=capsule_id, grant_id=grant_id, actor_user_id=actor_user_id,
        event_kind=event_kind, meta=meta or {},
    ))


# ---------------------------------------------------------------- hydration
@dataclass
class HydratedSource:
    capsule_source_id: str
    orbit_source_id: str
    source_kind: str
    source_id: str
    representation: str
    title: str
    body: str  # emptied for METADATA_ONLY, truncated for summaries


async def hydrate_capsule_sources(
    db: AsyncSession, *, capsule: ContextCapsule, viewer_user_id: uuid.UUID,
) -> list[HydratedSource]:
    """All hydration crosses ONE SECURITY DEFINER door (fn_hydrate_capsule),
    which itself enforces owner-or-active-grant and current-version-only.
    Representation shaping happens here so nothing beyond the granted form
    ever leaves this function (Rules 5/6)."""
    rows = (await db.execute(
        text("SELECT * FROM fn_hydrate_capsule(:cap, :usr)"),
        {"cap": str(capsule.id), "usr": str(viewer_user_id)})).all()
    out: list[HydratedSource] = []
    for r in rows:
        body = r.body or ""
        if r.representation == "METADATA_ONLY":
            body = ""
        elif r.representation == "OWNER_APPROVED_SUMMARY":
            body = body[:280]
        out.append(HydratedSource(
            capsule_source_id=str(r.capsule_source_id), orbit_source_id=str(r.orbit_source_id),
            source_kind=r.source_kind, source_id=str(r.source_id),
            representation=r.representation, title=r.title or "", body=body))
    return out


# ------------------------------------------------------------ capsule build
async def create_capsule(
    db: AsyncSession, *, owner_user_id: uuid.UUID, orbit_id: uuid.UUID,
    title: str, purpose: str, capability: str,
    orbit_source_ids: list[uuid.UUID], representations: dict[str, str] | None = None,
    recipient_instructions: str | None = None, expires_at: dt.datetime | None = None,
) -> ContextCapsule:
    """Immutable versioned snapshot: version 1 capsule_sources rows freeze the
    selection. Ownership of every orbit_source is verified against the caller
    (RLS enforces it again beneath)."""
    owned = (
        await db.execute(
            select(OrbitSource).where(
                OrbitSource.id.in_(orbit_source_ids),
                OrbitSource.owner_user_id == owner_user_id,
                OrbitSource.orbit_id == orbit_id,
            )
        )
    ).scalars().all()
    if len(owned) != len(set(orbit_source_ids)):
        raise PermissionError("Every capsule source must be an owned source of this orbit.")

    capsule = ContextCapsule(
        orbit_id=orbit_id, owner_user_id=owner_user_id, title=title, purpose=purpose,
        capability=capability, recipient_instructions=recipient_instructions,
        expires_at=expires_at, version=1,
    )
    db.add(capsule)
    await db.flush()
    reps = representations or {}
    for src in owned:
        db.add(CapsuleSource(
            capsule_id=capsule.id, capsule_version=1, orbit_source_id=src.id,
            included_representation=reps.get(str(src.id), "FULL"),
        ))
    return capsule


async def revoke_capsule(db: AsyncSession, *, capsule: ContextCapsule, owner_user_id: uuid.UUID) -> None:
    capsule.revoked_at = _now()
    await log_access(db, capsule_id=capsule.id, actor_user_id=owner_user_id, event_kind="REVOKED")


# -------------------------------------------------- constrained answer path
STOP = {"the","a","an","is","are","was","were","do","does","did","what","which","who","how","why","when","where","of","to","in","on","for","and","or","we","our","you","your","it","this","that","should","can"}


def _tokens(s: str) -> set[str]:
    return {w for w in "".join(c.lower() if c.isalnum() else " " for c in s).split() if len(w) > 2 and w not in STOP}


def _is_capsule_rls_denial(exc: SQLAlchemyError) -> bool:
    msg = str(exc).lower()
    return "row-level security policy" in msg and (
        "capsule_questions" in msg or "capsule_answers" in msg
    )


async def _raise_current_closed_state(
    db: AsyncSession, *, capsule_id: uuid.UUID, grant_id: uuid.UUID,
) -> None:
    await db.rollback()
    grant = (await db.execute(select(CapsuleGrant).where(CapsuleGrant.id == grant_id))).scalar_one_or_none()
    capsule = (await db.execute(select(ContextCapsule).where(ContextCapsule.id == capsule_id))).scalar_one_or_none()
    if grant is None or capsule is None:
        raise PermissionError("REVOKED")
    _, state = grant_active(grant, capsule)
    raise PermissionError(state)


async def answer_from_capsule(
    db: AsyncSession, *, capsule_id: uuid.UUID, grant_id: uuid.UUID,
    question: str, recipient_user_id: uuid.UUID,
) -> CapsuleAnswer:
    """The amendment's constrained method, verbatim in spirit:
    - validates the ACTIVE grant addressed to this recipient;
    - fetches ONLY current-version capsule source representations;
    - answers extractively from those and nothing else;
    - records question, answer, and both audit events."""
    grant = (await db.execute(select(CapsuleGrant).where(CapsuleGrant.id == grant_id))).scalar_one_or_none()
    capsule = (await db.execute(select(ContextCapsule).where(ContextCapsule.id == capsule_id))).scalar_one_or_none()
    if grant is None or capsule is None or grant.capsule_id != capsule.id:
        raise PermissionError("NO_GRANT")
    if grant.recipient_user_id != recipient_user_id:
        raise PermissionError("NO_GRANT")
    active, state = grant_active(grant, capsule)
    if not active:
        raise PermissionError(state)
    if grant.capability != "ASK_SCOPED_QUESTIONS":
        raise PermissionError("CAPABILITY")

    q = CapsuleQuestion(capsule_id=capsule.id, grant_id=grant.id, question=question)
    db.add(q)
    try:
        await db.flush()
    except SQLAlchemyError as exc:
        if _is_capsule_rls_denial(exc):
            await _raise_current_closed_state(db, capsule_id=capsule_id, grant_id=grant_id)
        raise
    await log_access(db, capsule_id=capsule.id, actor_user_id=recipient_user_id,
                     event_kind="QUESTION_ASKED", grant_id=grant.id, meta={"question_id": str(q.id)})

    sources = await hydrate_capsule_sources(db, capsule=capsule, viewer_user_id=recipient_user_id)
    qtok = _tokens(question)
    scored = []
    for s in sources:
        stok = _tokens(s.title + " " + s.body)
        overlap = len(qtok & stok)
        if overlap:
            scored.append((overlap, s))
    scored.sort(key=lambda t: -t[0])

    if not scored:
        answer = CapsuleAnswer(
            question_id=q.id,
            answer_text="Not available in this capsule. The approved context does not contain material matching this question.",
            answer_mode="NOT_AVAILABLE",
            source_refs=[],
            policy_explanation="Answers may only draw on the capsule's approved sources; nothing matched.",
        )
        final_status = "NOT_AVAILABLE"
    else:
        top = [s for _, s in scored[:3]]
        # A single matched, fully-included DECISION is the owner's own written word.
        if len(top) >= 1 and top[0].source_kind == "DECISION" and top[0].representation == "FULL":
            mode = "DIRECT_STATEMENT"
            body_lines = [f"{top[0].title}" + (f" — {top[0].body}" if top[0].body else "")]
        else:
            mode = "APPROVED_CONTEXT_SUMMARY"
            body_lines = [f"[{s.source_kind}] {s.title}" + (f": {s.body[:200]}" if s.body else " (metadata only)") for s in top]
        answer = CapsuleAnswer(
            question_id=q.id,
            answer_text="\n".join(body_lines),
            answer_mode=mode,
            source_refs=[{
                "capsule_source_id": s.capsule_source_id, "source_kind": s.source_kind,
                "source_id": s.source_id, "representation": s.representation,
            } for s in top],
            confidence=min(0.9, 0.4 + 0.15 * scored[0][0]),
            policy_explanation="INFERENCE mode is disabled until the model gateway phase; this answer is extractive from approved sources only.",
        )
        final_status = "ANSWERED"

    await db.refresh(capsule)
    await db.refresh(grant)
    active, state = grant_active(grant, capsule)
    if not active:
        raise PermissionError(state)

    db.add(answer)
    try:
        await db.flush()
    except SQLAlchemyError as exc:
        if _is_capsule_rls_denial(exc):
            await _raise_current_closed_state(db, capsule_id=capsule_id, grant_id=grant_id)
        raise
    await db.execute(text("SELECT fn_set_question_status(:q, :u, :s)"),
                     {"q": str(q.id), "u": str(recipient_user_id), "s": final_status})
    await db.execute(text("SELECT fn_touch_grant(:g, :u)"),
                     {"g": str(grant.id), "u": str(recipient_user_id)})
    await log_access(db, capsule_id=capsule.id, actor_user_id=recipient_user_id,
                     event_kind="ANSWER_SHOWN", grant_id=grant.id,
                     meta={"question_id": str(q.id), "answer_id": str(answer.id), "mode": answer.answer_mode})
    return answer
