"""Scoped Group NUR, evidence research, Web Signal, Expert, and Tender APIs."""

import datetime as dt
import hashlib
import uuid
from urllib.parse import urlsplit, urlunsplit

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select

from app.api.deps import Identity, Scoped, require_csrf
from app.models import (
    AuditEvent,
    CognitiveEvent,
    CommunityMembership,
    CommunityMessage,
    CommunityPost,
    CommunityRoom,
    Consultation,
    ConsultationContribution,
    ExpertContribution,
    ExpertProfile,
    ExpertVerification,
    GroupNURSynthesis,
    ResearchBrief,
    ResearchCitation,
    ResearchClaim,
    ResearchClaimRevision,
    ResearchJob,
    ResearchSource,
    TenderInsight,
    TimelineEvent,
    WebSignalAlert,
    WebSignalQuestion,
    WebSignalSnapshot,
    WebWatchlist,
)

router = APIRouter(tags=["group intelligence and research"])


def _now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def _bounded_url(value: str) -> str:
    raw = value.strip()
    parsed = urlsplit(raw)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise HTTPException(422, "A source URL must use http or https and include a host.")
    if parsed.username or parsed.password:
        raise HTTPException(422, "Source URLs cannot contain credentials.")
    host = parsed.hostname.lower().rstrip(".")
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".localhost"):
        raise HTTPException(422, "Local network source URLs are not accepted.")
    if host in {"0.0.0.0", "127.0.0.1", "::1"}:
        raise HTTPException(422, "Loopback source URLs are not accepted.")
    netloc = host
    if parsed.port:
        netloc = f"{host}:{parsed.port}"
    return urlunsplit((parsed.scheme.lower(), netloc, parsed.path or "/", parsed.query, ""))


def _event(
    db: Scoped,
    *,
    actor_user_id: uuid.UUID,
    event_type: str,
    title: str,
    object_type: str,
    object_id: uuid.UUID,
    orbit_id: uuid.UUID | None = None,
    metadata: dict | None = None,
) -> None:
    payload = {
        "object_type": object_type,
        "object_id": str(object_id),
        "domain_event_type": event_type,
        "provenance_label": "OWNER_ACTION",
        **(metadata or {}),
    }
    db.add(CognitiveEvent(
        owner_user_id=actor_user_id,
        orbit_id=orbit_id,
        event_kind="SYSTEM_EVENT",
        content_text=title,
        source_ref=f"{object_type}:{object_id}",
        structured_payload=payload,
    ))
    db.add(TimelineEvent(
        owner_user_id=actor_user_id,
        event_type=event_type,
        title=title,
        time_kind="PAST",
        occurred_at=_now(),
        source_type=object_type.upper(),
        source_id=object_id,
        group_id=orbit_id,
        orbit_id=orbit_id,
        status="COMPLETED",
        event_payload=payload,
    ))
    db.add(AuditEvent(
        actor_user_id=actor_user_id,
        event_type=event_type,
        object_type=object_type,
        object_id=object_id,
        event_metadata=payload,
    ))


async def _room_role(
    db: Scoped,
    room_id: uuid.UUID,
    user_id: uuid.UUID,
) -> tuple[CommunityRoom, str]:
    row = (await db.execute(
        select(CommunityRoom, CommunityMembership.role)
        .join(CommunityMembership, CommunityMembership.room_id == CommunityRoom.id)
        .where(
            CommunityRoom.id == room_id,
            CommunityRoom.status == "ACTIVE",
            CommunityMembership.user_id == user_id,
        )
    )).one_or_none()
    if row is None:
        raise HTTPException(404, "Active room membership is required.")
    return row[0], row[1]


async def _owned_brief(
    db: Scoped,
    brief_id: uuid.UUID,
    owner_user_id: uuid.UUID,
) -> ResearchBrief:
    row = (await db.execute(select(ResearchBrief).where(
        ResearchBrief.id == brief_id,
        ResearchBrief.owner_user_id == owner_user_id,
    ))).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Research brief not found.")
    return row


async def _owned_sources(
    db: Scoped,
    source_ids: list[uuid.UUID],
    owner_user_id: uuid.UUID,
    *,
    brief_id: uuid.UUID | None = None,
) -> list[ResearchSource]:
    unique_ids = set(source_ids)
    if not unique_ids:
        return []
    statement = select(ResearchSource).where(
        ResearchSource.id.in_(unique_ids),
        ResearchSource.owner_user_id == owner_user_id,
    )
    if brief_id:
        statement = statement.where(ResearchSource.research_brief_id == brief_id)
    rows = (await db.execute(statement)).scalars().all()
    if len(rows) != len(unique_ids):
        raise HTTPException(422, "Every cited source must belong to this owner and research brief.")
    return list(rows)


class GroupSynthesisIn(BaseModel):
    consultation_id: uuid.UUID | None = None
    supersedes_id: uuid.UUID | None = None
    trigger_kind: str = "ON_DEMAND"
    summary: str = Field(min_length=1, max_length=30000)
    current_question: str = Field(min_length=1, max_length=4000)
    decisions: list[dict | str] = Field(default_factory=list, max_length=100)
    tensions: list[dict | str] = Field(default_factory=list, max_length=100)
    minority_positions: list[dict | str] = Field(default_factory=list, max_length=100)
    evidence: list[dict | str] = Field(default_factory=list, max_length=200)
    counterevidence: list[dict | str] = Field(default_factory=list, max_length=200)
    unresolved_questions: list[dict | str] = Field(default_factory=list, max_length=100)
    tasks: list[dict | str] = Field(default_factory=list, max_length=100)
    source_message_ids: list[uuid.UUID] = Field(default_factory=list, max_length=500)
    source_post_ids: list[uuid.UUID] = Field(default_factory=list, max_length=500)
    source_contribution_ids: list[uuid.UUID] = Field(default_factory=list, max_length=500)
    what_may_be_wrong: str = Field(min_length=1, max_length=12000)
    correction_reason: str | None = Field(default=None, min_length=1, max_length=4000)
    language_tag: str = Field(default="en", min_length=2, max_length=20)


class GroupSynthesisOut(BaseModel):
    id: uuid.UUID
    room_id: uuid.UUID
    room_owner_user_id: uuid.UUID
    owner_user_id: uuid.UUID
    consultation_id: uuid.UUID | None
    supersedes_id: uuid.UUID | None
    version: int
    trigger_kind: str
    status: str
    summary: str
    current_question: str
    decisions: list
    tensions: list
    minority_positions: list
    evidence: list
    counterevidence: list
    unresolved_questions: list
    tasks: list
    source_message_ids: list
    source_post_ids: list
    source_contribution_ids: list
    what_may_be_wrong: str
    correction_reason: str | None
    language_tag: str
    provenance_label: str
    created_at: dt.datetime
    model_config = {"from_attributes": True}


async def _validate_group_sources(
    db: Scoped,
    room_id: uuid.UUID,
    payload: GroupSynthesisIn,
) -> None:
    checks = (
        (CommunityMessage, payload.source_message_ids),
        (CommunityPost, payload.source_post_ids),
    )
    for model, ids in checks:
        unique_ids = set(ids)
        if not unique_ids:
            continue
        count = int((await db.execute(select(func.count(model.id)).where(
            model.id.in_(unique_ids), model.room_id == room_id,
        ))).scalar_one())
        if count != len(unique_ids):
            raise HTTPException(422, "Every Group NUR source must belong to this room.")
    contribution_ids = set(payload.source_contribution_ids)
    if contribution_ids:
        count = int((await db.execute(
            select(func.count(ConsultationContribution.id))
            .join(Consultation, Consultation.id == ConsultationContribution.consultation_id)
            .where(
                ConsultationContribution.id.in_(contribution_ids),
                Consultation.room_id == room_id,
            )
        )).scalar_one())
        if count != len(contribution_ids):
            raise HTTPException(422, "Every Consultation source must belong to this room.")


