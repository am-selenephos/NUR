import datetime as dt
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.api.deps import Identity, Scoped, require_csrf
from app.cognition import personal_memory_service as service
from app.models import MemoryCandidate, PersonalMemory
from app.observability.metrics import record_counter
from app.schemas.memory import (
    CandidateApprove,
    CandidateCorrect,
    CandidateReject,
    MemoryCandidateOut,
    MemoryCreate,
    MemoryDetail,
    MemoryExport,
    MemoryOut,
    MemoryPatch,
    MemoryVersionOut,
)

router = APIRouter(tags=["memory"])


def _candidate_out(row: MemoryCandidate) -> MemoryCandidateOut:
    return MemoryCandidateOut.model_validate(row)


def _memory_out(row: PersonalMemory) -> MemoryOut:
    return MemoryOut.model_validate(row)


def _raise_service_error(exc: Exception) -> None:
    if isinstance(exc, service.MemoryNotFoundError):
        raise HTTPException(404, str(exc)) from exc
    if isinstance(exc, service.MemoryConflictError):
        raise HTTPException(409, str(exc)) from exc
    raise exc


@router.get("/memory-candidates", response_model=list[MemoryCandidateOut])
async def memory_candidates(
    db: Scoped,
    identity: Identity,
    status: str | None = None,
    limit: int = 100,
) -> list[MemoryCandidateOut]:
    owner_user_id, _ = identity
    rows = await service.list_candidates(
        db,
        owner_user_id=owner_user_id,
        status=status,
        limit=limit,
    )
    return [_candidate_out(row) for row in rows]


@router.get("/memory-candidates/{candidate_id}", response_model=MemoryCandidateOut)
async def memory_candidate(
    candidate_id: uuid.UUID,
    db: Scoped,
    identity: Identity,
) -> MemoryCandidateOut:
    owner_user_id, _ = identity
    try:
        row = await service.get_candidate(
            db,
            owner_user_id=owner_user_id,
            candidate_id=candidate_id,
        )
    except Exception as exc:
        _raise_service_error(exc)
    return _candidate_out(row)


@router.post(
    "/memory-candidates/{candidate_id}/approve",
    response_model=MemoryOut,
    dependencies=[Depends(require_csrf)],
)
async def approve_memory_candidate(
    candidate_id: uuid.UUID,
    payload: CandidateApprove,
    request: Request,
    db: Scoped,
    identity: Identity,
) -> MemoryOut:
    owner_user_id, _ = identity
    try:
        row = await service.approve_candidate(
            db,
            owner_user_id=owner_user_id,
            candidate_id=candidate_id,
            memory_type=payload.memory_type,
            sensitivity=payload.sensitivity,
            review_note=payload.review_note,
        )
    except Exception as exc:
        _raise_service_error(exc)
    record_counter(request, "nur_memory_candidates_reviewed_total", (("action", "approve"),))
    await db.commit()
    return _memory_out(row)


@router.post(
    "/memory-candidates/{candidate_id}/reject",
    response_model=MemoryCandidateOut,
    dependencies=[Depends(require_csrf)],
)
async def reject_memory_candidate(
    candidate_id: uuid.UUID,
    payload: CandidateReject,
    request: Request,
    db: Scoped,
    identity: Identity,
) -> MemoryCandidateOut:
    owner_user_id, _ = identity
    try:
        row = await service.reject_candidate(
            db,
            owner_user_id=owner_user_id,
            candidate_id=candidate_id,
            review_note=payload.review_note,
        )
    except Exception as exc:
        _raise_service_error(exc)
    record_counter(request, "nur_memory_candidates_reviewed_total", (("action", "reject"),))
    await db.commit()
    return _candidate_out(row)


@router.post(
    "/memory-candidates/{candidate_id}/correct",
    response_model=MemoryCandidateOut,
    dependencies=[Depends(require_csrf)],
)
async def correct_memory_candidate(
    candidate_id: uuid.UUID,
    payload: CandidateCorrect,
    request: Request,
    db: Scoped,
    identity: Identity,
) -> MemoryCandidateOut:
    owner_user_id, _ = identity
    try:
        row = await service.correct_candidate(
            db,
            owner_user_id=owner_user_id,
            candidate_id=candidate_id,
            canonical_text=payload.canonical_text,
            correction_reason=payload.correction_reason,
            memory_type=payload.memory_type,
            sensitivity=payload.sensitivity,
        )
    except Exception as exc:
        _raise_service_error(exc)
    record_counter(request, "nur_memory_candidates_reviewed_total", (("action", "correct"),))
    await db.commit()
    return _candidate_out(row)


@router.post("/memories", status_code=201, response_model=MemoryOut, dependencies=[Depends(require_csrf)])
async def create_memory(
    payload: MemoryCreate,
    request: Request,
    db: Scoped,
    identity: Identity,
) -> MemoryOut:
    owner_user_id, _ = identity
    try:
        row = await service.create_memory(
            db,
            owner_user_id=owner_user_id,
            **payload.model_dump(),
        )
    except Exception as exc:
        _raise_service_error(exc)
    record_counter(request, "nur_memories_total", (("action", "created"),))
    await db.commit()
    return _memory_out(row)


