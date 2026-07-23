import datetime as dt
import uuid

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    MemoryAccessEvent,
    MemoryCandidate,
    MemoryEdge,
    MemoryVersion,
    Orbit,
    PersonalMemory,
)
from app.models._mixins import now_utc
from app.services import audit_service
from app.services.domain_event_service import emit_domain_event


class MemoryNotFoundError(RuntimeError):
    pass


class MemoryConflictError(RuntimeError):
    pass


async def list_candidates(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    status: str | None = None,
    limit: int = 100,
) -> list[MemoryCandidate]:
    query = (
        select(MemoryCandidate)
        .where(MemoryCandidate.owner_user_id == owner_user_id)
        .order_by(MemoryCandidate.created_at.desc())
        .limit(min(max(limit, 1), 200))
    )
    if status:
        query = query.where(MemoryCandidate.status == status.upper())
    return list((await db.execute(query)).scalars())


async def get_candidate(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    candidate_id: uuid.UUID,
    lock: bool = False,
) -> MemoryCandidate:
    query = select(MemoryCandidate).where(
        MemoryCandidate.id == candidate_id,
        MemoryCandidate.owner_user_id == owner_user_id,
    )
    if lock:
        query = query.with_for_update()
    row = (await db.execute(query)).scalar_one_or_none()
    if row is None:
        raise MemoryNotFoundError("Memory candidate not found.")
    return row


async def correct_candidate(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    candidate_id: uuid.UUID,
    canonical_text: str,
    correction_reason: str,
    memory_type: str | None = None,
    sensitivity: str | None = None,
) -> MemoryCandidate:
    row = await get_candidate(
        db,
        owner_user_id=owner_user_id,
        candidate_id=candidate_id,
        lock=True,
    )
    if row.status not in {"CANDIDATE", "CORRECTED"}:
        raise MemoryConflictError("Closed memory candidates cannot be corrected.")
    row.candidate_text = canonical_text.strip()
    row.provenance_label = "USER_CORRECTION"
    row.created_by = "OWNER"
    row.confidence = 1.0
    row.status = "CORRECTED"
    row.review_note = correction_reason.strip()
    row.reviewed_at = now_utc()
    row.updated_at = row.reviewed_at
    if memory_type:
        row.memory_type = memory_type
    if sensitivity:
        row.sensitivity = sensitivity
    await audit_service.record(
        db,
        event_type="MEMORY_CANDIDATE_CORRECTED",
        object_type="memory_candidate",
        actor_user_id=owner_user_id,
        object_id=row.id,
        metadata={"provenance_label": row.provenance_label, "memory_type": row.memory_type},
    )
    await emit_domain_event(
        db,
        owner_user_id=owner_user_id,
        event_type="memory.candidate.corrected",
        aggregate_type="memory_candidate",
        aggregate_id=row.id,
        idempotency_key=f"memory-candidate:{row.id}:corrected:{row.updated_at.isoformat()}",
        payload={"status": row.status, "memory_type": row.memory_type},
    )
    return row


async def reject_candidate(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    candidate_id: uuid.UUID,
    review_note: str | None,
) -> MemoryCandidate:
    row = await get_candidate(
        db,
        owner_user_id=owner_user_id,
        candidate_id=candidate_id,
        lock=True,
    )
    if row.status == "REJECTED":
        return row
    if row.status == "APPROVED":
        raise MemoryConflictError("An approved memory candidate cannot be rejected.")
    row.status = "REJECTED"
    row.review_note = review_note.strip() if review_note else None
    row.reviewed_at = now_utc()
    row.updated_at = row.reviewed_at
    await audit_service.record(
        db,
        event_type="MEMORY_CANDIDATE_REJECTED",
        object_type="memory_candidate",
        actor_user_id=owner_user_id,
        object_id=row.id,
    )
    await emit_domain_event(
        db,
        owner_user_id=owner_user_id,
        event_type="memory.candidate.rejected",
        aggregate_type="memory_candidate",
        aggregate_id=row.id,
        idempotency_key=f"memory-candidate:{row.id}:rejected",
        payload={"status": row.status},
    )
    return row


