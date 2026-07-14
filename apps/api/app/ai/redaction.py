import re

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"Authorization:\s*Bearer\s+\S+", re.IGNORECASE),
    re.compile(r"OPENAI_API_KEY\s*=\s*\S+", re.IGNORECASE),
    re.compile(r"(?i)\b(api[_-]?key|secret|token|password)\b\s*[:=]\s*['\"]?[^'\"\s,;]{8,}"),
    re.compile(r"(?i)\b(bearer|basic)\s+[A-Za-z0-9._~+/=-]{16,}"),
]


def redact_for_audit(value: str | None) -> str | None:
    if value is None:
        return None
    redacted = value
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED_SECRET]", redacted)
    return redacted


def redact_for_model(value: str | None) -> str:
    """Scrub retrieved excerpts before they enter prompts, ledgers, or proof."""
    return redact_for_audit(value or "") or ""