@router.post(
    "/group-nur/rooms/{room_id}/syntheses",
    response_model=GroupSynthesisOut,
    status_code=201,
    dependencies=[Depends(require_csrf)],
)
async def create_group_synthesis(
    room_id: uuid.UUID,
    payload: GroupSynthesisIn,
    db: Scoped,
    identity: Identity,
) -> GroupSynthesisOut:
    user_id, _ = identity
    room, role = await _room_role(db, room_id, user_id)
    if role not in {"OWNER", "MODERATOR"}:
        raise HTTPException(403, "Only a room owner or moderator can publish Group NUR synthesis.")
    trigger_kind = payload.trigger_kind.upper().strip()
    if trigger_kind not in {"ON_DEMAND", "SCHEDULED", "TRANSITION", "CORRECTION"}:
        raise HTTPException(422, "Unsupported Group NUR trigger.")
    if payload.supersedes_id is None and payload.correction_reason is not None:
        raise HTTPException(422, "A correction reason requires the synthesis it supersedes.")
    if payload.supersedes_id is not None:
        prior = (await db.execute(select(GroupNURSynthesis).where(
            GroupNURSynthesis.id == payload.supersedes_id,
            GroupNURSynthesis.room_id == room_id,
        ))).scalar_one_or_none()
        if prior is None or not payload.correction_reason:
            raise HTTPException(422, "A correction needs a visible prior version and reason.")
        trigger_kind = "CORRECTION"
    if payload.consultation_id:
        consultation = (await db.execute(select(Consultation).where(
            Consultation.id == payload.consultation_id,
            Consultation.room_id == room_id,
        ))).scalar_one_or_none()
        if consultation is None:
            raise HTTPException(422, "The linked Consultation must belong to this room.")
    await _validate_group_sources(db, room_id, payload)
    await db.execute(select(CommunityRoom).where(CommunityRoom.id == room_id).with_for_update())
    version = int((await db.execute(select(func.coalesce(func.max(GroupNURSynthesis.version), 0)).where(
        GroupNURSynthesis.room_id == room_id,
    ))).scalar_one()) + 1
    row = GroupNURSynthesis(
        room_id=room.id,
        room_owner_user_id=room.owner_user_id,
        owner_user_id=user_id,
        consultation_id=payload.consultation_id,
        supersedes_id=payload.supersedes_id,
        version=version,
        trigger_kind=trigger_kind,
        summary=payload.summary,
        current_question=payload.current_question,
        decisions=payload.decisions,
        tensions=payload.tensions,
        minority_positions=payload.minority_positions,
        evidence=payload.evidence,
        counterevidence=payload.counterevidence,
        unresolved_questions=payload.unresolved_questions,
        tasks=payload.tasks,
        source_message_ids=[str(value) for value in payload.source_message_ids],
        source_post_ids=[str(value) for value in payload.source_post_ids],
        source_contribution_ids=[str(value) for value in payload.source_contribution_ids],
        what_may_be_wrong=payload.what_may_be_wrong,
        correction_reason=payload.correction_reason,
        language_tag=payload.language_tag,
        provenance_label="OWNER_SYNTHESIZED" if role == "OWNER" else "MODERATOR_SYNTHESIZED",
    )
    db.add(row)
    await db.flush()
    _event(
        db,
        actor_user_id=user_id,
        event_type="GROUP_NUR_SYNTHESIS_PUBLISHED",
        title=f"Group NUR v{version}: {room.title}",
        object_type="group_nur_synthesis",
        object_id=row.id,
        orbit_id=room.orbit_id if room.owner_user_id == user_id else None,
        metadata={"room_id": str(room.id), "version": version, "scope": "ROOM_ONLY"},
    )
    await db.commit()
    return GroupSynthesisOut.model_validate(row)


@router.get(
    "/group-nur/rooms/{room_id}/syntheses",
    response_model=list[GroupSynthesisOut],
)
async def list_group_syntheses(
    room_id: uuid.UUID,
    db: Scoped,
    identity: Identity,
) -> list[GroupSynthesisOut]:
    user_id, _ = identity
    await _room_role(db, room_id, user_id)
    rows = (await db.execute(select(GroupNURSynthesis).where(
        GroupNURSynthesis.room_id == room_id,
    ).order_by(GroupNURSynthesis.version.desc()).limit(100))).scalars().all()
    return [GroupSynthesisOut.model_validate(row) for row in rows]


class ResearchJobIn(BaseModel):
    research_brief_id: uuid.UUID
    mode: str = "QUICK"
    provider_name: str = "OWNER_SOURCES"
    query_preview: str = Field(min_length=1, max_length=4000)
    external_scope_approved: bool = False


class ResearchJobOut(BaseModel):
    id: uuid.UUID
    owner_user_id: uuid.UUID
    research_brief_id: uuid.UUID
    mode: str
    provider_name: str
    status: str
    query_preview: str
    external_scope_approved: bool
    failure_code: str | None
    failure_detail: str | None
    started_at: dt.datetime | None
    completed_at: dt.datetime | None
    created_at: dt.datetime
    updated_at: dt.datetime
    model_config = {"from_attributes": True}


@router.post(
    "/research/jobs",
    response_model=ResearchJobOut,
    status_code=201,
    dependencies=[Depends(require_csrf)],
)
async def create_research_job(
    payload: ResearchJobIn,
    db: Scoped,
    identity: Identity,
) -> ResearchJobOut:
    owner_user_id, _ = identity
    brief = await _owned_brief(db, payload.research_brief_id, owner_user_id)
    mode = payload.mode.upper().strip()
    provider = payload.provider_name.upper().strip()
    if mode not in {"QUICK", "DEEP"}:
        raise HTTPException(422, "Research mode must be QUICK or DEEP.")
    if provider not in {"OWNER_SOURCES", "EXTERNAL_WEB"}:
        raise HTTPException(422, "Research provider must be OWNER_SOURCES or EXTERNAL_WEB.")
    now = _now()
    if provider == "EXTERNAL_WEB":
        status = "NOT_CONNECTED"
        failure_code = "EXTERNAL_WEB_CONNECTOR_DISABLED"
        failure_detail = (
            "No lawful external retrieval connector is enabled. No browsing or source claim was made."
        )
        completed_at = now
        started_at = None
        brief.provider_status = "NOT_CONNECTED"
        brief.status = "AWAITING_PROVIDER"
    else:
        status = "RUNNING"
        failure_code = None
        failure_detail = None
        completed_at = None
        started_at = now
        brief.provider_status = "OWNER_SOURCES"
        brief.status = "IN_RESEARCH"
    brief.updated_at = now
    row = ResearchJob(
        owner_user_id=owner_user_id,
        research_brief_id=brief.id,
        mode=mode,
        provider_name=provider,
        status=status,
        query_preview=payload.query_preview,
        external_scope_approved=payload.external_scope_approved,
        failure_code=failure_code,
        failure_detail=failure_detail,
        started_at=started_at,
        completed_at=completed_at,
    )
    db.add(row)
    await db.flush()
    _event(
        db,
        actor_user_id=owner_user_id,
        event_type="RESEARCH_JOB_STAGED",
        title=f"Research job: {brief.question}",
        object_type="research_job",
        object_id=row.id,
        orbit_id=brief.orbit_id,
        metadata={"provider": provider, "status": status},
    )
    await db.commit()
    return ResearchJobOut.model_validate(row)


