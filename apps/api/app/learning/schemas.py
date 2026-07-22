import datetime as dt
import uuid
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


ContributionKind = Literal[
    "FACT",
    "LIVED_EXPERIENCE",
    "CORRECTION",
    "COUNTEREXAMPLE",
    "LANGUAGE",
    "RESEARCH",
    "EXPERTISE",
    "MISUNDERSTANDING",
    "OUTCOME_EVIDENCE",
]
ConsentScope = Literal["PRIVATE_OWNER", "DEIDENTIFIED_RESEARCH"]
Sensitivity = Literal["LOW", "PRIVATE", "SENSITIVE"]
ReviewAction = Literal[
    "EDIT",
    "APPROVE",
    "REJECT",
    "START_CANARY",
    "ACTIVATE",
    "ROLLBACK",
    "WITHDRAW_CONSENT",
]


class TeachNURSourceRef(BaseModel):
    kind: Literal["OWNER_REFERENCE", "URL", "DOI", "MEMORY", "OUTCOME", "RESEARCH_NOTE"]
    reference: str = Field(min_length=1, max_length=2048)

    @field_validator("reference")
    @classmethod
    def _reference_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("source reference cannot be blank.")
        return value


class TeachNURContributionCreate(BaseModel):
    contribution_kind: ContributionKind
    content: str = Field(min_length=1, max_length=12000)
    orbit_id: uuid.UUID | None = None
    language_tag: str = Field(default="und", min_length=2, max_length=35)
    consent_scope: ConsentScope = "PRIVATE_OWNER"
    consent_granted: bool
    consent_policy_version: Literal["teach-nur-v1"] = "teach-nur-v1"
    sensitivity: Sensitivity | None = None
    confidence: float = Field(default=1.0, ge=0, le=1)
    source_refs: list[TeachNURSourceRef] = Field(default_factory=list, max_length=20)

    @field_validator("content", "language_tag")
    @classmethod
    def _text_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value cannot be blank.")
        return value


class TeachNURReviewIn(BaseModel):
    action: ReviewAction
    edited_text: str | None = Field(default=None, min_length=1, max_length=12000)
    review_note: str | None = Field(default=None, max_length=1000)

    @field_validator("edited_text", "review_note")
    @classmethod
    def _optional_text_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("provided review text cannot be blank.")
        return value

    @model_validator(mode="after")
    def _edit_requires_text(self) -> "TeachNURReviewIn":
        if self.action == "EDIT" and self.edited_text is None:
            raise ValueError("EDIT requires edited_text.")
        if self.action != "EDIT" and self.edited_text is not None:
            raise ValueError("edited_text is accepted only for EDIT.")
        return self


class TeachNURCandidateOut(BaseModel):
    id: uuid.UUID
    contribution_id: uuid.UUID
    candidate_text: str
    original_text_digest: str
    deidentified_text: str | None
    provenance_label: str
    sensitivity: str
    confidence: float
    source_refs: list
    risk_flags: list[str]
    contradiction_refs: list
    disagreement_map: dict
    status: str
    current_knowledge_version_id: uuid.UUID | None
    created_at: dt.datetime
    updated_at: dt.datetime
    model_config = {"from_attributes": True}


class TeachNURReviewOut(BaseModel):
    id: uuid.UUID
    action: str
    prior_status: str
    resulting_status: str
    created_at: dt.datetime
    model_config = {"from_attributes": True}


class TeachNUREvaluationOut(BaseModel):
    id: uuid.UUID
    knowledge_version_id: uuid.UUID | None
    suite_version: str
    checks: dict
    passed: bool
    created_at: dt.datetime
    model_config = {"from_attributes": True}


class TeachNURKnowledgeVersionOut(BaseModel):
    id: uuid.UUID
    candidate_id: uuid.UUID
    version: int
    parent_version_id: uuid.UUID | None
    canonical_text: str
    retrieval_scope: str
    provenance_label: str
    verification_status: str
    status: str
    evaluation_result: dict
    why_changed: str
    activated_at: dt.datetime | None
    rolled_back_at: dt.datetime | None
    created_at: dt.datetime
    model_config = {"from_attributes": True}


class TeachNURContributionOut(BaseModel):
    id: uuid.UUID
    orbit_id: uuid.UUID | None
    contribution_kind: str
    content: str
    language_tag: str
    consent_scope: str
    consent_policy_version: str
    consent_granted: bool
    provenance_label: str
    sensitivity: str
    confidence: float
    source_refs: list
    risk_flags: list[str]
    deidentification_status: str
    verification_status: str
    status: str
    reviewed_at: dt.datetime | None
    created_at: dt.datetime
    updated_at: dt.datetime
    model_config = {"from_attributes": True}


class TeachNURContributionDetail(TeachNURContributionOut):
    candidate: TeachNURCandidateOut
    reviews: list[TeachNURReviewOut] = Field(default_factory=list)
    knowledge_versions: list[TeachNURKnowledgeVersionOut] = Field(default_factory=list)
    evaluations: list[TeachNUREvaluationOut] = Field(default_factory=list)
    model_training_status: Literal["NOT_AUTHORIZED"] = "NOT_AUTHORIZED"
    institutional_promotion_status: Literal["OWNER_SCOPED_ONLY"] = "OWNER_SCOPED_ONLY"