async def approve_candidate(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    candidate_id: uuid.UUID,
    memory_type: str | None = None,
    sensitivity: str | None = None,
    review_note: str | None = None,
) -> PersonalMemory:
    candidate = await get_candidate(
        db,
        owner_user_id=owner_user_id,
        candidate_id=candidate_id,
        lock=True,
    )
    if candidate.status == "APPROVED" and candidate.approved_memory_id:
        return await get_memory(
            db,
            owner_user_id=owner_user_id,
            memory_id=candidate.approved_memory_id,
            include_retired=True,
        )
    if candidate.status not in {"CANDIDATE", "CORRECTED"}:
        raise MemoryConflictError("Only an open or corrected candidate can be approved.")
    row = PersonalMemory(
        owner_user_id=owner_user_id,
        orbit_id=candidate.orbit_id,
        scope="PRIVATE_ORBIT",
        memory_type=memory_type or candidate.memory_type,
        canonical_text=candidate.candidate_text,
        structured_value={},
        source_object_ids=candidate.source_object_ids,
        provenance_label=candidate.provenance_label,
        confidence=candidate.confidence,
        sensitivity=sensitivity or candidate.sensitivity,
        status="APPROVED",
        created_by="OWNER",
        version=1,
    )
    db.add(row)
    await db.flush()
    await _append_version(
        db,
        memory=row,
        change_kind="APPROVED",
        changed_by="OWNER",
        correction_reason=candidate.review_note if candidate.status == "CORRECTED" else None,
    )
    await _create_source_edges(db, memory=row)
    candidate.status = "APPROVED"
    candidate.approved_memory_id = row.id
    candidate.review_note = review_note.strip() if review_note else candidate.review_note
    candidate.reviewed_at = now_utc()
    candidate.updated_at = candidate.reviewed_at
    await _record_memory_approved(db, memory=row, candidate_id=candidate.id)
    return row


async def create_memory(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    canonical_text: str,
    structured_value: dict,
    orbit_id: uuid.UUID | None,
    memory_type: str,
    sensitivity: str,
    confidence: float,
    expires_at: dt.datetime | None,
) -> PersonalMemory:
    await _assert_owned_orbit(db, owner_user_id=owner_user_id, orbit_id=orbit_id)
    if expires_at is not None and expires_at <= now_utc():
        raise MemoryConflictError("Memory expiry must be in the future.")
    row = PersonalMemory(
        owner_user_id=owner_user_id,
        orbit_id=orbit_id,
        scope="PRIVATE_ORBIT",
        memory_type=memory_type,
        canonical_text=canonical_text.strip(),
        structured_value=structured_value,
        source_object_ids={},
        provenance_label="OWNER_WRITTEN",
        confidence=confidence,
        sensitivity=sensitivity,
        status="APPROVED",
        created_by="OWNER",
        version=1,
        expires_at=expires_at,
    )
    db.add(row)
    await db.flush()
    await _append_version(db, memory=row, change_kind="OWNER_CREATED", changed_by="OWNER")
    await _record_memory_approved(db, memory=row)
    return row


async def list_memories(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    orbit_id: uuid.UUID | None = None,
    include_retired: bool = False,
    limit: int = 100,
) -> list[PersonalMemory]:
    query = (
        select(PersonalMemory)
        .where(PersonalMemory.owner_user_id == owner_user_id)
        .order_by(PersonalMemory.updated_at.desc())
        .limit(min(max(limit, 1), 200))
    )
    if not include_retired:
        now = now_utc()
        query = query.where(
            PersonalMemory.status == "APPROVED",
            PersonalMemory.deleted_at.is_(None),
            or_(PersonalMemory.expires_at.is_(None), PersonalMemory.expires_at > now),
        )
    if orbit_id:
        query = query.where(PersonalMemory.orbit_id == orbit_id)
    return list((await db.execute(query)).scalars())


async def get_memory(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    memory_id: uuid.UUID,
    include_retired: bool = False,
    lock: bool = False,
) -> PersonalMemory:
    query = select(PersonalMemory).where(
        PersonalMemory.id == memory_id,
        PersonalMemory.owner_user_id == owner_user_id,
    )
    if not include_retired:
        query = query.where(
            PersonalMemory.status == "APPROVED",
            PersonalMemory.deleted_at.is_(None),
            or_(PersonalMemory.expires_at.is_(None), PersonalMemory.expires_at > now_utc()),
        )
    if lock:
        query = query.with_for_update()
    row = (await db.execute(query)).scalar_one_or_none()
    if row is None:
        raise MemoryNotFoundError("Memory not found.")
    return row