@router.get("/research/jobs", response_model=list[ResearchJobOut])
async def list_research_jobs(db: Scoped, identity: Identity) -> list[ResearchJobOut]:
    owner_user_id, _ = identity
    rows = (await db.execute(select(ResearchJob).where(
        ResearchJob.owner_user_id == owner_user_id,
    ).order_by(ResearchJob.created_at.desc()).limit(100))).scalars().all()
    return [ResearchJobOut.model_validate(row) for row in rows]


@router.post(
    "/research/jobs/{job_id}/cancel",
    response_model=ResearchJobOut,
    dependencies=[Depends(require_csrf)],
)
async def cancel_research_job(
    job_id: uuid.UUID,
    db: Scoped,
    identity: Identity,
) -> ResearchJobOut:
    owner_user_id, _ = identity
    row = (await db.execute(select(ResearchJob).where(
        ResearchJob.id == job_id,
        ResearchJob.owner_user_id == owner_user_id,
    ).with_for_update())).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Research job not found.")
    if row.status != "RUNNING":
        raise HTTPException(409, "Only a running research job can be cancelled.")
    now = _now()
    row.status = "CANCELLED"
    row.completed_at = now
    row.updated_at = now
    brief = await _owned_brief(db, row.research_brief_id, owner_user_id)
    brief.status = "LOCAL_DRAFT"
    brief.updated_at = now
    _event(
        db,
        actor_user_id=owner_user_id,
        event_type="RESEARCH_JOB_CANCELLED",
        title="Research job cancelled by its owner.",
        object_type="research_job",
        object_id=row.id,
        orbit_id=brief.orbit_id,
        metadata={"previous_status": "RUNNING"},
    )
    await db.commit()
    return ResearchJobOut.model_validate(row)


class ResearchSourceIn(BaseModel):
    research_brief_id: uuid.UUID
    research_job_id: uuid.UUID | None = None
    title: str = Field(min_length=1, max_length=500)
    url: str = Field(min_length=8, max_length=4000)
    publisher: str | None = Field(default=None, max_length=300)
    source_kind: str = "OWNER_SOURCE"
    authority: str = "UNKNOWN"
    reliability: str = "UNASSESSED"
    excerpt: str = Field(min_length=1, max_length=12000)
    published_at: dt.datetime | None = None


class ResearchSourceOut(BaseModel):
    id: uuid.UUID
    owner_user_id: uuid.UUID
    research_brief_id: uuid.UUID
    research_job_id: uuid.UUID | None
    title: str
    url: str
    publisher: str | None
    source_kind: str
    authority: str
    reliability: str
    retrieval_status: str
    excerpt: str
    content_hash: str
    published_at: dt.datetime | None
    fetched_at: dt.datetime | None
    untrusted_external_content: bool
    provenance_label: str
    created_at: dt.datetime
    model_config = {"from_attributes": True}


@router.post(
    "/research/sources",
    response_model=ResearchSourceOut,
    status_code=201,
    dependencies=[Depends(require_csrf)],
)
async def add_research_source(
    payload: ResearchSourceIn,
    db: Scoped,
    identity: Identity,
) -> ResearchSourceOut:
    owner_user_id, _ = identity
    brief = await _owned_brief(db, payload.research_brief_id, owner_user_id)
    job: ResearchJob | None = None
    if payload.research_job_id:
        job = (await db.execute(select(ResearchJob).where(
            ResearchJob.id == payload.research_job_id,
            ResearchJob.owner_user_id == owner_user_id,
            ResearchJob.research_brief_id == brief.id,
        ))).scalar_one_or_none()
        if job is None:
            raise HTTPException(404, "Research job not found for this brief.")
        if job.status != "RUNNING" or job.provider_name != "OWNER_SOURCES":
            raise HTTPException(409, "Only a running owner-source job accepts manual sources.")
    source_kind = payload.source_kind.upper().strip()
    authority = payload.authority.upper().strip()
    reliability = payload.reliability.upper().strip()
    if source_kind not in {"WEB", "RSS", "API", "OWNER_SOURCE", "DOCUMENT"}:
        raise HTTPException(422, "Unsupported source kind.")
    if authority not in {"PRIMARY", "SECONDARY", "TERTIARY", "UNKNOWN"}:
        raise HTTPException(422, "Unsupported source authority.")
    if reliability not in {"HIGH", "MEDIUM", "LOW", "UNASSESSED"}:
        raise HTTPException(422, "Unsupported source reliability.")
    url = _bounded_url(payload.url)
    digest = hashlib.sha256(payload.excerpt.encode("utf-8")).hexdigest()
    duplicate = (await db.execute(select(ResearchSource).where(
        ResearchSource.owner_user_id == owner_user_id,
        ResearchSource.research_brief_id == brief.id,
        ResearchSource.url == url,
        ResearchSource.content_hash == digest,
    ))).scalar_one_or_none()
    if duplicate:
        raise HTTPException(409, "This exact source excerpt is already attached.")
    row = ResearchSource(
        owner_user_id=owner_user_id,
        research_brief_id=brief.id,
        research_job_id=job.id if job else None,
        title=payload.title,
        url=url,
        publisher=payload.publisher,
        source_kind=source_kind,
        authority=authority,
        reliability=reliability,
        retrieval_status="OWNER_SUBMITTED",
        excerpt=payload.excerpt,
        content_hash=digest,
        published_at=payload.published_at,
        fetched_at=None,
        untrusted_external_content=True,
        provenance_label="OWNER_SUPPLIED_SOURCE",
    )
    db.add(row)
    await db.flush()
    _event(
        db,
        actor_user_id=owner_user_id,
        event_type="RESEARCH_SOURCE_ADDED",
        title=f"Source added: {row.title}",
        object_type="research_source",
        object_id=row.id,
        orbit_id=brief.orbit_id,
        metadata={"retrieval_status": row.retrieval_status, "untrusted": True},
    )
    await db.commit()
    return ResearchSourceOut.model_validate(row)


@router.get("/research/sources", response_model=list[ResearchSourceOut])
async def list_research_sources(
    db: Scoped,
    identity: Identity,
    research_brief_id: uuid.UUID | None = None,
) -> list[ResearchSourceOut]:
    owner_user_id, _ = identity
    statement = select(ResearchSource).where(ResearchSource.owner_user_id == owner_user_id)
    if research_brief_id:
        statement = statement.where(ResearchSource.research_brief_id == research_brief_id)
    rows = (await db.execute(
        statement.order_by(ResearchSource.created_at.desc()).limit(200)
    )).scalars().all()
    return [ResearchSourceOut.model_validate(row) for row in rows]


class CitationIn(BaseModel):
    source_id: uuid.UUID
    relationship: str = "SUPPORTS"
    locator: str | None = Field(default=None, max_length=500)
    note: str | None = Field(default=None, max_length=4000)


class ResearchClaimIn(BaseModel):
    research_brief_id: uuid.UUID
    claim_text: str = Field(min_length=1, max_length=12000)
    uncertainty: str = Field(min_length=1, max_length=4000)
    citation_alignment: str = "MEDIUM"
    citations: list[CitationIn] = Field(min_length=1, max_length=100)


