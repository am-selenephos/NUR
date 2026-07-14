"""Owner-scoped local product surfaces for Research, Community, Web Signals.

These routes intentionally do not perform live web/community fetches. They
persist local owner notes/questions and emit provenance-bearing timeline events.
"""
import datetime as dt
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.deps import Identity, Scoped, require_csrf
from app.models import (
    AuditEvent,
    CognitiveEvent,
    CommunityConsultationNote,
    Orbit,
    OrbitReference,
    OrbitSource,
    ProviderCapability,
    ResearchBrief,
    ResearchSourceNote,
    WebSignalNote,
    WebSignalQuestion,
)
from app.models._mixins import now_utc

router = APIRouter(tags=["product-surfaces"])


class ResearchBriefIn(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    summary: str | None = None
    orbit_id: uuid.UUID | None = None


class ResearchBriefOut(BaseModel):
    id: uuid.UUID
    owner_user_id: uuid.UUID
    orbit_id: uuid.UUID | None
    question: str
    summary: str | None
    status: str
    provider_status: str
    provenance_label: str
    created_at: dt.datetime
    updated_at: dt.datetime
    model_config = {"from_attributes": True}


class ResearchSourceNoteIn(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    note: str = Field(min_length=1, max_length=8000)
    url: str | None = None
    orbit_id: uuid.UUID | None = None
    research_brief_id: uuid.UUID | None = None
    source_type: str = "OWNER_NOTE"
    trust_state: str = "OWNER_SUPPLIED"


class ResearchSourceNoteOut(BaseModel):
    id: uuid.UUID
    owner_user_id: uuid.UUID
    orbit_id: uuid.UUID | None
    research_brief_id: uuid.UUID | None
    title: str
    note: str
    url: str | None
    source_type: str
    trust_state: str
    provenance_label: str
    created_at: dt.datetime
    updated_at: dt.datetime
    model_config = {"from_attributes": True}


class CommunityNoteIn(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    note: str = Field(min_length=1, max_length=8000)
    collaborator_label: str | None = None
    orbit_id: uuid.UUID | None = None


class CommunityNoteOut(BaseModel):
    id: uuid.UUID
    owner_user_id: uuid.UUID
    orbit_id: uuid.UUID | None
    title: str
    note: str
    collaborator_label: str | None
    capsule_id: uuid.UUID | None
    status: str
    provenance_label: str
    created_at: dt.datetime
    updated_at: dt.datetime
    model_config = {"from_attributes": True}


class WebSignalQuestionIn(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    orbit_id: uuid.UUID | None = None


class WebSignalQuestionOut(BaseModel):
    id: uuid.UUID
    owner_user_id: uuid.UUID
    orbit_id: uuid.UUID | None
    question: str
    status: str
    provider_status: str
    provenance_label: str
    created_at: dt.datetime
    updated_at: dt.datetime
    model_config = {"from_attributes": True}


class WebSignalNoteIn(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    note: str = Field(min_length=1, max_length=8000)
    url: str | None = None
    orbit_id: uuid.UUID | None = None
    web_signal_question_id: uuid.UUID | None = None


class WebSignalNoteOut(BaseModel):
    id: uuid.UUID
    owner_user_id: uuid.UUID
    orbit_id: uuid.UUID | None
    web_signal_question_id: uuid.UUID | None
    title: str
    note: str
    url: str | None
    provenance_label: str
    created_at: dt.datetime
    updated_at: dt.datetime
    model_config = {"from_attributes": True}


class ProviderCapabilityOut(BaseModel):
    id: uuid.UUID
    provider_name: str
    capability_key: str
    status: str
    reason: str
    configured: bool
    created_at: dt.datetime
    updated_at: dt.datetime
    model_config = {"from_attributes": True}


class ConvertOut(BaseModel):
    source_kind: str
    source_id: uuid.UUID
    target_kind: str
    target_id: uuid.UUID
    orbit_id: uuid.UUID
    orbit_source_id: uuid.UUID


async def _owned_orbit(db: Scoped, owner_user_id: uuid.UUID, orbit_id: uuid.UUID | None) -> Orbit | None:
    if orbit_id is None:
        return None
    row = (await db.execute(select(Orbit).where(
        Orbit.id == orbit_id,
        Orbit.owner_user_id == owner_user_id,
    ))).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Orbit not found.")
    return row


async def _default_orbit(db: Scoped, owner_user_id: uuid.UUID, requested: uuid.UUID | None) -> Orbit:
    if requested:
        row = await _owned_orbit(db, owner_user_id, requested)
        assert row is not None
        return row
    row = (await db.execute(select(Orbit).where(
        Orbit.owner_user_id == owner_user_id,
        Orbit.kind != "PERSONAL_BRIDGE",
        Orbit.status == "ACTIVE",
    ).order_by(Orbit.created_at.asc()).limit(1))).scalar_one_or_none()
    if row is None:
        row = (await db.execute(select(Orbit).where(
            Orbit.owner_user_id == owner_user_id,
        ).order_by(Orbit.created_at.asc()).limit(1))).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Orbit not found.")
    return row


def _event(
    *,
    owner_user_id: uuid.UUID,
    orbit_id: uuid.UUID | None,
    kind: str,
    text: str,
    object_type: str,
    object_id: uuid.UUID,
    provenance_label: str = "OWNER_WRITTEN",
) -> tuple[CognitiveEvent, AuditEvent]:
    return (
        CognitiveEvent(
            owner_user_id=owner_user_id,
            orbit_id=orbit_id,
            event_kind=kind,
            content_text=text,
            source_ref=f"{object_type}:{object_id}",
            structured_payload={
                "object_type": object_type,
                "object_id": str(object_id),
                "provenance_label": provenance_label,
            },
        ),
        AuditEvent(
            actor_user_id=owner_user_id,
            event_type=kind,
            object_type=object_type,
            object_id=object_id,
            event_metadata={"provenance_label": provenance_label, "orbit_id": str(orbit_id) if orbit_id else None},
        ),
    )


def _add_event(db: Scoped, ev: CognitiveEvent, audit: AuditEvent) -> None:
    db.add(ev)
    db.add(audit)


@router.post("/research/briefs", response_model=ResearchBriefOut, status_code=201, dependencies=[Depends(require_csrf)])
async def create_research_brief(payload: ResearchBriefIn, db: Scoped, identity: Identity) -> ResearchBriefOut:
    owner_user_id, _ = identity
    await _owned_orbit(db, owner_user_id, payload.orbit_id)
    row = ResearchBrief(owner_user_id=owner_user_id, orbit_id=payload.orbit_id, question=payload.question, summary=payload.summary)
    db.add(row)
    await db.flush()
    _add_event(db, *_event(
        owner_user_id=owner_user_id,
        orbit_id=payload.orbit_id,
        kind="RESEARCH_BRIEF_CREATED",
        text=payload.question,
        object_type="research_brief",
        object_id=row.id,
    ))
    await db.commit()
    return ResearchBriefOut.model_validate(row)


@router.get("/research/briefs", response_model=list[ResearchBriefOut])
async def list_research_briefs(db: Scoped, identity: Identity, limit: int = 50) -> list[ResearchBriefOut]:
    owner_user_id, _ = identity
    rows = (await db.execute(select(ResearchBrief).where(
        ResearchBrief.owner_user_id == owner_user_id,
    ).order_by(ResearchBrief.created_at.desc()).limit(min(limit, 200)))).scalars()
    return [ResearchBriefOut.model_validate(row) for row in rows]


@router.patch("/research/briefs/{brief_id}", response_model=ResearchBriefOut, dependencies=[Depends(require_csrf)])
async def patch_research_brief(brief_id: uuid.UUID, payload: ResearchBriefIn, db: Scoped, identity: Identity) -> ResearchBriefOut:
    owner_user_id, _ = identity
    row = (await db.execute(select(ResearchBrief).where(
        ResearchBrief.id == brief_id,
        ResearchBrief.owner_user_id == owner_user_id,
    ))).scalar_one_or_none()
    if not row:
        raise HTTPException(404, "Research brief not found.")
    await _owned_orbit(db, owner_user_id, payload.orbit_id)
    row.question = payload.question
    row.summary = payload.summary
    row.orbit_id = payload.orbit_id
    row.updated_at = now_utc()
    await db.commit()
    return ResearchBriefOut.model_validate(row)


@router.post("/research/source-notes", response_model=ResearchSourceNoteOut, status_code=201, dependencies=[Depends(require_csrf)])
async def create_research_source_note(payload: ResearchSourceNoteIn, db: Scoped, identity: Identity) -> ResearchSourceNoteOut:
    owner_user_id, _ = identity
    await _owned_orbit(db, owner_user_id, payload.orbit_id)
    if payload.research_brief_id:
        exists = (await db.execute(select(ResearchBrief.id).where(
            ResearchBrief.id == payload.research_brief_id,
            ResearchBrief.owner_user_id == owner_user_id,
        ))).scalar_one_or_none()
        if exists is None:
            raise HTTPException(404, "Research brief not found.")
    row = ResearchSourceNote(owner_user_id=owner_user_id, **payload.model_dump())
    db.add(row)
    await db.flush()
    _add_event(db, *_event(
        owner_user_id=owner_user_id,
        orbit_id=row.orbit_id,
        kind="RESEARCH_SOURCE_NOTE_ADDED",
        text=row.title,
        object_type="research_source_note",
        object_id=row.id,
    ))
    await db.commit()
    return ResearchSourceNoteOut.model_validate(row)


@router.get("/research/source-notes", response_model=list[ResearchSourceNoteOut])
async def list_research_source_notes(db: Scoped, identity: Identity, limit: int = 50) -> list[ResearchSourceNoteOut]:
    owner_user_id, _ = identity
    rows = (await db.execute(select(ResearchSourceNote).where(
        ResearchSourceNote.owner_user_id == owner_user_id,
    ).order_by(ResearchSourceNote.created_at.desc()).limit(min(limit, 200)))).scalars()
    return [ResearchSourceNoteOut.model_validate(row) for row in rows]


@router.post("/research/briefs/{brief_id}/convert", response_model=ConvertOut, dependencies=[Depends(require_csrf)])
async def convert_research_brief(brief_id: uuid.UUID, db: Scoped, identity: Identity) -> ConvertOut:
    owner_user_id, _ = identity
    brief = (await db.execute(select(ResearchBrief).where(
        ResearchBrief.id == brief_id,
        ResearchBrief.owner_user_id == owner_user_id,
    ))).scalar_one_or_none()
    if not brief:
        raise HTTPException(404, "Research brief not found.")
    orbit = await _default_orbit(db, owner_user_id, brief.orbit_id)
    target = OrbitReference(
        owner_user_id=owner_user_id,
        orbit_id=orbit.id,
        kind="OPEN_QUESTION",
        title=brief.question,
        body=brief.summary,
    )
    db.add(target)
    brief.status = "CONVERTED"
    brief.updated_at = now_utc()
    await db.flush()
    source = OrbitSource(owner_user_id=owner_user_id, orbit_id=orbit.id, source_kind="REFERENCE", source_id=target.id)
    db.add(source)
    await db.commit()
    return ConvertOut(source_kind="RESEARCH_BRIEF", source_id=brief.id, target_kind="OPEN_QUESTION", target_id=target.id, orbit_id=orbit.id, orbit_source_id=source.id)


@router.post("/community/consultation-notes", response_model=CommunityNoteOut, status_code=201, dependencies=[Depends(require_csrf)])
async def create_community_note(payload: CommunityNoteIn, db: Scoped, identity: Identity) -> CommunityNoteOut:
    owner_user_id, _ = identity
    await _owned_orbit(db, owner_user_id, payload.orbit_id)
    row = CommunityConsultationNote(owner_user_id=owner_user_id, **payload.model_dump())
    db.add(row)
    await db.flush()
    _add_event(db, *_event(
        owner_user_id=owner_user_id,
        orbit_id=row.orbit_id,
        kind="COMMUNITY_NOTE_CREATED",
        text=row.title,
        object_type="community_consultation_note",
        object_id=row.id,
    ))
    await db.commit()
    return CommunityNoteOut.model_validate(row)


@router.get("/community/consultation-notes", response_model=list[CommunityNoteOut])
async def list_community_notes(db: Scoped, identity: Identity, limit: int = 50) -> list[CommunityNoteOut]:
    owner_user_id, _ = identity
    rows = (await db.execute(select(CommunityConsultationNote).where(
        CommunityConsultationNote.owner_user_id == owner_user_id,
    ).order_by(CommunityConsultationNote.created_at.desc()).limit(min(limit, 200)))).scalars()
    return [CommunityNoteOut.model_validate(row) for row in rows]


@router.post("/web-signals/questions", response_model=WebSignalQuestionOut, status_code=201, dependencies=[Depends(require_csrf)])
async def create_web_signal_question(payload: WebSignalQuestionIn, db: Scoped, identity: Identity) -> WebSignalQuestionOut:
    owner_user_id, _ = identity
    await _owned_orbit(db, owner_user_id, payload.orbit_id)
    row = WebSignalQuestion(owner_user_id=owner_user_id, **payload.model_dump())
    db.add(row)
    await db.flush()
    _add_event(db, *_event(
        owner_user_id=owner_user_id,
        orbit_id=row.orbit_id,
        kind="WEB_SIGNAL_QUESTION_STAGED",
        text=row.question,
        object_type="web_signal_question",
        object_id=row.id,
    ))
    await db.commit()
    return WebSignalQuestionOut.model_validate(row)


@router.get("/web-signals/questions", response_model=list[WebSignalQuestionOut])
async def list_web_signal_questions(db: Scoped, identity: Identity, limit: int = 50) -> list[WebSignalQuestionOut]:
    owner_user_id, _ = identity
    rows = (await db.execute(select(WebSignalQuestion).where(
        WebSignalQuestion.owner_user_id == owner_user_id,
    ).order_by(WebSignalQuestion.created_at.desc()).limit(min(limit, 200)))).scalars()
    return [WebSignalQuestionOut.model_validate(row) for row in rows]


@router.post("/web-signals/notes", response_model=WebSignalNoteOut, status_code=201, dependencies=[Depends(require_csrf)])
async def create_web_signal_note(payload: WebSignalNoteIn, db: Scoped, identity: Identity) -> WebSignalNoteOut:
    owner_user_id, _ = identity
    await _owned_orbit(db, owner_user_id, payload.orbit_id)
    if payload.web_signal_question_id:
        exists = (await db.execute(select(WebSignalQuestion.id).where(
            WebSignalQuestion.id == payload.web_signal_question_id,
            WebSignalQuestion.owner_user_id == owner_user_id,
        ))).scalar_one_or_none()
        if exists is None:
            raise HTTPException(404, "Web signal question not found.")
    row = WebSignalNote(owner_user_id=owner_user_id, **payload.model_dump())
    db.add(row)
    await db.flush()
    _add_event(db, *_event(
        owner_user_id=owner_user_id,
        orbit_id=row.orbit_id,
        kind="WEB_SIGNAL_NOTE_ADDED",
        text=row.title,
        object_type="web_signal_note",
        object_id=row.id,
    ))
    await db.commit()
    return WebSignalNoteOut.model_validate(row)


@router.get("/web-signals/notes", response_model=list[WebSignalNoteOut])
async def list_web_signal_notes(db: Scoped, identity: Identity, limit: int = 50) -> list[WebSignalNoteOut]:
    owner_user_id, _ = identity
    rows = (await db.execute(select(WebSignalNote).where(
        WebSignalNote.owner_user_id == owner_user_id,
    ).order_by(WebSignalNote.created_at.desc()).limit(min(limit, 200)))).scalars()
    return [WebSignalNoteOut.model_validate(row) for row in rows]


@router.post("/web-signals/notes/{note_id}/attach", response_model=ConvertOut, dependencies=[Depends(require_csrf)])
async def attach_web_signal_note(note_id: uuid.UUID, db: Scoped, identity: Identity) -> ConvertOut:
    owner_user_id, _ = identity
    note = (await db.execute(select(WebSignalNote).where(
        WebSignalNote.id == note_id,
        WebSignalNote.owner_user_id == owner_user_id,
    ))).scalar_one_or_none()
    if not note:
        raise HTTPException(404, "Web signal note not found.")
    orbit = await _default_orbit(db, owner_user_id, note.orbit_id)
    target = OrbitReference(owner_user_id=owner_user_id, orbit_id=orbit.id, kind="REFERENCE", title=note.title, body=note.note, url=note.url)
    db.add(target)
    await db.flush()
    source = OrbitSource(owner_user_id=owner_user_id, orbit_id=orbit.id, source_kind="REFERENCE", source_id=target.id)
    db.add(source)
    await db.commit()
    return ConvertOut(source_kind="WEB_SIGNAL_NOTE", source_id=note.id, target_kind="REFERENCE", target_id=target.id, orbit_id=orbit.id, orbit_source_id=source.id)


async def _ensure_capability(
    db: Scoped,
    owner_user_id: uuid.UUID,
    *,
    provider_name: str,
    capability_key: str,
    status: str,
    reason: str,
    configured: bool,
) -> ProviderCapability:
    row = (await db.execute(select(ProviderCapability).where(
        ProviderCapability.owner_user_id == owner_user_id,
        ProviderCapability.provider_name == provider_name,
        ProviderCapability.capability_key == capability_key,
    ))).scalar_one_or_none()
    if row is None:
        row = ProviderCapability(
            owner_user_id=owner_user_id,
            provider_name=provider_name,
            capability_key=capability_key,
            status=status,
            reason=reason,
            configured=configured,
        )
        db.add(row)
        await db.flush()
    else:
        row.status = status
        row.reason = reason
        row.configured = configured
        row.updated_at = now_utc()
    return row


@router.get("/provider-capabilities", response_model=list[ProviderCapabilityOut])
async def provider_capabilities(db: Scoped, identity: Identity) -> list[ProviderCapabilityOut]:
    owner_user_id, _ = identity
    defaults = [
        ("local", "research_notes", "AVAILABLE", "Local research questions and source notes are persisted owner-only.", True),
        ("local", "community_notes", "AVAILABLE", "Local consultation notes are persisted owner-only. No live community is connected.", True),
        ("local", "web_signal_notes", "AVAILABLE", "Web signal questions are staged locally. No live web fetch is performed.", True),
        ("external", "live_web_research", "NOT_CONNECTED", "Live web research is not connected yet.", False),
        ("external", "community_intelligence", "NOT_CONNECTED", "Community intelligence is not connected yet.", False),
    ]
    rows = [
        await _ensure_capability(
            db,
            owner_user_id,
            provider_name=provider,
            capability_key=key,
            status=status,
            reason=reason,
            configured=configured,
        )
        for provider, key, status, reason, configured in defaults
    ]
    await db.commit()
    return [ProviderCapabilityOut.model_validate(row) for row in rows]
