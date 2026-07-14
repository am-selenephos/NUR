"""Project Orbits (amendment Gate 2): owner-bound project containers, their
decisions/references/constraints/open-questions, and the explicit source
allowlist (orbit_sources) that alone can ever be shared."""
import datetime as dt
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import Identity, Scoped, require_csrf
from app.living.catalog import SYSTEMS
from app.models import (
    CognitiveEvent, Decision, MemoryCandidate, Orbit, OrbitEvent, OrbitMember,
    OrbitReference, OrbitSource, Outcome, Person, Plan, PlanStep, ResearchDraft,
)

router = APIRouter(prefix="/orbits", tags=["orbits"])
SYSTEM_TITLES = tuple(system.title for system in SYSTEMS)

SOURCE_TABLES = {
    "DECISION": "decisions", "REFERENCE": "orbit_references", "JOURNAL_ENTRY": "journal_entries",
    "PLAN": "plans", "PLAN_STEP": "plan_steps", "OUTCOME": "outcomes",
    "COGNITIVE_EVENT": "cognitive_events", "RESEARCH_DRAFT": "research_drafts",
    "RESEARCH_BRIEF": "research_briefs", "RESEARCH_SOURCE_NOTE": "research_source_notes",
    "WEB_SIGNAL_NOTE": "web_signal_notes",
}


class OrbitIn(BaseModel):
    title: str
    kind: str = "PROJECT"
    description: str | None = None
    primary_person_id: uuid.UUID | None = None
    system_slug: str | None = None
    privacy_scope: str = "PRIVATE_ORBIT"
    metadata: dict = Field(default_factory=dict)


class OrbitRow(BaseModel):
    id: uuid.UUID
    title: str
    kind: str
    description: str | None
    status: str
    primary_person_id: uuid.UUID | None
    system_slug: str | None
    privacy_scope: str
    orbit_metadata: dict
    created_at: dt.datetime
    model_config = {"from_attributes": True}


class OrbitStateOut(BaseModel):
    active_systems: int
    outcomes_returned: int
    insights_evolving: int
    open_questions: int
    research_staged: int
    plans_active: int
    live_status: str


@router.post("", response_model=OrbitRow, status_code=201, dependencies=[Depends(require_csrf)])
async def create_orbit(payload: OrbitIn, db: Scoped, identity: Identity) -> OrbitRow:
    user_id, _ = identity
    kind = payload.kind.upper().strip()
    if kind == "PERSONAL_BRIDGE":
        raise HTTPException(422, "The personal bridge orbit is created at registration.")
    allowed = {"PROJECT", "CREATIVE", "RESEARCH", "CARE", "PERSON", "GROUP", "COUNCIL", "COMMUNITY", "SYSTEM"}
    if kind not in allowed:
        raise HTTPException(422, f"kind must be one of: {', '.join(sorted(allowed))}.")
    if payload.primary_person_id:
        person = (await db.execute(select(Person).where(
            Person.id == payload.primary_person_id,
            Person.owner_user_id == user_id,
        ))).scalar_one_or_none()
        if person is None:
            raise HTTPException(404, "Person not found.")
    orbit = Orbit(
        owner_user_id=user_id,
        title=payload.title,
        kind=kind,
        description=payload.description,
        primary_person_id=payload.primary_person_id,
        system_slug=payload.system_slug,
        privacy_scope=payload.privacy_scope,
        orbit_metadata=payload.metadata,
    )
    db.add(orbit)
    await db.flush()
    if payload.primary_person_id:
        db.add(OrbitMember(
            owner_user_id=user_id,
            orbit_id=orbit.id,
            person_id=payload.primary_person_id,
            role="PRIMARY",
        ))
    await db.commit()
    return OrbitRow.model_validate(orbit)


@router.get("", response_model=list[OrbitRow])
async def list_orbits(db: Scoped, identity: Identity) -> list[OrbitRow]:
    user_id, _ = identity
    rows = (await db.execute(select(Orbit).where(Orbit.owner_user_id == user_id).order_by(Orbit.created_at))).scalars()
    return [OrbitRow.model_validate(o) for o in rows]