class ResearchClaimCorrectionIn(BaseModel):
    claim_text: str = Field(min_length=1, max_length=12000)
    uncertainty: str = Field(min_length=1, max_length=4000)
    citation_alignment: str = "MEDIUM"
    correction_reason: str = Field(min_length=1, max_length=4000)
    citations: list[CitationIn] = Field(min_length=1, max_length=100)


class CitationOut(BaseModel):
    id: uuid.UUID
    source_id: uuid.UUID
    relationship: str
    locator: str | None
    note: str | None
    created_at: dt.datetime
    model_config = {"from_attributes": True}


class ResearchClaimOut(BaseModel):
    id: uuid.UUID
    owner_user_id: uuid.UUID
    research_brief_id: uuid.UUID
    claim_text: str
    uncertainty: str
    citation_alignment: str
    status: str
    revision_number: int
    citations: list[CitationOut]
    created_at: dt.datetime
    updated_at: dt.datetime


async def _validate_citations(
    db: Scoped,
    citations: list[CitationIn],
    owner_user_id: uuid.UUID,
    brief_id: uuid.UUID,
) -> None:
    relationships = [item.relationship.upper().strip() for item in citations]
    if any(value not in {"SUPPORTS", "COUNTERS", "CONTEXT"} for value in relationships):
        raise HTTPException(422, "Citation relationship must support, counter, or contextualize.")
    if "SUPPORTS" not in relationships:
        raise HTTPException(422, "Every research claim needs at least one supporting citation.")
    await _owned_sources(
        db,
        [item.source_id for item in citations],
        owner_user_id,
        brief_id=brief_id,
    )


