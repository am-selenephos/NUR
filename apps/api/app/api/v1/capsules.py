"""Context Capsules (amendment §3/§4/§6): owner lifecycle + the recipient's
narrow room. Revoked and expired are distinct, immediate, and audited."""
import datetime as dt
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, text as sql_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import Identity, Scoped, require_csrf
from app.models import (
    CapsuleAccessEvent, CapsuleAnswer, CapsuleGrant,
    CollaborationOutcome, ContextCapsule, Orbit, Profile, User,
)
from app.observability.metrics import record_counter
from app.sharing import capsule_service as svc

router = APIRouter(tags=["capsules"])


async def _owned_capsule(db: AsyncSession, user_id: uuid.UUID, capsule_id: uuid.UUID) -> ContextCapsule:
    c = (await db.execute(select(ContextCapsule).where(
        ContextCapsule.id == capsule_id, ContextCapsule.owner_user_id == user_id))).scalar_one_or_none()
    if not c:
        raise HTTPException(404, "Capsule not found.")
    return c


class CapsuleIn(BaseModel):
    title: str
    purpose: str
    capability: str = "READ_ONLY"
    recipient_instructions: str | None = None
    expires_at: dt.datetime | None = None
    orbit_source_ids: list[uuid.UUID]
    representations: dict[str, str] = Field(default_factory=dict)


class CapsuleRow(BaseModel):
    id: uuid.UUID
    orbit_id: uuid.UUID
    title: str
    purpose: str
    capability: str
    expires_at: dt.datetime | None
    revoked_at: dt.datetime | None
    version: int
    created_at: dt.datetime
    model_config = {"from_attributes": True}


@router.post("/orbits/{orbit_id}/capsules", response_model=CapsuleRow, status_code=201, dependencies=[Depends(require_csrf)])
async def create_capsule(orbit_id: uuid.UUID, payload: CapsuleIn, db: Scoped, identity: Identity) -> CapsuleRow:
    user_id, _ = identity
    owned_orbit = (await db.execute(select(Orbit).where(
        Orbit.id == orbit_id, Orbit.owner_user_id == user_id))).scalar_one_or_none()
    if not owned_orbit:
        raise HTTPException(404, "Orbit not found.")
    if not payload.orbit_source_ids:
        raise HTTPException(422, "A capsule must include at least one approved source.")
    try:
        capsule = await svc.create_capsule(
            db, owner_user_id=user_id, orbit_id=orbit_id, title=payload.title, purpose=payload.purpose,
            capability=payload.capability, orbit_source_ids=payload.orbit_source_ids,
            representations=payload.representations, recipient_instructions=payload.recipient_instructions,
            expires_at=payload.expires_at)
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from exc
    await db.commit()
    return CapsuleRow.model_validate(capsule)


@router.get("/capsules", response_model=list[CapsuleRow])
async def list_my_capsules(db: Scoped, identity: Identity) -> list[CapsuleRow]:
    user_id, _ = identity
    rows = (await db.execute(select(ContextCapsule).where(ContextCapsule.owner_user_id == user_id)
                             .order_by(ContextCapsule.created_at.desc()))).scalars()
    return [CapsuleRow.model_validate(c) for c in rows]


class GrantIn(BaseModel):
    recipient_email: str
    capability: str = "ASK_SCOPED_QUESTIONS"
    expires_at: dt.datetime | None = None


class GrantOut(BaseModel):
    id: uuid.UUID
    capsule_id: uuid.UUID
    recipient_user_id: uuid.UUID | None
    capability: str
    expires_at: dt.datetime | None
    revoked_at: dt.datetime | None
    last_accessed_at: dt.datetime | None
    model_config = {"from_attributes": True}


@router.post("/capsules/{capsule_id}/grants", response_model=GrantOut, status_code=201, dependencies=[Depends(require_csrf)])
async def grant_access(capsule_id: uuid.UUID, payload: GrantIn, db: Scoped, identity: Identity) -> GrantOut:
    user_id, _ = identity
    capsule = await _owned_capsule(db, user_id, capsule_id)
    recipient_id = (await db.execute(
        sql_text("SELECT fn_user_id_by_email(:em)"), {"em": payload.recipient_email})).scalar()
    grant = CapsuleGrant(
        capsule_id=capsule.id,
        recipient_user_id=recipient_id,
        recipient_email_hash=svc.email_hash(payload.recipient_email),
        capability=payload.capability, expires_at=payload.expires_at)
    db.add(grant)
    await db.flush()
    await svc.log_access(db, capsule_id=capsule.id, actor_user_id=user_id, event_kind="VIEWED",
                         grant_id=grant.id, meta={"granted": True, "capability": payload.capability})
    await db.commit()
    return GrantOut.model_validate(grant)