@router.get("/current-state", response_model=OrbitStateOut)
async def current_state(db: Scoped, identity: Identity) -> OrbitStateOut:
    user_id, _ = identity
    counts = {}
    for key, stmt in {
        "active_systems": select(func.count(Orbit.id)).where(
            Orbit.owner_user_id == user_id,
            Orbit.title.in_(SYSTEM_TITLES),
            Orbit.status == "ACTIVE",
        ),
        "outcomes_returned": select(func.count(Outcome.id)).where(Outcome.owner_user_id == user_id),
        "insights_evolving": select(func.count(MemoryCandidate.id)).where(
            MemoryCandidate.owner_user_id == user_id,
            MemoryCandidate.status == "CANDIDATE",
        ),
        "open_questions": select(func.count(OrbitReference.id)).where(
            OrbitReference.owner_user_id == user_id,
            OrbitReference.kind == "OPEN_QUESTION",
        ),
        "research_staged": select(func.count(ResearchDraft.id)).where(ResearchDraft.owner_user_id == user_id),
        "plans_active": select(func.count(Plan.id)).where(
            Plan.owner_user_id == user_id,
            Plan.status == "ACTIVE",
        ),
    }.items():
        counts[key] = int((await db.execute(stmt)).scalar_one())
    return OrbitStateOut(**counts, live_status="owner_ledger")


async def _owned_orbit(db: AsyncSession, user_id: uuid.UUID, orbit_id: uuid.UUID) -> Orbit:
    o = (await db.execute(select(Orbit).where(Orbit.id == orbit_id, Orbit.owner_user_id == user_id))).scalar_one_or_none()
    if not o:
        raise HTTPException(404, "Orbit not found.")
    return o


class PersonIn(BaseModel):
    display_name: str = Field(min_length=1, max_length=240)
    handle: str | None = None
    relationship_type: str | None = None
    notes: str | None = None
    privacy_scope: str = "PRIVATE_ORBIT"


class PersonOut(PersonIn):
    id: uuid.UUID
    created_at: dt.datetime
    updated_at: dt.datetime

    model_config = {"from_attributes": True}


class MemberIn(BaseModel):
    person_id: uuid.UUID
    role: str = "MEMBER"
    closeness_score: int = Field(default=0, ge=0, le=100)
    recent_activity_score: int = Field(default=0, ge=0, le=100)
    unresolved_count: int = Field(default=0, ge=0)
    shared_goal_count: int = Field(default=0, ge=0)
    last_interaction_at: dt.datetime | None = None


class MemberOut(MemberIn):
    id: uuid.UUID
    orbit_id: uuid.UUID
    created_at: dt.datetime
    updated_at: dt.datetime

    model_config = {"from_attributes": True}


class OrbitEventIn(BaseModel):
    event_type: str = Field(min_length=2, max_length=80)
    summary: str = Field(min_length=1, max_length=4000)
    source_type: str | None = None
    source_id: uuid.UUID | None = None
    occurred_at: dt.datetime | None = None
    metadata: dict = Field(default_factory=dict)


class OrbitEventOut(BaseModel):
    id: uuid.UUID
    orbit_id: uuid.UUID
    event_type: str
    source_type: str | None
    source_id: uuid.UUID | None
    summary: str
    occurred_at: dt.datetime
    event_metadata: dict
    created_at: dt.datetime

    model_config = {"from_attributes": True}


class ConversationOrbitIn(BaseModel):
    display_name: str = Field(min_length=1, max_length=240)
    relationship_type: str | None = None
    conversation_summary: str = Field(min_length=1, max_length=4000)
    unresolved_count: int = Field(default=0, ge=0)
    shared_goal_count: int = Field(default=0, ge=0)


