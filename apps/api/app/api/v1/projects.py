"""Owner-scoped AM Projects with explicit approval and evidence gates.

This module records work. It does not execute tools, spend, publish, deploy,
message, or grant an agent authority outside the persisted owner policy.
"""

import datetime as dt
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.api.deps import Identity, Scoped, require_csrf
from app.models import (
    AMProject,
    AMProjectArtifact,
    AMProjectEvidence,
    AMProjectReview,
    AMProjectRun,
    AMProjectTask,
    AuditEvent,
    CognitiveEvent,
    Orbit,
)
from app.models._mixins import now_utc
from app.services.glow_service import AwardResult, award_glow


router = APIRouter(prefix="/projects", tags=["am-projects"])

PROJECT_STATUSES = {"ACTIVE", "PAUSED", "COMPLETED", "ARCHIVED"}
TASK_STATUSES = {"BACKLOG", "READY", "IN_PROGRESS", "BLOCKED", "REVIEW", "DONE", "CANCELLED"}
RUN_STATUSES = {"PROPOSED", "APPROVED", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED"}
DENIED_TOOL_ACTIONS = ("spend", "publish", "deploy", "message", "modify_security", "read_secrets")


class ProjectIn(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    objective: str = Field(min_length=1, max_length=12_000)
    orbit_id: uuid.UUID | None = None
    system_slug: str | None = Field(default=None, max_length=48)
    deadline: dt.datetime | None = None
    budget_cents: int | None = Field(default=None, ge=0)


class ProjectPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=240)
    objective: str | None = Field(default=None, min_length=1, max_length=12_000)
    status: str | None = None
    system_slug: str | None = Field(default=None, max_length=48)
    deadline: dt.datetime | None = None
    budget_cents: int | None = Field(default=None, ge=0)


class ProjectOut(BaseModel):
    id: uuid.UUID
    owner_user_id: uuid.UUID
    orbit_id: uuid.UUID
    title: str
    objective: str
    status: str
    system_slug: str | None
    deadline: dt.datetime | None
    budget_cents: int | None
    permission_policy: dict
    created_at: dt.datetime
    updated_at: dt.datetime
    model_config = {"from_attributes": True}


class TaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=12_000)
    acceptance_criteria: str | None = Field(default=None, max_length=12_000)
    parent_task_id: uuid.UUID | None = None
    status: str = "BACKLOG"
    priority: int = Field(default=50, ge=0, le=100)
    assigned_role: str | None = Field(default=None, max_length=80)
    due_at: dt.datetime | None = None


class TaskPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=12_000)
    acceptance_criteria: str | None = Field(default=None, max_length=12_000)
    status: str | None = None
    priority: int | None = Field(default=None, ge=0, le=100)
    assigned_role: str | None = Field(default=None, max_length=80)
    due_at: dt.datetime | None = None


class TaskOut(BaseModel):
    id: uuid.UUID
    owner_user_id: uuid.UUID
    project_id: uuid.UUID
    parent_task_id: uuid.UUID | None
    title: str
    description: str | None
    acceptance_criteria: str | None
    status: str
    priority: int
    assigned_role: str | None
    due_at: dt.datetime | None
    completed_at: dt.datetime | None
    created_at: dt.datetime
    updated_at: dt.datetime
    model_config = {"from_attributes": True}


class RunIn(BaseModel):
    task_id: uuid.UUID | None = None
    role: str = Field(min_length=1, max_length=80)
    request_summary: str = Field(min_length=1, max_length=12_000)
    tool_policy: dict = Field(default_factory=dict)
    budget_cents: int = Field(default=0, ge=0)


class RunOut(BaseModel):
    id: uuid.UUID
    owner_user_id: uuid.UUID
    project_id: uuid.UUID
    task_id: uuid.UUID | None
    role: str
    request_summary: str
    status: str
    tool_policy: dict
    budget_cents: int
    approval_required: bool
    approved_at: dt.datetime | None
    started_at: dt.datetime | None
    completed_at: dt.datetime | None
    result_summary: str | None
    created_at: dt.datetime
    updated_at: dt.datetime
    model_config = {"from_attributes": True}