async def memory_versions(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    memory_id: uuid.UUID,
) -> list[MemoryVersion]:
    query = (
        select(MemoryVersion)
        .where(
            MemoryVersion.owner_user_id == owner_user_id,
            MemoryVersion.memory_id == memory_id,
        )
        .order_by(MemoryVersion.version.asc())
    )
    return list((await db.execute(query)).scalars())


async def update_memory(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    memory_id: uuid.UUID,
    changes: dict,
) -> PersonalMemory:
    row = await get_memory(
        db,
        owner_user_id=owner_user_id,
        memory_id=memory_id,
        lock=True,
    )
    text_changed = "canonical_text" in changes and changes["canonical_text"] != row.canonical_text
    for key in ("canonical_text", "structured_value", "memory_type", "sensitivity", "confidence"):
        if key in changes:
            setattr(row, key, changes[key])
    row.version += 1
    row.updated_at = now_utc()
    if text_changed and row.provenance_label != "OWNER_WRITTEN":
        row.provenance_label = "USER_CORRECTION"
    await _append_version(
        db,
        memory=row,
        change_kind="CORRECTED" if text_changed else "EDITED",
        changed_by="OWNER",
        correction_reason=changes.get("correction_reason"),
    )
    db.add(
        MemoryAccessEvent(
            owner_user_id=owner_user_id,
            memory_id=row.id,
            access_kind="EDITED",
            purpose="OWNER_MEMORY_EDIT",
            context_ref=f"memory:{row.id}:v{row.version}",
        )
    )
    await audit_service.record(
        db,
        event_type="MEMORY_CORRECTED" if text_changed else "MEMORY_EDITED",
        object_type="memory",
        actor_user_id=owner_user_id,
        object_id=row.id,
        metadata={"version": row.version, "provenance_label": row.provenance_label},
    )
    await emit_domain_event(
        db,
        owner_user_id=owner_user_id,
        event_type="memory.corrected" if text_changed else "memory.updated",
        aggregate_type="memory",
        aggregate_id=row.id,
        idempotency_key=f"memory:{row.id}:version:{row.version}",
        payload={"version": row.version, "status": row.status, "memory_type": row.memory_type},
    )
    return row


async def delete_memory(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    memory_id: uuid.UUID,
) -> None:
    row = await get_memory(
        db,
        owner_user_id=owner_user_id,
        memory_id=memory_id,
        lock=True,
    )
    now = now_utc()
    await db.execute(
        delete(MemoryVersion).where(
            MemoryVersion.owner_user_id == owner_user_id,
            MemoryVersion.memory_id == row.id,
        )
    )
    await db.execute(
        delete(MemoryEdge).where(
            MemoryEdge.owner_user_id == owner_user_id,
            MemoryEdge.memory_id == row.id,
        )
    )
    linked_candidates = (
        await db.execute(
            select(MemoryCandidate).where(
                MemoryCandidate.owner_user_id == owner_user_id,
                MemoryCandidate.approved_memory_id == row.id,
            )
        )
    ).scalars()
    for candidate in linked_candidates:
        candidate.original_text = ""
        candidate.candidate_text = ""
        candidate.source_object_ids = {}
        candidate.review_note = None
        candidate.status = "REJECTED"
        candidate.updated_at = now
    row.version += 1
    row.canonical_text = ""
    row.structured_value = {}
    row.source_object_ids = {}
    row.status = "RETIRED"
    row.deleted_at = now
    row.updated_at = now
    db.add(
        MemoryVersion(
            owner_user_id=owner_user_id,
            memory_id=row.id,
            version=row.version,
            canonical_text="",
            structured_value={},
            provenance_label=row.provenance_label,
            change_kind="SUPERSEDED",
            correction_reason="Owner deleted memory content.",
            changed_by="OWNER",
        )
    )
    db.add(
        MemoryAccessEvent(
            owner_user_id=owner_user_id,
            memory_id=row.id,
            access_kind="DELETED",
            purpose="OWNER_MEMORY_DELETE",
            context_ref=f"memory:{row.id}",
        )
    )
    await audit_service.record(
        db,
        event_type="MEMORY_DELETED",
        object_type="memory",
        actor_user_id=owner_user_id,
        object_id=row.id,
        metadata={"version": row.version},
    )
    await emit_domain_event(
        db,
        owner_user_id=owner_user_id,
        event_type="memory.deleted",
        aggregate_type="memory",
        aggregate_id=row.id,
        idempotency_key=f"memory:{row.id}:deleted",
        payload={"version": row.version, "status": row.status},
    )


