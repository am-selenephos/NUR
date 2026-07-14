from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Literal, TypeAlias

from pydantic import BaseModel, Field, model_validator


class EvidenceRef(BaseModel):
    kind: str
    id: str
    excerpt: str
    rank: float = 0


class TalkProviderRequest(BaseModel):
    user_line: str
    orbit_id: str | None = None
    retrieval: list[EvidenceRef] = Field(default_factory=list)
    omega_context: dict | None = None
    locale: str = "en"
    writing_preference: str = "default"
    mode: Literal["talk", "challenge", "reflect", "summarize"] = "talk"


class NURTalkOutput(BaseModel):
    direct_response: str
    observed: list[str] = Field(default_factory=list)
    inferred: list[str] = Field(default_factory=list)
    hypotheses: list[str] = Field(default_factory=list)
    uncertainty: list[str] = Field(default_factory=list)
    next_move: str | None = None
    memory_candidates: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _bounded(self) -> "NURTalkOutput":
        if self.next_move and len(self.next_move) > 260:
            raise ValueError("next_move must be one concise move.")
        for ref in self.source_refs:
            if not ref or ":" not in ref:
                raise ValueError("source_refs must be concrete kind:id strings.")
        return self


class AIProviderResult(BaseModel):
    provider: str
    model: str | None = None
    available: bool
    reason: str | None = None
    output: NURTalkOutput
    usage: dict = Field(default_factory=dict)
    raw_response_id: str | None = None


AIStreamSink: TypeAlias = Callable[[str, dict[str, Any]], Awaitable[None]]