class ArtifactIn(BaseModel):
    task_id: uuid.UUID | None = None
    run_id: uuid.UUID | None = None
    artifact_kind: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=500)
    locator: str = Field(min_length=1, max_length=4000)
    checksum_sha256: str | None = Field(default=None, pattern=r"^[0-9a-fA-F]{64}$")
    provenance_label: str = Field(default="OWNER_SUPPLIED", max_length=64)
    artifact_metadata: dict = Field(default_factory=dict)


class ArtifactOut(BaseModel):
    id: uuid.UUID
    owner_user_id: uuid.UUID
    project_id: uuid.UUID
    task_id: uuid.UUID | None
    run_id: uuid.UUID | None
    artifact_kind: str
    title: str
    locator: str
    checksum_sha256: str | None
    provenance_label: str
    review_status: str
    artifact_metadata: dict
    created_at: dt.datetime
    updated_at: dt.datetime
    model_config = {"from_attributes": True}


class EvidenceIn(BaseModel):
    task_id: uuid.UUID | None = None
    run_id: uuid.UUID | None = None
    evidence_kind: str = Field(min_length=1, max_length=64)
    summary: str = Field(min_length=1, max_length=12_000)
    locator: str | None = Field(default=None, max_length=4000)
    checksum_sha256: str | None = Field(default=None, pattern=r"^[0-9a-fA-F]{64}$")
    verification_status: str = "UNVERIFIED"
    verifier: str | None = Field(default=None, max_length=120)


class EvidenceOut(BaseModel):
    id: uuid.UUID
    owner_user_id: uuid.UUID
    project_id: uuid.UUID
    task_id: uuid.UUID | None
    run_id: uuid.UUID | None
    evidence_kind: str
    summary: str
    locator: str | None
    checksum_sha256: str | None
    verification_status: str
    verifier: str | None
    created_at: dt.datetime
    updated_at: dt.datetime
    model_config = {"from_attributes": True}


class ReviewIn(BaseModel):
    task_id: uuid.UUID | None = None
    run_id: uuid.UUID | None = None
    decision: str
    note: str | None = Field(default=None, max_length=12_000)


class ReviewOut(BaseModel):
    id: uuid.UUID
    owner_user_id: uuid.UUID
    project_id: uuid.UUID
    task_id: uuid.UUID | None
    run_id: uuid.UUID | None
    decision: str
    note: str | None
    reviewer_label: str
    created_at: dt.datetime
    model_config = {"from_attributes": True}


def _event(
    db: Scoped,
    *,
    owner_user_id: uuid.UUID,
    orbit_id: uuid.UUID,
    kind: str,
    text_value: str,
    object_type: str,
    object_id: uuid.UUID,
    project_id: uuid.UUID,
) -> None:
    payload = {
        "timeline_kind": kind,
        "object_type": object_type,
        "object_id": str(object_id),
        "project_id": str(project_id),
        "provenance_label": "OWNER_LEDGER",
    }
    db.add(CognitiveEvent(
        owner_user_id=owner_user_id,
        orbit_id=orbit_id,
        event_kind="SYSTEM_EVENT",
        content_text=text_value,
        source_ref=f"{object_type}:{object_id}",
        structured_payload=payload,
    ))
    db.add(AuditEvent(
        actor_user_id=owner_user_id,
        event_type=kind,
        object_type=object_type,
        object_id=object_id,
        event_metadata=payload,
    ))


def _glow(result: AwardResult | None, reason: str | None = None) -> dict:
    if result is None:
        return {"awarded_points": 0, "status": "GATED", "reason": reason}
    return {
        "awarded_points": result.transaction.final_points,
        "status": "AWARDED",
        "transaction_id": result.transaction.id,
        "balance": result.balance.balance,
        "idempotent_replay": result.idempotent_replay,
    }


async def _award_or_gate(db: Scoped, **kwargs) -> tuple[AwardResult | None, str | None]:
    try:
        return await award_glow(db, **kwargs), None
    except HTTPException as exc:
        if exc.status_code == 409:
            return None, str(exc.detail)
        raise


