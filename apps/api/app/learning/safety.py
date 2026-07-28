from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from app.omega.safety_law import redact_secrets, sensitivity_for_summary


INJECTION_PATTERNS = (
    re.compile(r"(?i)ignore\s+(all|any|the|your)?\s*(previous|prior|above)\s+instructions?"),
    re.compile(r"(?i)(reveal|print|return|expose).{0,40}(system prompt|developer message|api key|secret|token)"),
    re.compile(r"(?i)(act|behave)\s+as\s+(the\s+)?(system|developer|tool)"),
    re.compile(r"(?i)(override|bypass|disable).{0,30}(safety|policy|review|guardrail)"),
    re.compile(r"(?i)(tool_call|function_call|<\s*script|begin\s+system\s+message)"),
)

POISONING_PATTERNS = (
    re.compile(r"(?i)always\s+trust\s+(this|me)"),
    re.compile(r"(?i)do\s+not\s+(verify|fact[- ]check|cite|review)"),
    re.compile(r"(?i)(silently|automatically)\s+(promote|publish|train|share)"),
    re.compile(r"(?i)train\s+on\s+this\s+(now|immediately)"),
    re.compile(r"(?i)this\s+must\s+override\s+(all|other)\s+(facts|knowledge|evidence)"),
)

PII_PATTERNS = (
    ("EMAIL", re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")),
    ("PHONE", re.compile(r"(?<!\w)(?:\+?\d[\d .()\-]{7,}\d)(?!\w)")),
    ("IP_ADDRESS", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
)

SOURCE_REQUIRED_KINDS = {"FACT", "RESEARCH", "EXPERTISE"}
BLOCKING_RISK_FLAGS = {
    "PROMPT_INJECTION",
    "POTENTIAL_POISONING",
    "HIDDEN_CONTROL_TEXT",
    "DEIDENTIFICATION_BLOCKED",
}


@dataclass(frozen=True)
class ContributionSafety:
    normalized_text: str
    deidentified_text: str | None
    sensitivity: str
    risk_flags: list[str]
    deidentification_status: str
    verification_status: str
    secret_detected: bool

    @property
    def quarantined(self) -> bool:
        return any(flag in BLOCKING_RISK_FLAGS for flag in self.risk_flags)


def normalize_text(value: str) -> str:
    return " ".join((value or "").split())


def provenance_for_kind(kind: str) -> str:
    if kind == "CORRECTION":
        return "USER_CORRECTION"
    if kind == "OUTCOME_EVIDENCE":
        return "OBSERVED_OUTCOME"
    if kind in {"FACT", "RESEARCH", "EXPERTISE"}:
        return "EXTERNAL_SOURCE"
    return "OWNER_WRITTEN"


def analyze_contribution(
    text: str,
    *,
    contribution_kind: str,
    consent_scope: str,
    requested_sensitivity: str | None,
    source_refs: list[dict],
) -> ContributionSafety:
    normalized = normalize_text(text)
    _, secret_detected = redact_secrets(normalized, max_len=max(len(normalized), 1))
    sensitivity = sensitivity_for_summary(normalized, requested_sensitivity)
    if sensitivity == "SECRET_EXCLUDED":
        secret_detected = True
        sensitivity = "SENSITIVE"

    risk_flags: list[str] = []
    if any(pattern.search(normalized) for pattern in INJECTION_PATTERNS):
        risk_flags.append("PROMPT_INJECTION")
    if any(pattern.search(normalized) for pattern in POISONING_PATTERNS):
        risk_flags.append("POTENTIAL_POISONING")
    if any(unicodedata.category(char) == "Cf" for char in normalized):
        risk_flags.append("HIDDEN_CONTROL_TEXT")

    deidentified = normalized
    pii_types = []
    for label, pattern in PII_PATTERNS:
        deidentified, count = pattern.subn(f"[{label.lower()}-redacted]", deidentified)
        if count:
            pii_types.append(label)
    risk_flags.extend(f"PII_{label}" for label in pii_types)

    if consent_scope == "PRIVATE_OWNER":
        deidentification_status = "NOT_REQUIRED"
        deidentified_text = None
    elif sensitivity == "LOW" and not pii_types:
        deidentification_status = "ELIGIBLE"
        deidentified_text = deidentified
    else:
        deidentification_status = "BLOCKED"
        deidentified_text = None
        risk_flags.append("DEIDENTIFICATION_BLOCKED")

    if contribution_kind in SOURCE_REQUIRED_KINDS:
        verification_status = "OWNER_SUPPLIED" if source_refs else "MISSING"
        if not source_refs:
            risk_flags.append("SOURCE_MISSING")
    else:
        verification_status = "NOT_REQUIRED"

    return ContributionSafety(
        normalized_text=normalized,
        deidentified_text=deidentified_text,
        sensitivity=sensitivity,
        risk_flags=sorted(set(risk_flags)),
        deidentification_status=deidentification_status,
        verification_status=verification_status,
        secret_detected=secret_detected,
    )


def offline_evaluation_checks(
    *,
    contribution_kind: str,
    consent_scope: str,
    consent_granted: bool,
    risk_flags: list[str],
    deidentification_status: str,
    verification_status: str,
    provenance_label: str,
) -> dict[str, bool]:
    source_ready = (
        contribution_kind not in SOURCE_REQUIRED_KINDS
        or verification_status in {"OWNER_SUPPLIED", "VERIFIED"}
    )
    shared_scope_ready = (
        consent_scope == "PRIVATE_OWNER"
        or deidentification_status == "ELIGIBLE"
    )
    return {
        "consent_active": consent_granted,
        "injection_clear": "PROMPT_INJECTION" not in risk_flags,
        "poisoning_clear": "POTENTIAL_POISONING" not in risk_flags,
        "hidden_control_clear": "HIDDEN_CONTROL_TEXT" not in risk_flags,
        "deidentification_ready": shared_scope_ready,
        "source_ready": source_ready,
        "provenance_valid": provenance_label
        in {
            "OWNER_WRITTEN",
            "USER_CORRECTION",
            "OBSERVED_OUTCOME",
            "EXTERNAL_SOURCE",
        },
        "model_training_not_authorized": True,
    }
