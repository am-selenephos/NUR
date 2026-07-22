import datetime as dt
import uuid
from typing import Literal

from pydantic import BaseModel, Field, field_validator


EvaluationSuite = Literal[
    "GROUNDING",
    "INJECTION_AND_TOOLS",
    "PERSONA_AND_SAFETY",
    "LANGUAGE_CONTRACT",
    "TEACH_NUR_GOVERNANCE",
    "OMEGA_CONSISTENCY",
]


class ProviderLastRun(BaseModel):
    id: uuid.UUID
    provider: str
    model: str | None
    status: str
    error_code: str | None
    created_at: dt.datetime


class IntelligenceProviderStatus(BaseModel):
    provider: str
    configuration_status: Literal["DISABLED", "CONFIGURED"]
    configured: bool
    model: str | None
    credential_state: Literal["NOT_CONFIGURED", "PRESENT_SERVER_SIDE"]
    credential_exposed_to_client: Literal[False] = False
    semantic_streaming: bool
    structured_output_schema: Literal["nur_talk_output"] = "nur_talk_output"
    external_web_research: bool
    network_probe_performed: Literal[False] = False
    live_probe_status: Literal["NOT_RUN", "OWNER_RUN_RECORDED"]
    release_proof: Literal["FOUNDER_KEY_REQUIRED", "EXTERNAL_GATE_REQUIRED"]
    last_owner_run: ProviderLastRun | None = None


class IntelligenceEvaluationRequest(BaseModel):
    suites: list[EvaluationSuite] = Field(default_factory=list, max_length=6)

    @field_validator("suites")
    @classmethod
    def _unique_suites(cls, value: list[str]) -> list[str]:
        if len(set(value)) != len(value):
            raise ValueError("evaluation suites must be unique.")
        return value


class IntelligenceCaseResult(BaseModel):
    id: str
    passed: bool
    expected: str
    actual: str
    critical: bool = True


class IntelligenceSuiteResult(BaseModel):
    name: str
    case_count: int
    passed: int
    failed: int
    cases: list[IntelligenceCaseResult]


class IntelligenceEvaluationResult(BaseModel):
    id: uuid.UUID
    created_at: dt.datetime
    suite_version: str
    execution_mode: Literal["DETERMINISTIC_OFFLINE"]
    live_provider_exercised: Literal[False]
    verdict: Literal["PASS", "BLOCK"]
    case_count: int
    critical_failures: list[str]
    suites: list[IntelligenceSuiteResult]