async def _owned_project(db: Scoped, owner_user_id: uuid.UUID, project_id: uuid.UUID) -> AMProject:
    row = (await db.execute(select(AMProject).where(
        AMProject.id == project_id,
        AMProject.owner_user_id == owner_user_id,
    ))).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "AM Project not found.")
    return row


async def _owned_task(
    db: Scoped, owner_user_id: uuid.UUID, task_id: uuid.UUID, project_id: uuid.UUID | None = None
) -> AMProjectTask:
    query = select(AMProjectTask).where(
        AMProjectTask.id == task_id,
        AMProjectTask.owner_user_id == owner_user_id,
    )
    if project_id is not None:
        query = query.where(AMProjectTask.project_id == project_id)
    row = (await db.execute(query)).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "AM Project task not found.")
    return row


async def _owned_run(
    db: Scoped, owner_user_id: uuid.UUID, run_id: uuid.UUID, project_id: uuid.UUID | None = None
) -> AMProjectRun:
    query = select(AMProjectRun).where(
        AMProjectRun.id == run_id,
        AMProjectRun.owner_user_id == owner_user_id,
    )
    if project_id is not None:
        query = query.where(AMProjectRun.project_id == project_id)
    row = (await db.execute(query)).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "AM Project run not found.")
    return row


async def _validate_links(
    db: Scoped,
    owner_user_id: uuid.UUID,
    project_id: uuid.UUID,
    *,
    task_id: uuid.UUID | None,
    run_id: uuid.UUID | None,
) -> None:
    if task_id is not None:
        await _owned_task(db, owner_user_id, task_id, project_id)
    if run_id is not None:
        run = await _owned_run(db, owner_user_id, run_id, project_id)
        if task_id is not None and run.task_id not in {None, task_id}:
            raise HTTPException(409, "Run and task do not belong to the same work branch.")


@router.get("/summary")
async def project_summary(db: Scoped, identity: Identity) -> dict:
    owner_user_id, _ = identity
    projects = (await db.execute(select(AMProject).where(
        AMProject.owner_user_id == owner_user_id,
    ).order_by(AMProject.updated_at.desc()))).scalars().all()
    rows = []
    for project in projects:
        task_counts = dict((await db.execute(select(
            AMProjectTask.status, func.count(AMProjectTask.id),
        ).where(
            AMProjectTask.owner_user_id == owner_user_id,
            AMProjectTask.project_id == project.id,
        ).group_by(AMProjectTask.status))).all())
        evidence_passed = int((await db.execute(select(func.count(AMProjectEvidence.id)).where(
            AMProjectEvidence.owner_user_id == owner_user_id,
            AMProjectEvidence.project_id == project.id,
            AMProjectEvidence.verification_status == "PASSED",
        ))).scalar_one())
        rows.append({
            **ProjectOut.model_validate(project).model_dump(),
            "task_counts": task_counts,
            "verified_evidence": evidence_passed,
        })
    return {
        "provenance_label": "OWNER_PROJECT_LEDGER",
        "counts": {
            "projects": len(projects),
            "active": sum(row.status == "ACTIVE" for row in projects),
            "blocked_tasks": sum(row["task_counts"].get("BLOCKED", 0) for row in rows),
        },
        "projects": rows,
    }