def record_memory_access(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    memory_id: uuid.UUID,
    access_kind: str,
    purpose: str,
    context_ref: str | None = None,
) -> None:
    db.add(
        MemoryAccessEvent(
            owner_user_id=owner_user_id,
            memory_id=memory_id,
            access_kind=access_kind,
            purpose=purpose,
            context_ref=context_ref,
        )
    )


async def _append_version(
    db: AsyncSession,
    *,
    memory: PersonalMemory,
    change_kind: str,
    changed_by: str,
    correction_reason: str | None = None,
) -> MemoryVersion:
    row = MemoryVersion(
        owner_user_id=memory.owner_user_id,
        memory_id=memory.id,
        version=memory.version,
        canonical_text=memory.canonical_text,
        structured_value=memory.structured_value,
        provenance_label=memory.provenance_label,
        change_kind=change_kind,
        correction_reason=correction_reason,
        changed_by=changed_by,
    )
    db.add(row)
    await db.flush()
    return row


async def _create_source_edges(db: AsyncSession, *, memory: PersonalMemory) -> None:
    source_ids = memory.source_object_ids or {}
    candidates: list[tuple[str, str]] = []
    key_kinds = {
        "user_message_event_id": "COGNITIVE_EVENT",
        "assistant_message_event_id": "COGNITIVE_EVENT",
        "model_run_id": "MODEL_RUN",
        "insight_id": "INSIGHT",
        "outcome_id": "OUTCOME",
        "plan_step_id": "PLAN_STEP",
    }
    for key, kind in key_kinds.items():
        value = source_ids.get(key)
        if value:
            candidates.append((kind, str(value)))
    for ref in source_ids.get("source_refs", []):
        kind, separator, value = str(ref).partition(":")
        if separator:
            candidates.append((kind[:48].upper(), value))
    for item in source_ids.get("evidence_sources", []):
        if isinstance(item, dict) and item.get("id") and item.get("kind"):
            candidates.append((str(item["kind"])[:48].upper(), str(item["id"])))
    seen: set[tuple[str, uuid.UUID]] = set()
    for kind, raw_id in candidates:
        try:
            source_id = uuid.UUID(raw_id)
        except ValueError:
            continue
        marker = (kind, source_id)
        if marker in seen:
            continue
        seen.add(marker)
        db.add(
            MemoryEdge(
                owner_user_id=memory.owner_user_id,
                memory_id=memory.id,
                relation="DERIVED_FROM",
                source_kind=kind,
                source_id=source_id,
                edge_metadata={"provenance_label": memory.provenance_label},
            )
        )


async def _record_memory_approved(
    db: AsyncSession,
    *,
    memory: PersonalMemory,
    candidate_id: uuid.UUID | None = None,
) -> None:
    await audit_service.record(
        db,
        event_type="MEMORY_APPROVED",
        object_type="memory",
        actor_user_id=memory.owner_user_id,
        object_id=memory.id,
        metadata={
            "candidate_id": str(candidate_id) if candidate_id else None,
            "memory_type": memory.memory_type,
            "provenance_label": memory.provenance_label,
            "version": memory.version,
        },
    )
    await emit_domain_event(
        db,
        owner_user_id=memory.owner_user_id,
        event_type="memory.approved",
        aggregate_type="memory",
        aggregate_id=memory.id,
        idempotency_key=f"memory:{memory.id}:approved:v{memory.version}",
        payload={
            "candidate_id": str(candidate_id) if candidate_id else None,
            "memory_type": memory.memory_type,
            "scope": memory.scope,
            "provenance_label": memory.provenance_label,
            "status": memory.status,
            "version": memory.version,
        },
    )


async def _assert_owned_orbit(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    orbit_id: uuid.UUID | None,
) -> None:
    if orbit_id is None:
        return
    owned = (
        await db.execute(
            select(Orbit.id).where(Orbit.id == orbit_id, Orbit.owner_user_id == owner_user_id)
        )
    ).scalar_one_or_none()
    if owned is None:
        raise MemoryNotFoundError("Orbit not found.")