class CouncilIn(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    purpose: str = Field(min_length=1, max_length=1000)
    person_ids: list[uuid.UUID] = Field(min_length=1, max_length=20)


@router.post("/people", response_model=PersonOut, status_code=201, dependencies=[Depends(require_csrf)])
async def create_person(payload: PersonIn, db: Scoped, identity: Identity) -> PersonOut:
    user_id, _ = identity
    row = Person(owner_user_id=user_id, **payload.model_dump())
    db.add(row)
    await db.commit()
    return PersonOut.model_validate(row)


@router.get("/people", response_model=list[PersonOut])
async def list_people(db: Scoped, identity: Identity) -> list[PersonOut]:
    user_id, _ = identity
    rows = (await db.execute(select(Person).where(
        Person.owner_user_id == user_id,
    ).order_by(Person.updated_at.desc()))).scalars().all()
    return [PersonOut.model_validate(row) for row in rows]


@router.post("/from-conversation", status_code=201, dependencies=[Depends(require_csrf)])
async def orbit_from_conversation(payload: ConversationOrbitIn, db: Scoped, identity: Identity) -> dict:
    user_id, _ = identity
    person = Person(
        owner_user_id=user_id,
        display_name=payload.display_name,
        relationship_type=payload.relationship_type,
        privacy_scope="PRIVATE_ORBIT",
    )
    db.add(person)
    await db.flush()
    orbit = Orbit(
        owner_user_id=user_id,
        title=payload.display_name,
        kind="PERSON",
        description="Owner-created Person Orbit from a bounded conversation summary.",
        primary_person_id=person.id,
        privacy_scope="PRIVATE_ORBIT",
    )
    db.add(orbit)
    await db.flush()
    db.add(OrbitMember(
        owner_user_id=user_id,
        orbit_id=orbit.id,
        person_id=person.id,
        role="PRIMARY",
        recent_activity_score=50,
        unresolved_count=payload.unresolved_count,
        shared_goal_count=payload.shared_goal_count,
        last_interaction_at=dt.datetime.now(dt.UTC),
    ))
    event = OrbitEvent(
        owner_user_id=user_id,
        orbit_id=orbit.id,
        event_type="CONVERSATION_SUMMARY",
        source_type="OWNER_SUMMARY",
        summary=payload.conversation_summary,
    )
    db.add(event)
    db.add(CognitiveEvent(
        owner_user_id=user_id,
        orbit_id=orbit.id,
        event_kind="SYSTEM_EVENT",
        content_text=f"Person Orbit created for {person.display_name}.",
        source_ref=f"orbit:{orbit.id}",
        structured_payload={
            "timeline_kind": "PERSON_ORBIT_CREATED",
            "person_id": str(person.id),
            "provenance_label": "OWNER_SOCIAL_LEDGER",
        },
    ))
    await db.commit()
    return {"person": PersonOut.model_validate(person), "orbit": OrbitRow.model_validate(orbit)}


@router.get("/{orbit_id}")
async def orbit_detail(orbit_id: uuid.UUID, db: Scoped, identity: Identity) -> dict:
    user_id, _ = identity
    orbit = await _owned_orbit(db, user_id, orbit_id)
    members = (await db.execute(select(OrbitMember).where(
        OrbitMember.owner_user_id == user_id,
        OrbitMember.orbit_id == orbit.id,
    ).order_by(OrbitMember.recent_activity_score.desc()))).scalars().all()
    people_ids = [row.person_id for row in members]
    people = (await db.execute(select(Person).where(
        Person.owner_user_id == user_id,
        Person.id.in_(people_ids),
    ))).scalars().all()
    people_by_id = {row.id: row for row in people}
    events = (await db.execute(select(OrbitEvent).where(
        OrbitEvent.owner_user_id == user_id,
        OrbitEvent.orbit_id == orbit.id,
    ).order_by(OrbitEvent.occurred_at.desc()).limit(40))).scalars().all()
    return {
        "orbit": OrbitRow.model_validate(orbit),
        "members": [{
            **MemberOut.model_validate(row).model_dump(),
            "person": PersonOut.model_validate(people_by_id[row.person_id]).model_dump(),
        } for row in members if row.person_id in people_by_id],
        "events": [OrbitEventOut.model_validate(row) for row in events],
        "privacy": {
            "scope": orbit.privacy_scope,
            "personal_talk_included": False,
            "personal_journal_included": False,
            "omega_included": False,
        },
    }


@router.post("/{orbit_id}/members", response_model=MemberOut, status_code=201, dependencies=[Depends(require_csrf)])
async def add_orbit_member(
    orbit_id: uuid.UUID, payload: MemberIn, db: Scoped, identity: Identity
) -> MemberOut:
    user_id, _ = identity
    await _owned_orbit(db, user_id, orbit_id)
    person = (await db.execute(select(Person).where(
        Person.id == payload.person_id,
        Person.owner_user_id == user_id,
    ))).scalar_one_or_none()
    if person is None:
        raise HTTPException(404, "Person not found.")
    row = OrbitMember(owner_user_id=user_id, orbit_id=orbit_id, **payload.model_dump())
    db.add(row)
    await db.commit()
    return MemberOut.model_validate(row)


@router.post("/{orbit_id}/events", response_model=OrbitEventOut, status_code=201, dependencies=[Depends(require_csrf)])
async def add_orbit_event(
    orbit_id: uuid.UUID, payload: OrbitEventIn, db: Scoped, identity: Identity
) -> OrbitEventOut:
    user_id, _ = identity
    await _owned_orbit(db, user_id, orbit_id)
    row = OrbitEvent(
        owner_user_id=user_id,
        orbit_id=orbit_id,
        event_type=payload.event_type.upper(),
        source_type=payload.source_type,
        source_id=payload.source_id,
        summary=payload.summary,
        occurred_at=payload.occurred_at or dt.datetime.now(dt.UTC),
        event_metadata=payload.metadata,
    )
    db.add(row)
    await db.commit()
    return OrbitEventOut.model_validate(row)


@router.post("/{orbit_id}/summary")
async def summarize_orbit(orbit_id: uuid.UUID, db: Scoped, identity: Identity) -> dict:
    user_id, _ = identity
    orbit = await _owned_orbit(db, user_id, orbit_id)
    members = (await db.execute(select(OrbitMember).where(
        OrbitMember.owner_user_id == user_id,
        OrbitMember.orbit_id == orbit.id,
    ))).scalars().all()
    events = (await db.execute(select(OrbitEvent).where(
        OrbitEvent.owner_user_id == user_id,
        OrbitEvent.orbit_id == orbit.id,
    ).order_by(OrbitEvent.occurred_at.desc()).limit(12))).scalars().all()
    return {
        "orbit_id": orbit.id,
        "title": orbit.title,
        "kind": orbit.kind,
        "member_count": len(members),
        "unresolved_count": sum(row.unresolved_count for row in members),
        "shared_goal_count": sum(row.shared_goal_count for row in members),
        "latest_event": OrbitEventOut.model_validate(events[0]) if events else None,
        "next_action": (
            "Name the oldest unresolved thread and choose a bounded next contact."
            if any(row.unresolved_count for row in members)
            else "No unresolved social loop is persisted."
        ),
        "provenance_label": "OWNER_SOCIAL_LEDGER",
    }


@router.post("/{orbit_id}/create-plan", dependencies=[Depends(require_csrf)])
async def create_orbit_plan(orbit_id: uuid.UUID, db: Scoped, identity: Identity) -> dict:
    user_id, _ = identity
    orbit = await _owned_orbit(db, user_id, orbit_id)
    plan = Plan(owner_user_id=user_id, orbit_id=orbit.id, title=f"Return to {orbit.title}")
    db.add(plan)
    await db.flush()
    step = PlanStep(
        owner_user_id=user_id,
        plan_id=plan.id,
        title=f"Choose one bounded next move with {orbit.title}",
        position=0,
    )
    db.add(step)
    await db.commit()
    return {"plan_id": plan.id, "plan_step_id": step.id, "route": "/plan"}


@router.post("/{orbit_id}/start-council", dependencies=[Depends(require_csrf)])
async def start_council(
    orbit_id: uuid.UUID, payload: CouncilIn, db: Scoped, identity: Identity
) -> dict:
    user_id, _ = identity
    source = await _owned_orbit(db, user_id, orbit_id)
    people = (await db.execute(select(Person).where(
        Person.owner_user_id == user_id,
        Person.id.in_(payload.person_ids),
    ))).scalars().all()
    if len({row.id for row in people}) != len(set(payload.person_ids)):
        raise HTTPException(404, "One or more council people were not found.")
    council = Orbit(
        owner_user_id=user_id,
        title=payload.title,
        kind="COUNCIL",
        description=payload.purpose,
        privacy_scope="PRIVATE_ORBIT",
        orbit_metadata={"source_orbit_id": str(source.id), "group_memory_separate": True},
    )
    db.add(council)
    await db.flush()
    for person in people:
        db.add(OrbitMember(
            owner_user_id=user_id,
            orbit_id=council.id,
            person_id=person.id,
            role="COUNCIL_MEMBER",
        ))
    db.add(OrbitEvent(
        owner_user_id=user_id,
        orbit_id=council.id,
        event_type="COUNCIL_STARTED",
        source_type="ORBIT",
        source_id=source.id,
        summary=payload.purpose,
        event_metadata={"personal_memory_included": False},
    ))
    await db.commit()
    return {
        "council": OrbitRow.model_validate(council),
        "member_count": len(people),
        "privacy": "Council memory is separate; no personal Talk, Journal, Timeline, or Omega was copied.",
    }


class DecisionIn(BaseModel):
    statement: str
    rationale: str | None = None


class DecisionOut(DecisionIn):
    id: uuid.UUID
    status: str
    created_at: dt.datetime
    model_config = {"from_attributes": True}


@router.post("/{orbit_id}/decisions", response_model=DecisionOut, status_code=201, dependencies=[Depends(require_csrf)])
async def add_decision(orbit_id: uuid.UUID, payload: DecisionIn, db: Scoped, identity: Identity) -> DecisionOut:
    user_id, _ = identity
    await _owned_orbit(db, user_id, orbit_id)
    d = Decision(owner_user_id=user_id, orbit_id=orbit_id, statement=payload.statement, rationale=payload.rationale)
    db.add(d)
    await db.commit()
    return DecisionOut.model_validate(d)


@router.get("/{orbit_id}/decisions", response_model=list[DecisionOut])
async def list_decisions(orbit_id: uuid.UUID, db: Scoped, identity: Identity) -> list[DecisionOut]:
    user_id, _ = identity
    await _owned_orbit(db, user_id, orbit_id)
    rows = (await db.execute(select(Decision).where(Decision.orbit_id == orbit_id, Decision.owner_user_id == user_id).order_by(Decision.created_at.desc()))).scalars()
    return [DecisionOut.model_validate(d) for d in rows]


class ReferenceIn(BaseModel):
    title: str
    body: str | None = None
    url: str | None = None
    kind: str = "REFERENCE"  # REFERENCE | CONSTRAINT | OPEN_QUESTION


class ReferenceOut(ReferenceIn):
    id: uuid.UUID
    created_at: dt.datetime
    model_config = {"from_attributes": True}


@router.post("/{orbit_id}/references", response_model=ReferenceOut, status_code=201, dependencies=[Depends(require_csrf)])
async def add_reference(orbit_id: uuid.UUID, payload: ReferenceIn, db: Scoped, identity: Identity) -> ReferenceOut:
    user_id, _ = identity
    await _owned_orbit(db, user_id, orbit_id)
    r = OrbitReference(owner_user_id=user_id, orbit_id=orbit_id, **payload.model_dump())
    db.add(r)
    await db.commit()
    return ReferenceOut.model_validate(r)


@router.get("/{orbit_id}/references", response_model=list[ReferenceOut])
async def list_references(orbit_id: uuid.UUID, db: Scoped, identity: Identity, kind: str | None = None) -> list[ReferenceOut]:
    user_id, _ = identity
    await _owned_orbit(db, user_id, orbit_id)
    q = select(OrbitReference).where(OrbitReference.orbit_id == orbit_id, OrbitReference.owner_user_id == user_id).order_by(OrbitReference.created_at.desc())
    if kind:
        q = q.where(OrbitReference.kind == kind)
    return [ReferenceOut.model_validate(r) for r in (await db.execute(q)).scalars()]


class SourceIn(BaseModel):
    source_kind: str
    source_id: uuid.UUID
    inclusion_mode: str = "FULL"


class SourceOut(SourceIn):
    id: uuid.UUID
    created_at: dt.datetime
    model_config = {"from_attributes": True}


@router.post("/{orbit_id}/sources", response_model=SourceOut, status_code=201, dependencies=[Depends(require_csrf)])
async def attach_source(orbit_id: uuid.UUID, payload: SourceIn, db: Scoped, identity: Identity) -> SourceOut:
    """Explicit allowlisting (amendment §3): the target row must exist AND be
    owned by the caller — verified here, and RLS re-verifies beneath."""
    user_id, _ = identity
    await _owned_orbit(db, user_id, orbit_id)
    table = SOURCE_TABLES.get(payload.source_kind)
    if not table:
        raise HTTPException(422, "Unknown source kind.")
    owned = (await db.execute(text(
        f"SELECT 1 FROM {table} WHERE id = :sid AND owner_user_id = :uid"),
        {"sid": str(payload.source_id), "uid": str(user_id)})).first()
    if not owned:
        raise HTTPException(404, "Source object not found among your owned objects.")
    src = OrbitSource(orbit_id=orbit_id, owner_user_id=user_id, **payload.model_dump())
    db.add(src)
    await db.commit()
    return SourceOut.model_validate(src)


@router.get("/{orbit_id}/sources", response_model=list[SourceOut])
async def list_sources(orbit_id: uuid.UUID, db: Scoped, identity: Identity) -> list[SourceOut]:
    user_id, _ = identity
    await _owned_orbit(db, user_id, orbit_id)
    rows = (await db.execute(select(OrbitSource).where(OrbitSource.orbit_id == orbit_id, OrbitSource.owner_user_id == user_id))).scalars()
    return [SourceOut.model_validate(s) for s in rows]