@router.post("", response_model=ProjectOut, status_code=201, dependencies=[Depends(require_csrf)])
async def create_project(payload: ProjectIn, db: Scoped, identity: Identity) -> ProjectOut:
    owner_user_id, _ = identity
    if payload.orbit_id:
        orbit = (await db.execute(select(Orbit).where(
            Orbit.id == payload.orbit_id,
            Orbit.owner_user_id == owner_user_id,
        ))).scalar_one_or_none()
        if orbit is None:
            raise HTTPException(404, "Orbit not found.")
    else:
        orbit = Orbit(
            owner_user_id=owner_user_id,
            title=payload.title,
            kind="PROJECT",
            description=payload.objective,
        )
        db.add(orbit)
        await db.flush()
    permission_policy = {
        "external_actions_require_owner_approval": True,
        **{key: False for key in DENIED_TOOL_ACTIONS},
    }
    row = AMProject(
        owner_user_id=owner_user_id,
        orbit_id=orbit.id,
        title=payload.title,
        objective=payload.objective,
        system_slug=payload.system_slug,
        deadline=payload.deadline,
        budget_cents=payload.budget_cents,
        permission_policy=permission_policy,
    )
    db.add(row)
    await db.flush()
    _event(
        db,
        owner_user_id=owner_user_id,
        orbit_id=orbit.id,
        kind="PROJECT_CREATED",
        text_value=row.title,
        object_type="am_project",
        object_id=row.id,
        project_id=row.id,
    )
    await _award_or_gate(
        db,
        owner_user_id=owner_user_id,
        event_type="project.created",
        source_kind="AM_PROJECT",
        source_id=row.id,
        orbit_id=orbit.id,
        idempotency_key=f"project:{row.id}:created",
    )
    await db.commit()
    return ProjectOut.model_validate(row)


@router.get("", response_model=list[ProjectOut])
async def list_projects(db: Scoped, identity: Identity) -> list[ProjectOut]:
    owner_user_id, _ = identity
    rows = (await db.execute(select(AMProject).where(
        AMProject.owner_user_id == owner_user_id,
    ).order_by(AMProject.updated_at.desc()))).scalars()
    return [ProjectOut.model_validate(row) for row in rows]


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: uuid.UUID, db: Scoped, identity: Identity) -> ProjectOut:
    owner_user_id, _ = identity
    return ProjectOut.model_validate(await _owned_project(db, owner_user_id, project_id))


@router.patch("/{project_id}", response_model=ProjectOut, dependencies=[Depends(require_csrf)])
async def patch_project(
    project_id: uuid.UUID, payload: ProjectPatch, db: Scoped, identity: Identity
) -> ProjectOut:
    owner_user_id, _ = identity
    row = await _owned_project(db, owner_user_id, project_id)
    updates = payload.model_dump(exclude_unset=True)
    if (status := updates.get("status")) is not None and status not in PROJECT_STATUSES:
        raise HTTPException(422, "Unsupported project status.")
    if status == "COMPLETED":
        task_states = (await db.execute(select(AMProjectTask.status).where(
            AMProjectTask.owner_user_id == owner_user_id,
            AMProjectTask.project_id == project_id,
            AMProjectTask.status != "CANCELLED",
        ))).scalars().all()
        if not task_states or any(value != "DONE" for value in task_states):
            raise HTTPException(409, "Project completion requires at least one task and every active task DONE.")
    for key, value in updates.items():
        setattr(row, key, value)
    row.updated_at = now_utc()
    await db.commit()
    return ProjectOut.model_validate(row)


@router.post("/{project_id}/tasks", response_model=TaskOut, status_code=201, dependencies=[Depends(require_csrf)])
async def create_task(
    project_id: uuid.UUID, payload: TaskIn, db: Scoped, identity: Identity
) -> TaskOut:
    owner_user_id, _ = identity
    project = await _owned_project(db, owner_user_id, project_id)
    if payload.status not in TASK_STATUSES:
        raise HTTPException(422, "Unsupported task status.")
    if payload.parent_task_id:
        await _owned_task(db, owner_user_id, payload.parent_task_id, project_id)
    row = AMProjectTask(owner_user_id=owner_user_id, project_id=project_id, **payload.model_dump())
    db.add(row)
    await db.flush()
    _event(
        db,
        owner_user_id=owner_user_id,
        orbit_id=project.orbit_id,
        kind="PROJECT_TASK_CREATED",
        text_value=row.title,
        object_type="am_project_task",
        object_id=row.id,
        project_id=project.id,
    )
    await db.commit()
    return TaskOut.model_validate(row)