@router.post("/capsules/{capsule_id}/revoke", response_model=CapsuleRow, dependencies=[Depends(require_csrf)])
async def revoke(capsule_id: uuid.UUID, request: Request, db: Scoped, identity: Identity) -> CapsuleRow:
    user_id, _ = identity
    capsule = await _owned_capsule(db, user_id, capsule_id)
    await svc.revoke_capsule(db, capsule=capsule, owner_user_id=user_id)
    record_counter(request, "nur_capsule_revoke_total")
    await db.commit()
    return CapsuleRow.model_validate(capsule)


class AuditRow(BaseModel):
    event_kind: str
    actor_user_id: uuid.UUID | None
    grant_id: uuid.UUID | None
    created_at: dt.datetime
    meta: dict
    model_config = {"from_attributes": True}


@router.get("/capsules/{capsule_id}/audit", response_model=list[AuditRow])
async def audit(capsule_id: uuid.UUID, db: Scoped, identity: Identity) -> list[AuditRow]:
    user_id, _ = identity
    await _owned_capsule(db, user_id, capsule_id)
    rows = (await db.execute(select(CapsuleAccessEvent).where(CapsuleAccessEvent.capsule_id == capsule_id)
                             .order_by(CapsuleAccessEvent.created_at.desc()).limit(200))).scalars()
    return [AuditRow.model_validate(r) for r in rows]


class CollabIn(BaseModel):
    onboarding_faster: bool | None = None
    decisions_respected: bool | None = None
    answered_correctly: bool | None = None
    time_saved_minutes: int | None = None
    notes: str | None = None


@router.post("/capsules/{capsule_id}/collaboration-outcome", status_code=201, dependencies=[Depends(require_csrf)])
async def collaboration_outcome(capsule_id: uuid.UUID, payload: CollabIn, db: Scoped, identity: Identity) -> dict:
    user_id, _ = identity
    await _owned_capsule(db, user_id, capsule_id)
    row = CollaborationOutcome(capsule_id=capsule_id, owner_user_id=user_id, **payload.model_dump())
    db.add(row)
    await db.commit()
    return {"id": str(row.id)}


# ------------------------------ recipient room ---------------------------
class IncludedSource(BaseModel):
    source_id: str
    source_kind: str
    representation: str
    title: str
    body: str


class RecipientView(BaseModel):
    capsule_id: uuid.UUID
    state: str  # ACTIVE | REVOKED | EXPIRED
    title: str
    purpose: str
    owner_display: str
    capability: str
    expires_at: dt.datetime | None
    recipient_instructions: str | None
    safety_copy: str
    included: list[IncludedSource]
    excluded_summary: list[dict]
    grant_id: uuid.UUID | None


async def _recipient_grant(db: AsyncSession, user_id: uuid.UUID, capsule_id: uuid.UUID) -> tuple[ContextCapsule | None, CapsuleGrant | None]:
    # invited-by-email before registering? claim the hash-addressed grant now
    my_email = (await db.execute(select(User.email).where(User.id == user_id))).scalar_one_or_none()
    if my_email:
        await db.execute(sql_text("SELECT fn_claim_grants(:uid, :h)"),
                         {"uid": str(user_id), "h": svc.email_hash(my_email)})
    grant = (await db.execute(select(CapsuleGrant).where(
        CapsuleGrant.capsule_id == capsule_id, CapsuleGrant.recipient_user_id == user_id))).scalars().first()
    capsule = (await db.execute(select(ContextCapsule).where(ContextCapsule.id == capsule_id))).scalar_one_or_none()
    return capsule, grant


