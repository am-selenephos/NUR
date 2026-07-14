"""Bounded ORIENT -> GATHER -> MAP -> MOVE -> RETURN Consultations."""

import datetime as dt
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.deps import Identity, Scoped, require_csrf
from app.models import (
    AuditEvent, CognitiveEvent, CommunityMembership, CommunityRoom,
    Consultation, ConsultationContribution, ConsultationStageRecord,
    Orbit, TimelineEvent,
)
from app.services.glow_service import award_glow

router = APIRouter(prefix="/consultations", tags=["consultations"])
STAGES = ("ORIENT", "GATHER", "MAP", "MOVE", "RETURN")
CONTRIBUTION_TYPES = {
    "LIVED_EXPERIENCE", "PRACTICAL_MOVE", "CONSTRAINT", "COUNTEREXAMPLE",
    "DISAGREEMENT", "WITNESS", "TRIED_THIS", "OUTCOME", "EXPERT_VOICE",
    "RESEARCH_EVIDENCE", "NUR_SYNTHESIS",
}


class ConsultationIn(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    question: str = Field(min_length=1, max_length=4000)
    purpose: str = Field(min_length=1, max_length=4000)
    desired_outcome: str = Field(min_length=1, max_length=4000)
    scope_statement: str = Field(min_length=1, max_length=4000)
    room_id: uuid.UUID | None = None
    orbit_id: uuid.UUID | None = None
    system_slug: str | None = Field(default=None, max_length=48)
    is_demo: bool = False


class ContributionIn(BaseModel):
    contribution_type: str
    body: str = Field(min_length=1, max_length=12000)
    evidence: list[dict | str] = Field(default_factory=list, max_length=50)
    language_tag: str = Field(default="en", min_length=2, max_length=20)
    is_demo: bool = False


class StageIn(BaseModel):
    payload: dict = Field(default_factory=dict)


class ConsultationOut(BaseModel):
    id: uuid.UUID
    owner_user_id: uuid.UUID
    room_id: uuid.UUID | None
    orbit_id: uuid.UUID | None
    system_slug: str | None
    title: str
    question: str
    purpose: str
    desired_outcome: str
    scope_statement: str
    current_stage: str
    status: str
    is_demo: bool
    current_user_role: str
    privacy: str = "BOUNDED_CONSULTATION_ONLY"
    created_at: dt.datetime
    updated_at: dt.datetime


class ContributionOut(BaseModel):
    id: uuid.UUID
    consultation_id: uuid.UUID
    owner_user_id: uuid.UUID
    contribution_type: str
    body: str
    evidence: list
    language_tag: str
    provenance_label: str
    is_demo: bool
    created_at: dt.datetime
    model_config = {"from_attributes": True}


class StageOut(BaseModel):
    id: uuid.UUID
    consultation_id: uuid.UUID
    owner_user_id: uuid.UUID
    stage: str
    stage_payload: dict
    provenance_label: str
    created_at: dt.datetime
    glow: dict | None = None
    model_config = {"from_attributes": True}


class ConsultationDetail(BaseModel):
    consultation: ConsultationOut
    completed_stages: list[StageOut]
    contributions: list[ContributionOut]
    stage_order: list[str]
    next_stage: str | None
    what_nur_may_be_wrong_about: str


async def _membership(db: Scoped, room_id: uuid.UUID, user_id: uuid.UUID) -> CommunityMembership | None:
    return (await db.execute(select(CommunityMembership).where(
        CommunityMembership.room_id == room_id,
        CommunityMembership.user_id == user_id,
    ))).scalar_one_or_none()


async def _consultation(db: Scoped, consultation_id: uuid.UUID) -> Consultation:
    row = (await db.execute(select(Consultation).where(Consultation.id == consultation_id))).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Consultation not found inside this boundary.")
    return row


async def _role(db: Scoped, row: Consultation, user_id: uuid.UUID) -> str:
    if row.owner_user_id == user_id:
        return "OWNER"
    if row.room_id:
        member = await _membership(db, row.room_id, user_id)
        if member:
            return member.role
    raise HTTPException(404, "Consultation not found inside this boundary.")


def _out(row: Consultation, role: str) -> ConsultationOut:
    return ConsultationOut(
        id=row.id, owner_user_id=row.owner_user_id, room_id=row.room_id,
        orbit_id=row.orbit_id, system_slug=row.system_slug, title=row.title,
        question=row.question, purpose=row.purpose, desired_outcome=row.desired_outcome,
        scope_statement=row.scope_statement, current_stage=row.current_stage,
        status=row.status, is_demo=row.is_demo, current_user_role=role,
        created_at=row.created_at, updated_at=row.updated_at,
    )


def _record(
    db: Scoped, *, actor_user_id: uuid.UUID, consultation: Consultation,
    event_type: str, title: str, object_type: str, object_id: uuid.UUID,
    extra: dict | None = None,
) -> None:
    actor_orbit = consultation.orbit_id if consultation.owner_user_id == actor_user_id else None
    payload = {
        "consultation_id": str(consultation.id),
        "room_id": str(consultation.room_id) if consultation.room_id else None,
        "object_type": object_type,
        "object_id": str(object_id),
        "privacy_boundary": "BOUNDED_CONSULTATION_ONLY",
        "provenance_label": "OWNER_WRITTEN" if consultation.owner_user_id == actor_user_id else "MEMBER_WRITTEN",
        **(extra or {}),
    }
    db.add(CognitiveEvent(
        owner_user_id=actor_user_id, orbit_id=actor_orbit,
        event_kind="COMMUNITY_NOTE_CREATED", content_text=title,
        source_ref=f"{object_type}:{object_id}", structured_payload=payload,
    ))
    db.add(TimelineEvent(
        owner_user_id=actor_user_id, event_type=event_type, title=title,
        time_kind="PAST", occurred_at=dt.datetime.now(dt.UTC),
        source_type=object_type.upper(), source_id=object_id,
        group_id=actor_orbit, orbit_id=actor_orbit, status="COMPLETED",
        event_payload=payload,
    ))
    db.add(AuditEvent(
        actor_user_id=actor_user_id, event_type=event_type,
        object_type=object_type, object_id=object_id, event_metadata=payload,
    ))


@router.post("", response_model=ConsultationOut, status_code=201, dependencies=[Depends(require_csrf)])
async def create_consultation(payload: ConsultationIn, db: Scoped, identity: Identity) -> ConsultationOut:
    user_id, _ = identity
    room: CommunityRoom | None = None
    if payload.room_id:
        room = (await db.execute(select(CommunityRoom).where(
            CommunityRoom.id == payload.room_id,
            CommunityRoom.status == "ACTIVE",
        ))).scalar_one_or_none()
        if room is None or await _membership(db, room.id, user_id) is None:
            raise HTTPException(404, "Active room membership is required.")
    if payload.orbit_id:
        orbit = (await db.execute(select(Orbit).where(
            Orbit.id == payload.orbit_id, Orbit.owner_user_id == user_id,
        ))).scalar_one_or_none()
        if orbit is None:
            raise HTTPException(404, "Owned Orbit not found.")
    row = Consultation(
        owner_user_id=user_id, room_id=room.id if room else None,
        room_owner_user_id=room.owner_user_id if room else None,
        orbit_id=payload.orbit_id, system_slug=payload.system_slug,
        title=payload.title, question=payload.question, purpose=payload.purpose,
        desired_outcome=payload.desired_outcome, scope_statement=payload.scope_statement,
        is_demo=payload.is_demo,
    )
    db.add(row)
    await db.flush()
    _record(db, actor_user_id=user_id, consultation=row, event_type="CONSULTATION_CREATED",
            title=f"Consultation opened: {row.title}", object_type="consultation", object_id=row.id)
    await db.commit()
    return _out(row, "OWNER")


@router.get("", response_model=list[ConsultationOut])
async def list_consultations(db: Scoped, identity: Identity) -> list[ConsultationOut]:
    user_id, _ = identity
    rows = (await db.execute(select(Consultation).order_by(Consultation.updated_at.desc()).limit(100))).scalars().all()
    return [_out(row, await _role(db, row, user_id)) for row in rows]


@router.get("/{consultation_id}", response_model=ConsultationDetail)
async def consultation_detail(consultation_id: uuid.UUID, db: Scoped, identity: Identity) -> ConsultationDetail:
    user_id, _ = identity
    row = await _consultation(db, consultation_id)
    role = await _role(db, row, user_id)
    stages = (await db.execute(select(ConsultationStageRecord).where(
        ConsultationStageRecord.consultation_id == consultation_id,
    ).order_by(ConsultationStageRecord.created_at))).scalars().all()
    contributions = (await db.execute(select(ConsultationContribution).where(
        ConsultationContribution.consultation_id == consultation_id,
    ).order_by(ConsultationContribution.created_at))).scalars().all()
    return ConsultationDetail(
        consultation=_out(row, role),
        completed_stages=[StageOut.model_validate(stage) for stage in stages],
        contributions=[ContributionOut.model_validate(item) for item in contributions],
        stage_order=list(STAGES), next_stage=row.current_stage if row.status == "ACTIVE" else None,
        what_nur_may_be_wrong_about="This synthesis is incomplete until the owner records RETURN evidence.",
    )


@router.post("/{consultation_id}/contributions", response_model=ContributionOut, status_code=201, dependencies=[Depends(require_csrf)])
async def add_contribution(consultation_id: uuid.UUID, payload: ContributionIn, db: Scoped, identity: Identity) -> ContributionOut:
    user_id, _ = identity
    row = await _consultation(db, consultation_id)
    await _role(db, row, user_id)
    if row.status != "ACTIVE":
        raise HTTPException(409, "This Consultation no longer accepts contributions.")
    contribution_type = payload.contribution_type.upper()
    if contribution_type not in CONTRIBUTION_TYPES:
        raise HTTPException(422, "Unsupported Consultation contribution type.")
    contribution = ConsultationContribution(
        consultation_id=row.id, consultation_owner_user_id=row.owner_user_id,
        owner_user_id=user_id, contribution_type=contribution_type,
        body=payload.body, evidence=payload.evidence, language_tag=payload.language_tag,
        is_demo=payload.is_demo,
    )
    db.add(contribution)
    await db.flush()
    _record(db, actor_user_id=user_id, consultation=row,
            event_type="CONSULTATION_CONTRIBUTION_ADDED",
            title=f"{contribution_type.replace('_', ' ').title()} added to {row.title}",
            object_type="consultation_contribution", object_id=contribution.id,
            extra={"contribution_type": contribution_type})
    await db.commit()
    return ContributionOut.model_validate(contribution)


@router.post("/{consultation_id}/stages/{stage}", response_model=StageOut, status_code=201, dependencies=[Depends(require_csrf)])
async def complete_stage(consultation_id: uuid.UUID, stage: str, payload: StageIn, db: Scoped, identity: Identity) -> StageOut:
    user_id, _ = identity
    row = await _consultation(db, consultation_id)
    if row.owner_user_id != user_id:
        raise HTTPException(403, "Only the Consultation owner can advance the stage.")
    stage = stage.upper()
    if stage not in STAGES:
        raise HTTPException(422, "Unknown Consultation stage.")
    if row.status != "ACTIVE" or row.current_stage != stage:
        raise HTTPException(409, f"Expected stage {row.current_stage}.")
    if not payload.payload:
        raise HTTPException(422, "A stage needs a persisted record.")
    record = ConsultationStageRecord(
        consultation_id=row.id, consultation_owner_user_id=row.owner_user_id,
        owner_user_id=user_id, stage=stage, stage_payload=payload.payload,
    )
    db.add(record)
    await db.flush()
    if stage == "RETURN":
        row.status = "COMPLETED"
    else:
        row.current_stage = STAGES[STAGES.index(stage) + 1]
    row.updated_at = dt.datetime.now(dt.UTC)
    _record(db, actor_user_id=user_id, consultation=row,
            event_type=f"CONSULTATION_{stage}_COMPLETED",
            title=f"{stage.title()} completed: {row.title}", object_type="consultation_stage",
            object_id=record.id, extra={"stage": stage})
    glow: dict | None = None
    if stage == "RETURN":
        if row.is_demo:
            glow = {"status": "GLOW_GATED", "awarded_points": 0, "note": "DEMO Consultations never earn Glow."}
        else:
            try:
                awarded = await award_glow(
                    db, owner_user_id=user_id, event_type="consultation_return",
                    source_kind="CONSULTATION", source_id=row.id, orbit_id=row.orbit_id,
                    idempotency_key=f"consultation_return:{row.id}",
                )
                glow = {"status": "AWARDED", "awarded_points": awarded.transaction.final_points,
                        "transaction_id": str(awarded.transaction.id),
                        "idempotent_replay": awarded.idempotent_replay}
            except HTTPException as exc:
                if exc.status_code not in {409, 422}:
                    raise
                glow = {"status": "GLOW_GATED", "awarded_points": 0, "note": str(exc.detail)}
    await db.commit()
    return StageOut(
        id=record.id, consultation_id=record.consultation_id,
        owner_user_id=record.owner_user_id, stage=record.stage,
        stage_payload=record.stage_payload, provenance_label=record.provenance_label,
        created_at=record.created_at, glow=glow,
    )
