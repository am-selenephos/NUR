import re

FORBIDDEN_PROPOSAL_TARGETS = {
    "rls",
    "row level security",
    "auth",
    "authentication",
    "session",
    "secret",
    "api key",
    "recipient grant",
    "grant law",
    "external autonomous",
    "autonomous action",
}

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*\S+"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._-]{12,}"),
]


def redact_secrets(text: str, *, max_len: int = 900) -> tuple[str, bool]:
    redacted = text or ""
    found = False
    for pattern in SECRET_PATTERNS:
        redacted, count = pattern.subn("[secret-redacted]", redacted)
        found = found or count > 0
    redacted = " ".join(redacted.split())
    if len(redacted) > max_len:
        redacted = redacted[: max_len - 1].rstrip() + "..."
    return redacted, found


def sensitivity_for_summary(summary: str, requested: str | None = None) -> str:
    if requested == "SECRET_EXCLUDED":
        return requested
    _, found = redact_secrets(summary)
    if found:
        return "SECRET_EXCLUDED"
    if requested in {"LOW", "PRIVATE", "SENSITIVE"}:
        return requested
    lowered = summary.lower()
    if any(word in lowered for word in ("medical", "password", "private key", "trauma", "religious", "relationship")):
        return "SENSITIVE"
    return "PRIVATE"


def allowed_truth_status_for_provenance(provenance_label: str, requested: str) -> str:
    if requested == "OBSERVED" and provenance_label not in {"OWNER_WRITTEN", "OBSERVED_OUTCOME", "SYSTEM_MEASURED"}:
        return "HYPOTHESIS"
    if requested not in {"OBSERVED", "INFERRED", "HYPOTHESIS", "CONTRADICTED", "SUPERSEDED", "RETIRED"}:
        return "HYPOTHESIS"
    return requested


def proposal_risk(description: str, proposal_kind: str) -> str:
    lowered = f"{proposal_kind} {description}".lower()
    if any(target in lowered for target in FORBIDDEN_PROPOSAL_TARGETS):
        return "FORBIDDEN"
    if "prompt" in lowered or "memory policy" in lowered:
        return "MEDIUM"
    return "LOW"


def ensure_proposal_allowed(description: str, proposal_kind: str) -> None:
    if proposal_risk(description, proposal_kind) == "FORBIDDEN":
        raise PermissionError("Omega learning proposals cannot target RLS, auth, secrets, recipient grants, or autonomous external actions.")
