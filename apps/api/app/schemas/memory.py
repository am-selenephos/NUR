import datetime as dt
import uuid
from typing import Literal

from pydantic import BaseModel, Field, field_validator

MemoryType = Literal[
    "EPISODIC", "SEMANTIC", "PROCEDURAL", "SOCIAL", "EVIDENCE",
    "SELF", "GOAL", "META_COGNITIVE", "ADAPTIVE_INTERFACE",
]
Sensitivity = Literal["LOW", "PRIVATE", "SENSITIVE"]


class MemoryCreate(BaseModel):
    canonical_text: str = Field(min_length=1, max_length=8000)
    structured_value: dict = Field(default_factory=dict)
    orbit_id: uuid.UUID | None = None
    memory_type: MemoryType = "SEMANTIC"
    sensitivity: Sensitivity = "PRIVATE"
    confidence: float = Field(default=1.0, ge=0, le=1)
    expires_at: dt.datetime | None = None

    @field_validator("canonical_text")
    @classmethod
    def _canonical_text_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("canonical_text cannot be blank.")
        return stripped

    @field_validator("expires_at")
    @classmethod
    def _timezone_required(cls, value: dt.datetime | None) -> dt.datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("expires_at must include a timezone.")
        return value


class MemoryPatch(BaseModel):
    canonical_text: str | None = Field(default=None, min_length=1, max_length=8000)
    structured_value: dict | None = None
    memory_type: MemoryType | None = None
    sensitivity: Sensitivity | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    correction_reason: str | None = Field(default=None, max_length=1000)

    @field_validator("canonical_text")
    @classmethod
    def _patched_text_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("canonical_text cannot be blank.")
        return stripped


class CandidateApprove(BaseModel):
    memory_type: MemoryType | None = None
    sensitivity: Sensitivity | None = None
    review_note: str | None = Field(default=None, max_length=1000)


class CandidateReject(BaseModel):
    review_note: str | None = Field(default=None, max_length=1000)


class CandidateCorrect(BaseModel):
    canonical_text: str = Field(min_length=1, max_length=8000)
    correction_reason: str = Field(min_length=1, max_length=1000)
    memory_type: MemoryType | None = None
    sensitivity: Sensitivity | None = None

    @field_validator("canonical_text", "correction_reason")
    @classmethod
    def _correction_fields_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Correction fields cannot be blank.")
        return stripped


class MemoryCandidateOut(BaseModel):
    id: uuid.UUID
    orbit_id: uuid.UUID | None
    source_event_id: uuid.UUID | None
    candidate_text: str
    original_text: str
    scope: str
    memory_type: str
    provenance_label: str
    confidence: float
    sensitivity: str
    created_by: str
    source_object_ids: dict
    status: str
    review_note: str | None
    reviewed_at: dt.datetime | None
    approved_memory_id: uuid.UUID | None
    created_at: dt.datetime
    updated_at: dt.datetime
    model_config = {"from_attributes": True}


class MemoryOut(BaseModel):
    id: uuid.UUID
    orbit_id: uuid.UUID | None
    scope: str
    memory_type: str
    canonical_text: str
    structured_value: dict
    source_object_ids: dict
    provenance_label: str
    confidence: float
    sensitivity: str
    status: str
    created_by: str
    version: int
    superseded_by_memory_id: uuid.UUID | None
    expires_at: dt.datetime | None
    deleted_at: dt.datetime | None
    created_at: dt.datetime
    updated_at: dt.datetime
    model_config = {"from_attributes": True}


class MemoryVersionOut(BaseModel):
    id: uuid.UUID
    memory_id: uuid.UUID
    version: int
    canonical_text: str
    structured_value: dict
    provenance_label: str
    change_kind: str
    correction_reason: str | None
    changed_by: str
    created_at: dt.datetime
    model_config = {"from_attributes": True}


class MemoryDetail(MemoryOut):
    versions: list[MemoryVersionOut] = Field(default_factory=list)


class MemoryExport(BaseModel):
    exported_at: dt.datetime
    owner_user_id: uuid.UUID
    memories: list[MemoryDetail]
    candidates: list[MemoryCandidateOut]
    safety: dict