@router.get("/{project_id}/tasks", response_model=list[TaskOut])
async def list_tasks(project_id: uuid.UUID, db: Scoped, identity: Identity) -> list[TaskOut]:
    owner_user_id, _ = identity
    await _owned_project(db, owner_user_id, project_id)
    rows = (await db.execute(select(AMProjectTask).where(
        AMProjectTask.owner_user_id == owner_user_id,
        AMProjectTask.project_id == project_id,
    ).order_by(AMProjectTask.priority.desc(), AMProjectTask.created_at))).scalars()
    return [TaskOut.model_validate(row) for row in rows]


@router.patch("/tasks/{task_id}", dependencies=[Depends(require_csrf)])
async def patch_task(task_id: uuid.UUID, payload: TaskPatch, db: Scoped, identity: Identity) -> dict:
    owner_user_id, _ = identity
    row = await _owned_task(db, owner_user_id, task_id)
    project = await _owned_project(db, owner_user_id, row.project_id)
    updates = payload.model_dump(exclude_unset=True)
    target_status = updates.get("status")
    if target_status is not None and target_status not in TASK_STATUSES:
        raise HTTPException(422, "Unsupported task status.")
    glow_result = None
    glow_reason = None
    if target_status == "DONE" and row.status != "DONE":
        acceptance = updates.get("acceptance_criteria", row.acceptance_criteria)
        if not acceptance:
            raise HTTPException(409, "Task completion requires explicit acceptance criteria.")
        passed = (await db.execute(select(func.count(AMProjectEvidence.id)).where(
            AMProjectEvidence.owner_user_id == owner_user_id,
            AMProjectEvidence.project_id == row.project_id,
            AMProjectEvidence.task_id == row.id,
            AMProjectEvidence.verification_status == "PASSED",
        ))).scalar_one()
        if not passed:
            raise HTTPException(409, "Task completion requires at least one PASSED evidence record.")
        row.completed_at = now_utc()
    elif target_status != "DONE":
        row.completed_at = None
    for key, value in updates.items():
        setattr(row, key, value)
    row.updated_at = now_utc()
    if target_status == "DONE":
        _event(
            db,
            owner_user_id=owner_user_id,
            orbit_id=project.orbit_id,
            kind="PROJECT_TASK_COMPLETED",
            text_value=row.title,
            object_type="am_project_task",
            object_id=row.id,
            project_id=project.id,
        )
        glow_result, glow_reason = await _award_or_gate(
            db,
            owner_user_id=owner_user_id,
            event_type="project.task_completed",
            source_kind="AM_PROJECT_TASK",
            source_id=row.id,
            orbit_id=project.orbit_id,
            idempotency_key=f"project-task:{row.id}:completed",
        )
    await db.commit()
    return {"task": TaskOut.model_validate(row), "glow": _glow(glow_result, glow_reason)}


@router.post("/{project_id}/runs", response_model=RunOut, status_code=201, dependencies=[Depends(require_csrf)])
async def propose_run(project_id: uuid.UUID, payload: RunIn, db: Scoped, identity: Identity) -> RunOut:
    owner_user_id, _ = identity
    project = await _owned_project(db, owner_user_id, project_id)
    await _validate_links(db, owner_user_id, project_id, task_id=payload.task_id, run_id=None)
    requested_policy = {key: bool(value) for key, value in payload.tool_policy.items()}
    policy = {
        "external_actions_require_owner_approval": True,
        **{key: False for key in DENIED_TOOL_ACTIONS},
        **requested_policy,
    }
    if any(policy.get(key) for key in DENIED_TOOL_ACTIONS):
        raise HTTPException(422, "Proposed runs cannot pre-authorize spending, publishing, deployment, messaging, secret access, or security changes.")
    if project.budget_cents is not None and payload.budget_cents > project.budget_cents:
        raise HTTPException(409, "Run budget exceeds the persisted project budget.")
    row = AMProjectRun(
        owner_user_id=owner_user_id,
        project_id=project_id,
        task_id=payload.task_id,
        role=payload.role,
        request_summary=payload.request_summary,
        tool_policy=policy,
        budget_cents=payload.budget_cents,
        status="PROPOSED",
        approval_required=True,
    )
    db.add(row)
    await db.flush()
    _event(
        db,
        owner_user_id=owner_user_id,
        orbit_id=project.orbit_id,
        kind="PROJECT_RUN_PROPOSED",
        text_value=row.request_summary,
        object_type="am_project_run",
        object_id=row.id,
        project_id=project.id,
    )
    await db.commit()
    return RunOut.model_validate(row)