@router.get("/capsules/{capsule_id}/view", response_model=RecipientView)
async def recipient_view(capsule_id: uuid.UUID, request: Request, db: Scoped, identity: Identity) -> RecipientView:
    user_id, _ = identity
    capsule, grant = await _recipient_grant(db, user_id, capsule_id)
    if capsule is None or grant is None:
        # Owners preview through owner endpoints; strangers see nothing.
        raise HTTPException(404, "No capsule is shared with you at this address.")
    owner_profile = (await db.execute(
        select(Profile).where(Profile.user_id == capsule.owner_user_id))).scalar_one_or_none()
    owner_name = owner_profile.chosen_name if owner_profile else "the owner"
    active, state = svc.grant_active(grant, capsule)
    safety = f"This does not speak for {owner_name}. It answers only from approved context."
    if not active:
        record_counter(request, "nur_capsule_view_total", (("state", state),))
        await svc.log_access(db, capsule_id=capsule.id, actor_user_id=user_id,
                             event_kind="EXPIRED" if state == "EXPIRED" else "VIEWED",
                             grant_id=grant.id, meta={"state": state})
        await db.commit()
        return RecipientView(capsule_id=capsule.id, state=state, title=capsule.title, purpose=capsule.purpose,
                             owner_display=owner_name, capability=grant.capability, expires_at=capsule.expires_at,
                             recipient_instructions=None, safety_copy=safety, included=[], excluded_summary=[],
                             grant_id=None)
    sources = await svc.hydrate_capsule_sources(db, capsule=capsule, viewer_user_id=user_id)
    record_counter(request, "nur_capsule_view_total", (("state", "ACTIVE"),))
    excluded_rows = (await db.execute(
        sql_text("SELECT * FROM fn_excluded_summary(:cap, :usr)"),
        {"cap": str(capsule.id), "usr": str(user_id)})).all()
    excluded = {r.source_kind: r.cnt for r in excluded_rows}
    await db.execute(sql_text("SELECT fn_touch_grant(:g, :u)"), {"g": str(grant.id), "u": str(user_id)})
    await svc.log_access(db, capsule_id=capsule.id, actor_user_id=user_id, event_kind="VIEWED", grant_id=grant.id)
    await db.commit()
    return RecipientView(
        capsule_id=capsule.id, state="ACTIVE", title=capsule.title, purpose=capsule.purpose,
        owner_display=owner_name, capability=grant.capability, expires_at=capsule.expires_at,
        recipient_instructions=capsule.recipient_instructions, safety_copy=safety,
        included=[IncludedSource(source_id=s.source_id, source_kind=s.source_kind,
                                 representation=s.representation, title=s.title, body=s.body)
                  for s in sources],
        excluded_summary=[{"source_kind": k, "count": v, "note": "withheld by the owner"} for k, v in excluded.items()],
        grant_id=grant.id,
    )


class QuestionIn(BaseModel):
    question: str


class AnswerOut(BaseModel):
    question: str
    answer_text: str
    answer_mode: str
    source_refs: list
    confidence: float | None
    policy_explanation: str | None
    created_at: dt.datetime


@router.post("/capsules/{capsule_id}/questions", response_model=AnswerOut, status_code=201, dependencies=[Depends(require_csrf)])
async def ask(capsule_id: uuid.UUID, payload: QuestionIn, request: Request, db: Scoped, identity: Identity) -> AnswerOut:
    user_id, _ = identity
    capsule, grant = await _recipient_grant(db, user_id, capsule_id)
    if capsule is None or grant is None:
        raise HTTPException(404, "No capsule is shared with you at this address.")
    try:
        answer: CapsuleAnswer = await svc.answer_from_capsule(
            db, capsule_id=capsule_id, grant_id=grant.id, question=payload.question, recipient_user_id=user_id)
    except PermissionError as exc:
        code = str(exc)
        await db.commit()
        if code in ("REVOKED", "EXPIRED"):
            record_counter(request, "nur_capsule_ask_total", (("state", code),))
            raise HTTPException(410, f"This capsule is {code.lower()}.") from exc
        if code == "CAPABILITY":
            raise HTTPException(403, "This grant is read-only; questions are not enabled.") from exc
        raise HTTPException(404, "No capsule is shared with you at this address.") from exc
    await db.commit()
    record_counter(request, "nur_capsule_ask_total", (("state", "ANSWERED"), ("mode", answer.answer_mode)))
    return AnswerOut(question=payload.question, answer_text=answer.answer_text, answer_mode=answer.answer_mode,
                     source_refs=answer.source_refs, confidence=float(answer.confidence) if answer.confidence is not None else None,
                     policy_explanation=answer.policy_explanation, created_at=answer.created_at)