@router.get("/memories", response_model=list[MemoryOut])
async def memories(
    request: Request,
    db: Scoped,
    identity: Identity,
    orbit_id: uuid.UUID | None = None,
    include_retired: bool = False,
    limit: int = 100,
) -> list[MemoryOut]:
    owner_user_id, _ = identity
    rows = await service.list_memories(
        db,
        owner_user_id=owner_user_id,
        orbit_id=orbit_id,
        include_retired=include_retired,
        limit=limit,
    )
    for row in rows:
        service.record_memory_access(
            db,
            owner_user_id=owner_user_id,
            memory_id=row.id,
            access_kind="VIEWED",
            purpose="OWNER_MEMORY_LIST",
        )
    record_counter(request, "nur_memory_access_total", (("kind", "list"),), len(rows))
    await db.commit()
    return [_memory_out(row) for row in rows]


@router.get("/memories/export", response_model=MemoryExport)
async def export_memories(
    request: Request,
    db: Scoped,
    identity: Identity,
) -> MemoryExport:
    owner_user_id, _ = identity
    memories = await service.list_memories(
        db,
        owner_user_id=owner_user_id,
        include_retired=True,
        limit=200,
    )
    details = []
    for row in memories:
        versions = await service.memory_versions(
            db,
            owner_user_id=owner_user_id,
            memory_id=row.id,
        )
        service.record_memory_access(
            db,
            owner_user_id=owner_user_id,
            memory_id=row.id,
            access_kind="EXPORTED",
            purpose="OWNER_MEMORY_EXPORT",
        )
        details.append(
            MemoryDetail(
                **_memory_out(row).model_dump(),
                versions=[MemoryVersionOut.model_validate(version) for version in versions],
            )
        )
    candidates = await service.list_candidates(
        db,
        owner_user_id=owner_user_id,
        limit=200,
    )
    record_counter(request, "nur_memory_access_total", (("kind", "export"),), len(memories))
    await db.commit()
    return MemoryExport(
        exported_at=dt.datetime.now(dt.UTC),
        owner_user_id=owner_user_id,
        memories=details,
        candidates=[_candidate_out(row) for row in candidates],
        safety={
            "owner_only": True,
            "chain_of_thought_excluded": True,
            "provider_state_excluded": True,
            "deleted_content_excluded": True,
        },
    )


@router.get("/memories/{memory_id}", response_model=MemoryDetail)
async def memory_detail(
    memory_id: uuid.UUID,
    request: Request,
    db: Scoped,
    identity: Identity,
) -> MemoryDetail:
    owner_user_id, _ = identity
    try:
        row = await service.get_memory(
            db,
            owner_user_id=owner_user_id,
            memory_id=memory_id,
        )
    except Exception as exc:
        _raise_service_error(exc)
    versions = await service.memory_versions(
        db,
        owner_user_id=owner_user_id,
        memory_id=row.id,
    )
    service.record_memory_access(
        db,
        owner_user_id=owner_user_id,
        memory_id=row.id,
        access_kind="VIEWED",
        purpose="OWNER_MEMORY_DETAIL",
    )
    record_counter(request, "nur_memory_access_total", (("kind", "detail"),))
    await db.commit()
    return MemoryDetail(
        **_memory_out(row).model_dump(),
        versions=[MemoryVersionOut.model_validate(version) for version in versions],
    )


@router.patch("/memories/{memory_id}", response_model=MemoryOut, dependencies=[Depends(require_csrf)])
async def patch_memory(
    memory_id: uuid.UUID,
    payload: MemoryPatch,
    request: Request,
    db: Scoped,
    identity: Identity,
) -> MemoryOut:
    owner_user_id, _ = identity
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    if not changes or set(changes) == {"correction_reason"}:
        raise HTTPException(422, "At least one memory field must change.")
    try:
        row = await service.update_memory(
            db,
            owner_user_id=owner_user_id,
            memory_id=memory_id,
            changes=changes,
        )
    except Exception as exc:
        _raise_service_error(exc)
    record_counter(request, "nur_memories_total", (("action", "updated"),))
    await db.commit()
    return _memory_out(row)


@router.delete("/memories/{memory_id}", status_code=204, dependencies=[Depends(require_csrf)])
async def delete_memory(
    memory_id: uuid.UUID,
    request: Request,
    response: Response,
    db: Scoped,
    identity: Identity,
):
    owner_user_id, _ = identity
    try:
        await service.delete_memory(
            db,
            owner_user_id=owner_user_id,
            memory_id=memory_id,
        )
    except Exception as exc:
        _raise_service_error(exc)
    record_counter(request, "nur_memories_total", (("action", "deleted"),))
    await db.commit()
    response.status_code = 204
    return None