@router.get("/{project_id}/runs", response_model=list[RunOut])
async def list_runs(project_id: uuid.UUID, db: Scoped, identity: Identity) -> list[RunOut]:
    owner_user_id, _ = identity
    await _owned_project(db, owner_user_id, project_id)
    rows = (await db.execute(select(AMProjectRun).where(
        AMProjectRun.owner_user_id == owner_user_id,
        AMProjectRun.project_id == project_id,
    ).order_by(AMProjectRun.created_at.desc()))).scalars()
    return [RunOut.model_validate(row) for row in rows]


@router.post("/runs/{run_id}/approve", response_model=RunOut, dependencies=[Depends(require_csrf)])
async def approve_run(run_id: uuid.UUID, db: Scoped, identity: Identity) -> RunOut:
    owner_user_id, _ = identity
    row = await _owned_run(db, owner_user_id, run_id)
    project = await _owned_project(db, owner_user_id, row.project_id)
    if row.status != "PROPOSED":
        raise HTTPException(409, "Only a PROPOSED run can be approved.")
    row.status = "APPROVED"
    row.approved_at = now_utc()
    row.updated_at = now_utc()
    _event(
        db,
        owner_user_id=owner_user_id,
        orbit_id=project.orbit_id,
        kind="PROJECT_RUN_APPROVED",
        text_value=row.request_summary,
        object_type="am_project_run",
        object_id=row.id,
        project_id=project.id,
    )
    await db.commit()
    return RunOut.model_validate(row)


@router.post("/runs/{run_id}/cancel", response_model=RunOut, dependencies=[Depends(require_csrf)])
async def cancel_run(run_id: uuid.UUID, db: Scoped, identity: Identity) -> RunOut:
    owner_user_id, _ = identity
    row = await _owned_run(db, owner_user_id, run_id)
    if row.status in {"SUCCEEDED", "FAILED", "CANCELLED"}:
        raise HTTPException(409, "This run is already terminal.")
    row.status = "CANCELLED"
    row.completed_at = now_utc()
    row.updated_at = now_utc()
    await db.commit()
    return RunOut.model_validate(row)


@router.post("/{project_id}/artifacts", response_model=ArtifactOut, status_code=201, dependencies=[Depends(require_csrf)])
async def create_artifact(
    project_id: uuid.UUID, payload: ArtifactIn, db: Scoped, identity: Identity
) -> ArtifactOut:
    owner_user_id, _ = identity
    await _owned_project(db, owner_user_id, project_id)
    await _validate_links(db, owner_user_id, project_id, task_id=payload.task_id, run_id=payload.run_id)
    if payload.provenance_label == "MODEL_GENERATED" and not payload.checksum_sha256:
        raise HTTPException(409, "Generated artifacts require a SHA-256 checksum.")
    row = AMProjectArtifact(owner_user_id=owner_user_id, project_id=project_id, **payload.model_dump())
    db.add(row)
    await db.commit()
    return ArtifactOut.model_validate(row)


@router.get("/{project_id}/artifacts", response_model=list[ArtifactOut])
async def list_artifacts(project_id: uuid.UUID, db: Scoped, identity: Identity) -> list[ArtifactOut]:
    owner_user_id, _ = identity
    await _owned_project(db, owner_user_id, project_id)
    rows = (await db.execute(select(AMProjectArtifact).where(
        AMProjectArtifact.owner_user_id == owner_user_id,
        AMProjectArtifact.project_id == project_id,
    ).order_by(AMProjectArtifact.created_at.desc()))).scalars()
    return [ArtifactOut.model_validate(row) for row in rows]