async def _claim_out(db: Scoped, row: ResearchClaim) -> ResearchClaimOut:
    citations = (await db.execute(select(ResearchCitation).where(
        ResearchCitation.claim_id == row.id,
    ).order_by(ResearchCitation.created_at))).scalars().all()
    return ResearchClaimOut(
        id=row.id,
        owner_user_id=row.owner_user_id,
        research_brief_id=row.research_brief_id,
        claim_text=row.claim_text,
        uncertainty=row.uncertainty,
        citation_alignment=row.citation_alignment,
        status=row.status,
        revision_number=row.revision_number,
        citations=[CitationOut.model_validate(item) for item in citations],
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _add_citations(
    db: Scoped,
    *,
    owner_user_id: uuid.UUID,
    claim_id: uuid.UUID,
    citations: list[CitationIn],
) -> None:
    for citation in citations:
        db.add(ResearchCitation(
            owner_user_id=owner_user_id,
            claim_id=claim_id,
            source_id=citation.source_id,
            relationship=citation.relationship.upper().strip(),
            locator=citation.locator,
            note=citation.note,
        ))


@router.post(
    "/research/claims",
    response_model=ResearchClaimOut,
    status_code=201,
    dependencies=[Depends(require_csrf)],
)
async def create_research_claim(
    payload: ResearchClaimIn,
    db: Scoped,
    identity: Identity,
) -> ResearchClaimOut:
    owner_user_id, _ = identity
    brief = await _owned_brief(db, payload.research_brief_id, owner_user_id)
    alignment = payload.citation_alignment.upper().strip()
    if alignment not in {"HIGH", "MEDIUM", "LOW"}:
        raise HTTPException(422, "Citation alignment must be HIGH, MEDIUM, or LOW.")
    await _validate_citations(db, payload.citations, owner_user_id, brief.id)
    row = ResearchClaim(
        owner_user_id=owner_user_id,
        research_brief_id=brief.id,
        claim_text=payload.claim_text,
        uncertainty=payload.uncertainty,
        citation_alignment=alignment,
    )
    db.add(row)
    await db.flush()
    _add_citations(db, owner_user_id=owner_user_id, claim_id=row.id, citations=payload.citations)
    _event(
        db,
        actor_user_id=owner_user_id,
        event_type="RESEARCH_CLAIM_CREATED",
        title="Evidence-backed research claim created.",
        object_type="research_claim",
        object_id=row.id,
        orbit_id=brief.orbit_id,
        metadata={"citation_count": len(payload.citations)},
    )
    await db.flush()
    result = await _claim_out(db, row)
    await db.commit()
    return result


@router.get("/research/claims", response_model=list[ResearchClaimOut])
async def list_research_claims(
    db: Scoped,
    identity: Identity,
    research_brief_id: uuid.UUID | None = None,
) -> list[ResearchClaimOut]:
    owner_user_id, _ = identity
    statement = select(ResearchClaim).where(ResearchClaim.owner_user_id == owner_user_id)
    if research_brief_id:
        statement = statement.where(ResearchClaim.research_brief_id == research_brief_id)
    rows = (await db.execute(
        statement.order_by(ResearchClaim.created_at.desc()).limit(200)
    )).scalars().all()
    return [await _claim_out(db, row) for row in rows]


@router.post(
    "/research/claims/{claim_id}/corrections",
    response_model=ResearchClaimOut,
    dependencies=[Depends(require_csrf)],
)
async def correct_research_claim(
    claim_id: uuid.UUID,
    payload: ResearchClaimCorrectionIn,
    db: Scoped,
    identity: Identity,
) -> ResearchClaimOut:
    owner_user_id, _ = identity
    row = (await db.execute(select(ResearchClaim).where(
        ResearchClaim.id == claim_id,
        ResearchClaim.owner_user_id == owner_user_id,
    ).with_for_update())).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Research claim not found.")
    alignment = payload.citation_alignment.upper().strip()
    if alignment not in {"HIGH", "MEDIUM", "LOW"}:
        raise HTTPException(422, "Citation alignment must be HIGH, MEDIUM, or LOW.")
    await _validate_citations(db, payload.citations, owner_user_id, row.research_brief_id)
    next_revision = row.revision_number + 1
    db.add(ResearchClaimRevision(
        owner_user_id=owner_user_id,
        claim_id=row.id,
        revision_number=next_revision,
        previous_claim_text=row.claim_text,
        current_claim_text=payload.claim_text,
        previous_uncertainty=row.uncertainty,
        current_uncertainty=payload.uncertainty,
        correction_reason=payload.correction_reason,
    ))
    await db.execute(delete(ResearchCitation).where(ResearchCitation.claim_id == row.id))
    row.claim_text = payload.claim_text
    row.uncertainty = payload.uncertainty
    row.citation_alignment = alignment
    row.status = "CORRECTED"
    row.revision_number = next_revision
    row.updated_at = _now()
    _add_citations(db, owner_user_id=owner_user_id, claim_id=row.id, citations=payload.citations)
    _event(
        db,
        actor_user_id=owner_user_id,
        event_type="RESEARCH_CLAIM_CORRECTED",
        title="Research claim corrected with a preserved revision.",
        object_type="research_claim",
        object_id=row.id,
        metadata={"revision": next_revision},
    )
    await db.flush()
    result = await _claim_out(db, row)
    await db.commit()
    return result


@router.post(
    "/research/jobs/{job_id}/complete",
    response_model=ResearchJobOut,
    dependencies=[Depends(require_csrf)],
)
async def complete_research_job(
    job_id: uuid.UUID,
    db: Scoped,
    identity: Identity,
) -> ResearchJobOut:
    owner_user_id, _ = identity
    row = (await db.execute(select(ResearchJob).where(
        ResearchJob.id == job_id,
        ResearchJob.owner_user_id == owner_user_id,
    ).with_for_update())).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Research job not found.")
    if row.status != "RUNNING":
        raise HTTPException(409, "Only a running research job can complete.")
    source_count = int((await db.execute(select(func.count(ResearchSource.id)).where(
        ResearchSource.research_job_id == row.id,
    ))).scalar_one())
    claim_count = int((await db.execute(select(func.count(ResearchClaim.id)).where(
        ResearchClaim.research_brief_id == row.research_brief_id,
    ))).scalar_one())
    counter_count = int((await db.execute(
        select(func.count(ResearchCitation.id))
        .join(ResearchClaim, ResearchClaim.id == ResearchCitation.claim_id)
        .where(
            ResearchClaim.research_brief_id == row.research_brief_id,
            ResearchCitation.relationship == "COUNTERS",
        )
    )).scalar_one())
    if source_count < 1 or claim_count < 1:
        raise HTTPException(409, "Completion needs a persisted source and cited claim.")
    if row.mode == "DEEP" and counter_count < 1:
        raise HTTPException(409, "Deep research needs at least one counter-source citation.")
    now = _now()
    row.status = "SUCCEEDED"
    row.completed_at = now
    row.updated_at = now
    brief = await _owned_brief(db, row.research_brief_id, owner_user_id)
    brief.status = "EVIDENCE_READY"
    brief.provider_status = "OWNER_SOURCES"
    brief.updated_at = now
    _event(
        db,
        actor_user_id=owner_user_id,
        event_type="RESEARCH_JOB_COMPLETED",
        title="Research job completed with persisted citations.",
        object_type="research_job",
        object_id=row.id,
        orbit_id=brief.orbit_id,
        metadata={"sources": source_count, "claims": claim_count, "counter_citations": counter_count},
    )
    await db.commit()
    return ResearchJobOut.model_validate(row)


class WatchlistIn(BaseModel):
    web_signal_question_id: uuid.UUID | None = None
    name: str = Field(min_length=1, max_length=240)
    source_url: str = Field(min_length=8, max_length=4000)
    schedule: str = "MANUAL"
    alert_enabled: bool = True
    relevance_scope: dict = Field(default_factory=dict)


class WatchlistOut(BaseModel):
    id: uuid.UUID
    owner_user_id: uuid.UUID
    web_signal_question_id: uuid.UUID | None
    name: str
    source_url: str
    schedule: str
    status: str
    connector_status: str
    alert_enabled: bool
    relevance_scope: dict
    last_content_hash: str | None
    last_checked_at: dt.datetime | None
    next_check_at: dt.datetime | None
    created_at: dt.datetime
    updated_at: dt.datetime
    model_config = {"from_attributes": True}


class WatchlistPatch(BaseModel):
    schedule: str | None = None
    status: str | None = None
    alert_enabled: bool | None = None


@router.post(
    "/web-signals/watchlists",
    response_model=WatchlistOut,
    status_code=201,
    dependencies=[Depends(require_csrf)],
)
async def create_watchlist(
    payload: WatchlistIn,
    db: Scoped,
    identity: Identity,
) -> WatchlistOut:
    owner_user_id, _ = identity
    schedule = payload.schedule.upper().strip()
    if schedule not in {"MANUAL", "HOURLY", "DAILY", "WEEKLY"}:
        raise HTTPException(422, "Unsupported watchlist schedule.")
    if payload.web_signal_question_id:
        question = (await db.execute(select(WebSignalQuestion).where(
            WebSignalQuestion.id == payload.web_signal_question_id,
            WebSignalQuestion.owner_user_id == owner_user_id,
        ))).scalar_one_or_none()
        if question is None:
            raise HTTPException(404, "Web Signal question not found.")
    url = _bounded_url(payload.source_url)
    existing = (await db.execute(select(WebWatchlist).where(
        WebWatchlist.owner_user_id == owner_user_id,
        WebWatchlist.source_url == url,
    ))).scalar_one_or_none()
    if existing:
        raise HTTPException(409, "This source is already on the watchlist.")
    row = WebWatchlist(
        owner_user_id=owner_user_id,
        web_signal_question_id=payload.web_signal_question_id,
        name=payload.name,
        source_url=url,
        schedule=schedule,
        connector_status="NOT_CONNECTED",
        alert_enabled=payload.alert_enabled,
        relevance_scope=payload.relevance_scope,
    )
    db.add(row)
    await db.flush()
    _event(
        db,
        actor_user_id=owner_user_id,
        event_type="WEB_WATCHLIST_CREATED",
        title=f"Watchlist created: {row.name}",
        object_type="web_watchlist",
        object_id=row.id,
        metadata={
            "connector_status": "NOT_CONNECTED",
            "truth": "schedule_saved_no_fetch_performed",
        },
    )
    await db.commit()
    return WatchlistOut.model_validate(row)


@router.get("/web-signals/watchlists", response_model=list[WatchlistOut])
async def list_watchlists(db: Scoped, identity: Identity) -> list[WatchlistOut]:
    owner_user_id, _ = identity
    rows = (await db.execute(select(WebWatchlist).where(
        WebWatchlist.owner_user_id == owner_user_id,
    ).order_by(WebWatchlist.updated_at.desc()).limit(100))).scalars().all()
    return [WatchlistOut.model_validate(row) for row in rows]


@router.patch(
    "/web-signals/watchlists/{watchlist_id}",
    response_model=WatchlistOut,
    dependencies=[Depends(require_csrf)],
)
async def update_watchlist(
    watchlist_id: uuid.UUID,
    payload: WatchlistPatch,
    db: Scoped,
    identity: Identity,
) -> WatchlistOut:
    owner_user_id, _ = identity
    if payload.schedule is None and payload.status is None and payload.alert_enabled is None:
        raise HTTPException(422, "A watchlist update needs at least one setting.")
    row = (await db.execute(select(WebWatchlist).where(
        WebWatchlist.id == watchlist_id,
        WebWatchlist.owner_user_id == owner_user_id,
    ).with_for_update())).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Watchlist not found.")
    if payload.schedule is not None:
        schedule = payload.schedule.upper().strip()
        if schedule not in {"MANUAL", "HOURLY", "DAILY", "WEEKLY"}:
            raise HTTPException(422, "Unsupported watchlist schedule.")
        row.schedule = schedule
    if payload.status is not None:
        status = payload.status.upper().strip()
        if status not in {"ACTIVE", "PAUSED", "ARCHIVED"}:
            raise HTTPException(422, "Unsupported watchlist status.")
        row.status = status
    if payload.alert_enabled is not None:
        row.alert_enabled = payload.alert_enabled
    row.updated_at = _now()
    await db.commit()
    return WatchlistOut.model_validate(row)


class SnapshotIn(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    summary: str = Field(min_length=1, max_length=12000)
    change_summary: str | None = Field(default=None, max_length=4000)


class SnapshotOut(BaseModel):
    id: uuid.UUID
    owner_user_id: uuid.UUID
    watchlist_id: uuid.UUID
    title: str
    summary: str
    content_hash: str
    changed_from_previous: bool
    change_summary: str | None
    capture_method: str
    captured_at: dt.datetime
    model_config = {"from_attributes": True}


@router.post(
    "/web-signals/watchlists/{watchlist_id}/owner-captures",
    response_model=SnapshotOut,
    status_code=201,
    dependencies=[Depends(require_csrf)],
)
async def capture_watchlist_snapshot(
    watchlist_id: uuid.UUID,
    payload: SnapshotIn,
    db: Scoped,
    identity: Identity,
) -> SnapshotOut:
    owner_user_id, _ = identity
    watchlist = (await db.execute(select(WebWatchlist).where(
        WebWatchlist.id == watchlist_id,
        WebWatchlist.owner_user_id == owner_user_id,
    ).with_for_update())).scalar_one_or_none()
    if watchlist is None:
        raise HTTPException(404, "Watchlist not found.")
    if watchlist.status != "ACTIVE":
        raise HTTPException(409, "Only an active watchlist accepts captures.")
    digest = hashlib.sha256(payload.summary.encode("utf-8")).hexdigest()
    if watchlist.last_content_hash == digest:
        raise HTTPException(409, "No source change: this exact capture already exists.")
    changed = watchlist.last_content_hash is not None
    if changed and not payload.change_summary:
        raise HTTPException(422, "A changed capture needs a plain-language change summary.")
    row = WebSignalSnapshot(
        owner_user_id=owner_user_id,
        watchlist_id=watchlist.id,
        title=payload.title,
        summary=payload.summary,
        content_hash=digest,
        changed_from_previous=changed,
        change_summary=payload.change_summary,
        capture_method="OWNER_CAPTURE",
    )
    db.add(row)
    await db.flush()
    now = _now()
    watchlist.last_content_hash = digest
    watchlist.last_checked_at = now
    watchlist.updated_at = now
    if changed and watchlist.alert_enabled:
        db.add(WebSignalAlert(
            owner_user_id=owner_user_id,
            watchlist_id=watchlist.id,
            snapshot_id=row.id,
            change_summary=payload.change_summary or "Owner recorded a source change.",
        ))
    _event(
        db,
        actor_user_id=owner_user_id,
        event_type="WEB_SIGNAL_OWNER_CAPTURED",
        title=f"Owner captured: {watchlist.name}",
        object_type="web_signal_snapshot",
        object_id=row.id,
        metadata={"changed": changed, "capture_method": "OWNER_CAPTURE"},
    )
    await db.commit()
    return SnapshotOut.model_validate(row)


class AlertOut(BaseModel):
    id: uuid.UUID
    owner_user_id: uuid.UUID
    watchlist_id: uuid.UUID
    snapshot_id: uuid.UUID
    status: str
    change_summary: str
    created_at: dt.datetime
    updated_at: dt.datetime
    model_config = {"from_attributes": True}


@router.get("/web-signals/alerts", response_model=list[AlertOut])
async def list_web_signal_alerts(db: Scoped, identity: Identity) -> list[AlertOut]:
    owner_user_id, _ = identity
    rows = (await db.execute(select(WebSignalAlert).where(
        WebSignalAlert.owner_user_id == owner_user_id,
    ).order_by(WebSignalAlert.created_at.desc()).limit(100))).scalars().all()
    return [AlertOut.model_validate(row) for row in rows]


class AlertStatusIn(BaseModel):
    status: str


@router.patch(
    "/web-signals/alerts/{alert_id}",
    response_model=AlertOut,
    dependencies=[Depends(require_csrf)],
)
async def update_web_signal_alert(
    alert_id: uuid.UUID,
    payload: AlertStatusIn,
    db: Scoped,
    identity: Identity,
) -> AlertOut:
    owner_user_id, _ = identity
    status = payload.status.upper().strip()
    if status not in {"READ", "DISMISSED"}:
        raise HTTPException(422, "Alert status must be READ or DISMISSED.")
    row = (await db.execute(select(WebSignalAlert).where(
        WebSignalAlert.id == alert_id,
        WebSignalAlert.owner_user_id == owner_user_id,
    ))).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Web Signal alert not found.")
    row.status = status
    row.updated_at = _now()
    await db.commit()
    return AlertOut.model_validate(row)


class ExpertProfileIn(BaseModel):
    display_name: str = Field(min_length=1, max_length=240)
    bio: str = Field(min_length=1, max_length=12000)
    domains: list[str] = Field(min_length=1, max_length=50)
    conflicts: list[str] = Field(default_factory=list, max_length=50)


class ExpertProfileOut(BaseModel):
    id: uuid.UUID
    owner_user_id: uuid.UUID
    display_name: str
    bio: str
    domains: list
    verification_status: str
    verification_scope: str
    moderation_state: str
    conflicts: list
    created_at: dt.datetime
    updated_at: dt.datetime
    model_config = {"from_attributes": True}


@router.post(
    "/experts/profiles",
    response_model=ExpertProfileOut,
    status_code=201,
    dependencies=[Depends(require_csrf)],
)
async def create_expert_profile(
    payload: ExpertProfileIn,
    db: Scoped,
    identity: Identity,
) -> ExpertProfileOut:
    owner_user_id, _ = identity
    row = ExpertProfile(
        owner_user_id=owner_user_id,
        display_name=payload.display_name,
        bio=payload.bio,
        domains=payload.domains,
        conflicts=payload.conflicts,
    )
    db.add(row)
    await db.flush()
    _event(
        db,
        actor_user_id=owner_user_id,
        event_type="EXPERT_PROFILE_CREATED",
        title="Expert profile created as self-declared.",
        object_type="expert_profile",
        object_id=row.id,
        metadata={"verification_scope": "SELF_DECLARED"},
    )
    await db.commit()
    return ExpertProfileOut.model_validate(row)


@router.get("/experts/profiles", response_model=list[ExpertProfileOut])
async def list_expert_profiles(db: Scoped, identity: Identity) -> list[ExpertProfileOut]:
    owner_user_id, _ = identity
    rows = (await db.execute(select(ExpertProfile).where(
        ExpertProfile.owner_user_id == owner_user_id,
    ).order_by(ExpertProfile.created_at.desc()))).scalars().all()
    return [ExpertProfileOut.model_validate(row) for row in rows]


class VerificationIn(BaseModel):
    verifier_email: str = Field(min_length=3, max_length=320)
    claim_type: str
    claim: str = Field(min_length=1, max_length=4000)
    evidence_url: str = Field(min_length=8, max_length=4000)
    expires_at: dt.datetime | None = None


class VerificationReviewIn(BaseModel):
    decision: str
    reviewer_note: str = Field(min_length=1, max_length=4000)


class VerificationOut(BaseModel):
    id: uuid.UUID
    profile_id: uuid.UUID
    owner_user_id: uuid.UUID
    verifier_user_id: uuid.UUID
    claim_type: str
    claim: str
    evidence_url: str
    method: str
    status: str
    reviewer_note: str | None
    expires_at: dt.datetime | None
    reviewed_at: dt.datetime | None
    created_at: dt.datetime
    updated_at: dt.datetime
    model_config = {"from_attributes": True}


@router.post(
    "/experts/profiles/{profile_id}/verifications",
    response_model=VerificationOut,
    status_code=201,
    dependencies=[Depends(require_csrf)],
)
async def request_expert_verification(
    profile_id: uuid.UUID,
    payload: VerificationIn,
    db: Scoped,
    identity: Identity,
) -> VerificationOut:
    owner_user_id, _ = identity
    profile = (await db.execute(select(ExpertProfile).where(
        ExpertProfile.id == profile_id,
        ExpertProfile.owner_user_id == owner_user_id,
    ))).scalar_one_or_none()
    if profile is None:
        raise HTTPException(404, "Expert profile not found.")
    claim_type = payload.claim_type.upper().strip()
    if claim_type not in {"IDENTITY", "CREDENTIAL"}:
        raise HTTPException(422, "Verification claim must be IDENTITY or CREDENTIAL.")
    verifier_id = (await db.execute(
        select(func.fn_active_user_id_by_email(payload.verifier_email))
    )).scalar()
    if verifier_id is None:
        raise HTTPException(404, "No active NUR account exists for that verifier email.")
    if verifier_id == owner_user_id:
        raise HTTPException(422, "An expert cannot attest their own claim.")
    row = ExpertVerification(
        profile_id=profile.id,
        owner_user_id=owner_user_id,
        verifier_user_id=verifier_id,
        claim_type=claim_type,
        claim=payload.claim,
        evidence_url=_bounded_url(payload.evidence_url),
        method="PEER_ATTESTATION",
        expires_at=payload.expires_at,
    )
    profile.verification_status = "PENDING"
    profile.verification_scope = "PEER_ATTESTATION_ONLY"
    profile.updated_at = _now()
    db.add(row)
    await db.flush()
    _event(
        db,
        actor_user_id=owner_user_id,
        event_type="EXPERT_VERIFICATION_REQUESTED",
        title="Peer attestation requested for an expert claim.",
        object_type="expert_verification",
        object_id=row.id,
        metadata={"claim_type": claim_type, "scope": "PEER_ATTESTATION_ONLY"},
    )
    await db.commit()
    return VerificationOut.model_validate(row)


@router.get("/experts/verifications", response_model=list[VerificationOut])
async def list_expert_verifications(db: Scoped, identity: Identity) -> list[VerificationOut]:
    user_id, _ = identity
    rows = (await db.execute(select(ExpertVerification).where(
        (ExpertVerification.owner_user_id == user_id)
        | (ExpertVerification.verifier_user_id == user_id)
    ).order_by(ExpertVerification.created_at.desc()))).scalars().all()
    return [VerificationOut.model_validate(row) for row in rows]


@router.post(
    "/experts/verifications/{verification_id}/review",
    response_model=VerificationOut,
    dependencies=[Depends(require_csrf)],
)
async def review_expert_verification(
    verification_id: uuid.UUID,
    payload: VerificationReviewIn,
    db: Scoped,
    identity: Identity,
) -> VerificationOut:
    verifier_user_id, _ = identity
    row = (await db.execute(select(ExpertVerification).where(
        ExpertVerification.id == verification_id,
        ExpertVerification.verifier_user_id == verifier_user_id,
    ).with_for_update())).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Verification request not found.")
    if row.status != "PENDING":
        raise HTTPException(409, "This verification request is already resolved.")
    decision = payload.decision.upper().strip()
    if decision not in {"ATTEST", "REJECT"}:
        raise HTTPException(422, "Verification decision must be ATTEST or REJECT.")
    if row.expires_at and row.expires_at <= _now():
        row.status = "EXPIRED"
    else:
        row.status = "ATTESTED" if decision == "ATTEST" else "REJECTED"
    row.reviewer_note = payload.reviewer_note
    row.reviewed_at = _now()
    row.updated_at = row.reviewed_at
    _event(
        db,
        actor_user_id=verifier_user_id,
        event_type="EXPERT_VERIFICATION_REVIEWED",
        title=f"Expert peer attestation {row.status.lower()}.",
        object_type="expert_verification",
        object_id=row.id,
        metadata={"status": row.status, "scope": "PEER_ATTESTATION_ONLY"},
    )
    await db.commit()
    return VerificationOut.model_validate(row)


class ExpertContributionIn(BaseModel):
    profile_id: uuid.UUID
    body: str = Field(min_length=1, max_length=30000)
    source_ids: list[uuid.UUID] = Field(min_length=1, max_length=100)
    conflict_disclosure: str = Field(min_length=1, max_length=4000)


class ExpertContributionOut(BaseModel):
    id: uuid.UUID
    room_id: uuid.UUID
    room_owner_user_id: uuid.UUID
    profile_id: uuid.UUID
    owner_user_id: uuid.UUID
    body: str
    source_ids: list
    conflict_disclosure: str
    verification_label: str
    moderation_state: str
    moderator_user_id: uuid.UUID | None
    moderation_note: str | None
    created_at: dt.datetime
    updated_at: dt.datetime
    model_config = {"from_attributes": True}


@router.post(
    "/experts/rooms/{room_id}/contributions",
    response_model=ExpertContributionOut,
    status_code=201,
    dependencies=[Depends(require_csrf)],
)
async def create_expert_contribution(
    room_id: uuid.UUID,
    payload: ExpertContributionIn,
    db: Scoped,
    identity: Identity,
) -> ExpertContributionOut:
    owner_user_id, _ = identity
    room, _ = await _room_role(db, room_id, owner_user_id)
    profile = (await db.execute(select(ExpertProfile).where(
        ExpertProfile.id == payload.profile_id,
        ExpertProfile.owner_user_id == owner_user_id,
        ExpertProfile.moderation_state == "ACTIVE",
    ))).scalar_one_or_none()
    if profile is None:
        raise HTTPException(404, "Active owned expert profile not found.")
    await _owned_sources(db, payload.source_ids, owner_user_id)
    row = ExpertContribution(
        room_id=room.id,
        room_owner_user_id=room.owner_user_id,
        profile_id=profile.id,
        owner_user_id=owner_user_id,
        body=payload.body,
        source_ids=[str(value) for value in payload.source_ids],
        conflict_disclosure=payload.conflict_disclosure,
        verification_label=(
            "PEER_ATTESTED_NOT_CREDENTIAL_VERIFIED"
            if profile.verification_status == "PEER_ATTESTED"
            else "SELF_DECLARED_UNVERIFIED"
        ),
    )
    db.add(row)
    await db.flush()
    _event(
        db,
        actor_user_id=owner_user_id,
        event_type="EXPERT_CONTRIBUTION_SUBMITTED",
        title=f"Expert contribution submitted to {room.title} for moderation.",
        object_type="expert_contribution",
        object_id=row.id,
        orbit_id=room.orbit_id if room.owner_user_id == owner_user_id else None,
        metadata={"room_id": str(room.id), "verification_label": row.verification_label},
    )
    await db.commit()
    return ExpertContributionOut.model_validate(row)


@router.get(
    "/experts/rooms/{room_id}/contributions",
    response_model=list[ExpertContributionOut],
)
async def list_expert_contributions(
    room_id: uuid.UUID,
    db: Scoped,
    identity: Identity,
) -> list[ExpertContributionOut]:
    user_id, _ = identity
    _, role = await _room_role(db, room_id, user_id)
    statement = select(ExpertContribution).where(ExpertContribution.room_id == room_id)
    if role not in {"OWNER", "MODERATOR"}:
        statement = statement.where(
            (ExpertContribution.moderation_state == "APPROVED")
            | (ExpertContribution.owner_user_id == user_id)
        )
    rows = (await db.execute(
        statement.order_by(ExpertContribution.created_at.desc()).limit(100)
    )).scalars().all()
    return [ExpertContributionOut.model_validate(row) for row in rows]


class ExpertModerationIn(BaseModel):
    decision: str
    note: str = Field(min_length=1, max_length=4000)


@router.post(
    "/experts/contributions/{contribution_id}/moderate",
    response_model=ExpertContributionOut,
    dependencies=[Depends(require_csrf)],
)
async def moderate_expert_contribution(
    contribution_id: uuid.UUID,
    payload: ExpertModerationIn,
    db: Scoped,
    identity: Identity,
) -> ExpertContributionOut:
    moderator_user_id, _ = identity
    row = (await db.execute(select(ExpertContribution).where(
        ExpertContribution.id == contribution_id,
    ).with_for_update())).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Expert contribution not found.")
    _, role = await _room_role(db, row.room_id, moderator_user_id)
    if role not in {"OWNER", "MODERATOR"}:
        raise HTTPException(403, "Room moderation permission is required.")
    if row.moderation_state != "PENDING":
        raise HTTPException(409, "This expert contribution is already moderated.")
    decision = payload.decision.upper().strip()
    if decision not in {"APPROVE", "REJECT"}:
        raise HTTPException(422, "Moderation decision must be APPROVE or REJECT.")
    row.moderation_state = "APPROVED" if decision == "APPROVE" else "REJECTED"
    row.moderator_user_id = moderator_user_id
    row.moderation_note = payload.note
    row.updated_at = _now()
    _event(
        db,
        actor_user_id=moderator_user_id,
        event_type="EXPERT_CONTRIBUTION_MODERATED",
        title=f"Expert contribution {row.moderation_state.lower()}.",
        object_type="expert_contribution",
        object_id=row.id,
        metadata={"room_id": str(row.room_id), "status": row.moderation_state},
    )
    await db.commit()
    return ExpertContributionOut.model_validate(row)


class TenderInsightIn(BaseModel):
    scope_kind: str = "GENERAL"
    scope_id: uuid.UUID | None = None
    insight: str = Field(min_length=1, max_length=12000)
    uncertainty: str = Field(min_length=1, max_length=4000)
    counterexample: str = Field(min_length=1, max_length=4000)
    conditions: list[dict | str] = Field(default_factory=list, max_length=100)
    source_ids: list[uuid.UUID] = Field(min_length=1, max_length=100)


class TenderCorrectionIn(TenderInsightIn):
    correction_reason: str = Field(min_length=1, max_length=4000)


class TenderActionIn(BaseModel):
    action: str


class TenderInsightOut(BaseModel):
    id: uuid.UUID
    owner_user_id: uuid.UUID
    supersedes_id: uuid.UUID | None
    scope_kind: str
    scope_id: uuid.UUID | None
    version: int
    insight: str
    uncertainty: str
    counterexample: str
    conditions: list
    source_ids: list
    status: str
    correction_reason: str | None
    provenance_label: str
    created_at: dt.datetime
    updated_at: dt.datetime
    model_config = {"from_attributes": True}


async def _validate_tender(
    db: Scoped,
    payload: TenderInsightIn,
    owner_user_id: uuid.UUID,
) -> str:
    scope_kind = payload.scope_kind.upper().strip()
    if scope_kind not in {"ORBIT", "SYSTEM", "PROJECT", "ROOM", "GENERAL"}:
        raise HTTPException(422, "Unsupported Tender Insight scope.")
    if scope_kind == "GENERAL" and payload.scope_id is not None:
        raise HTTPException(422, "A general Tender Insight cannot carry a scope id.")
    if scope_kind != "GENERAL" and payload.scope_id is None:
        raise HTTPException(422, "A scoped Tender Insight needs a scope id.")
    await _owned_sources(db, payload.source_ids, owner_user_id)
    return scope_kind


@router.post(
    "/tender-insights",
    response_model=TenderInsightOut,
    status_code=201,
    dependencies=[Depends(require_csrf)],
)
async def create_tender_insight(
    payload: TenderInsightIn,
    db: Scoped,
    identity: Identity,
) -> TenderInsightOut:
    owner_user_id, _ = identity
    scope_kind = await _validate_tender(db, payload, owner_user_id)
    version = int((await db.execute(select(func.coalesce(func.max(TenderInsight.version), 0)).where(
        TenderInsight.owner_user_id == owner_user_id,
        TenderInsight.scope_kind == scope_kind,
        TenderInsight.scope_id == payload.scope_id,
    ))).scalar_one()) + 1
    row = TenderInsight(
        owner_user_id=owner_user_id,
        scope_kind=scope_kind,
        scope_id=payload.scope_id,
        version=version,
        insight=payload.insight,
        uncertainty=payload.uncertainty,
        counterexample=payload.counterexample,
        conditions=payload.conditions,
        source_ids=[str(value) for value in payload.source_ids],
    )
    db.add(row)
    await db.flush()
    _event(
        db,
        actor_user_id=owner_user_id,
        event_type="TENDER_INSIGHT_CREATED",
        title="Evidence-linked Tender Insight created.",
        object_type="tender_insight",
        object_id=row.id,
        metadata={"scope_kind": scope_kind, "version": version},
    )
    await db.commit()
    return TenderInsightOut.model_validate(row)


@router.get("/tender-insights", response_model=list[TenderInsightOut])
async def list_tender_insights(db: Scoped, identity: Identity) -> list[TenderInsightOut]:
    owner_user_id, _ = identity
    rows = (await db.execute(select(TenderInsight).where(
        TenderInsight.owner_user_id == owner_user_id,
    ).order_by(TenderInsight.created_at.desc()).limit(200))).scalars().all()
    return [TenderInsightOut.model_validate(row) for row in rows]


@router.patch(
    "/tender-insights/{insight_id}/status",
    response_model=TenderInsightOut,
    dependencies=[Depends(require_csrf)],
)
async def act_on_tender_insight(
    insight_id: uuid.UUID,
    payload: TenderActionIn,
    db: Scoped,
    identity: Identity,
) -> TenderInsightOut:
    owner_user_id, _ = identity
    row = (await db.execute(select(TenderInsight).where(
        TenderInsight.id == insight_id,
        TenderInsight.owner_user_id == owner_user_id,
    ))).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Tender Insight not found.")
    action = payload.action.upper().strip()
    status_by_action = {"KEEP": "KEPT", "ACCEPT": "ACCEPTED", "REJECT": "REJECTED"}
    if action not in status_by_action:
        raise HTTPException(422, "Tender action must be KEEP, ACCEPT, or REJECT.")
    row.status = status_by_action[action]
    row.updated_at = _now()
    await db.commit()
    return TenderInsightOut.model_validate(row)


@router.post(
    "/tender-insights/{insight_id}/corrections",
    response_model=TenderInsightOut,
    status_code=201,
    dependencies=[Depends(require_csrf)],
)
async def correct_tender_insight(
    insight_id: uuid.UUID,
    payload: TenderCorrectionIn,
    db: Scoped,
    identity: Identity,
) -> TenderInsightOut:
    owner_user_id, _ = identity
    prior = (await db.execute(select(TenderInsight).where(
        TenderInsight.id == insight_id,
        TenderInsight.owner_user_id == owner_user_id,
    ).with_for_update())).scalar_one_or_none()
    if prior is None:
        raise HTTPException(404, "Tender Insight not found.")
    scope_kind = await _validate_tender(db, payload, owner_user_id)
    if scope_kind != prior.scope_kind or payload.scope_id != prior.scope_id:
        raise HTTPException(422, "A correction cannot silently change the insight scope.")
    prior.status = "CORRECTED"
    prior.updated_at = _now()
    row = TenderInsight(
        owner_user_id=owner_user_id,
        supersedes_id=prior.id,
        scope_kind=scope_kind,
        scope_id=payload.scope_id,
        version=prior.version + 1,
        insight=payload.insight,
        uncertainty=payload.uncertainty,
        counterexample=payload.counterexample,
        conditions=payload.conditions,
        source_ids=[str(value) for value in payload.source_ids],
        correction_reason=payload.correction_reason,
    )
    db.add(row)
    await db.flush()
    _event(
        db,
        actor_user_id=owner_user_id,
        event_type="TENDER_INSIGHT_CORRECTED",
        title="Tender Insight corrected with prior version preserved.",
        object_type="tender_insight",
        object_id=row.id,
        metadata={"supersedes_id": str(prior.id), "version": row.version},
    )
    await db.commit()
    return TenderInsightOut.model_validate(row)
