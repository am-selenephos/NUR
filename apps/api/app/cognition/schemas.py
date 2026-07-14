from __future__ import annotations

import uuid
from enum import StrEnum

from pydantic import BaseModel, Field

from app.ai.schemas import EvidenceRef, NURTalkOutput
from app.omega.schemas import OmegaTalkSummary


class TaskMode(StrEnum):
    TALK = "talk"
    REFLECT = "reflect"
    CHALLENGE = "challenge"
    SUMMARIZE = "summarize"


class EvidencePacket(BaseModel):
    orbit_id: uuid.UUID | None = None
    retrieval: list[EvidenceRef] = Field(default_factory=list)
    withheld: list[dict] = Field(default_factory=list)


class VerificationResult(BaseModel):
    verdict: str
    checks: dict = Field(default_factory=dict)


class TalkKernelResult(BaseModel):
    turn_event_id: uuid.UUID
    response_event_id: uuid.UUID
    model_run_id: uuid.UUID
    provider: str
    provider_available: bool
    provider_reason: str | None
    output: NURTalkOutput
    evidence: EvidencePacket
    verification: VerificationResult
    omega: OmegaTalkSummary | None = None
    idempotent_replay: bool = False