@router.post("/{project_id}/evidence", status_code=201, dependencies=[Depends(require_csrf)])
async def create_evidence(
    project_id: uuid.UUID, payload: EvidenceIn, db: Scoped, identity: Identity
) -> dict:
    owner_user_id, _ = identity
    project = await _owned_project(db, owner_user_id, project_id)
    await _validate_links(db, owner_user_id, project_id, task_id=payload.task_id, run_id=payload.run_id)
    if payload.verification_status not in {"UNVERIFIED", "PASSED", "FAILED"}:
        raise HTTPException(422, "Unsupported evidence verification status.")
    if payload.verification_status == "PASSED" and (not payload.verifier or not (payload.locator or payload.checksum_sha256)):
        raise HTTPException(409, "PASSED evidence requires a named verifier and a locator or checksum.")
    row = AMProjectEvidence(owner_user_id=owner_user_id, project_id=project_id, **payload.model_dump())
    db.add(row)
    await db.flush()
    _event(
        db,
        owner_user_id=owner_user_id,
        orbit_id=project.orbit_id,
        kind="PROJECT_EVIDENCE_ADDED",
        text_value=row.summary,
        object_type="am_project_evidence",
        object_id=row.id,
        project_id=project.id,
    )
    glow_result = None
    glow_reason = None
    if row.verification_status == "PASSED":
        glow_result, glow_reason = await _award_or_gate(
            db,
            owner_user_id=owner_user_id,
            event_type="project.evidence_verified",
            source_kind="AM_PROJECT_EVIDENCE",
            source_id=row.id,
            orbit_id=project.orbit_id,
            idempotency_key=f"project-evidence:{row.id}:verified",
        )
    await db.commit()
    return {"evidence": EvidenceOut.model_validate(row), "glow": _glow(glow_result, glow_reason)}


@router.get("/{project_id}/evidence", response_model=list[EvidenceOut])
async def list_evidence(project_id: uuid.UUID, db: Scoped, identity: Identity) -> list[EvidenceOut]:
    owner_user_id, _ = identity
    await _owned_project(db, owner_user_id, project_id)
    rows = (await db.execute(select(AMProjectEvidence).where(
        AMProjectEvidence.owner_user_id == owner_user_id,
        AMProjectEvidence.project_id == project_id,
    ).order_by(AMProjectEvidence.created_at.desc()))).scalars()
    return [EvidenceOut.model_validate(row) for row in rows]


@router.post("/{project_id}/reviews", response_model=ReviewOut, status_code=201, dependencies=[Depends(require_csrf)])
async def create_review(
    project_id: uuid.UUID, payload: ReviewIn, db: Scoped, identity: Identity
) -> ReviewOut:
    owner_user_id, _ = identity
    project = await _owned_project(db, owner_user_id, project_id)
    if payload.decision not in {"APPROVE", "REJECT", "CORRECT"}:
        raise HTTPException(422, "Unsupported review decision.")
    await _validate_links(db, owner_user_id, project_id, task_id=payload.task_id, run_id=payload.run_id)
    row = AMProjectReview(
        owner_user_id=owner_user_id,
        project_id=project_id,
        reviewer_label="OWNER",
        **payload.model_dump(),
    )
    db.add(row)
    await db.flush()
    _event(
        db,
        owner_user_id=owner_user_id,
        orbit_id=project.orbit_id,
        kind="PROJECT_REVIEW_RECORDED",
        text_value=f"{row.decision}: {row.note or 'No note'}",
        object_type="am_project_review",
        object_id=row.id,
        project_id=project.id,
    )
    await db.commit()
    return ReviewOut.model_validate(row)


@router.get("/{project_id}/reviews", response_model=list[ReviewOut])
async def list_reviews(project_id: uuid.UUID, db: Scoped, identity: Identity) -> list[ReviewOut]:
    owner_user_id, _ = identity
    await _owned_project(db, owner_user_id, project_id)
    rows = (await db.execute(select(AMProjectReview).where(
        AMProjectReview.owner_user_id == owner_user_id,
        AMProjectReview.project_id == project_id,
    ).order_by(AMProjectReview.created_at.desc()))).scalars()
    return [ReviewOut.model_validate(row) for row in rows]
