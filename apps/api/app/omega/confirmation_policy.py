"""Confirmation gates for Omega v1 claim extraction.

The rule is intentionally conservative: model-shaped or sensitive inferred
claims wait for the owner. This prevents the research layer from quietly
turning guesses about health, identity, beliefs, relationships, or private
state into stored facts.
"""
from app.models import OmegaExperience

SENSITIVE_HINTS = {
    "health",
    "medical",
    "diagnosis",
    "medicine",
    "therapy",
    "trauma",
    "religious",
    "allah",
    "god",
    "faith",
    "identity",
    "relationship",
    "family",
    "body",
    "money",
    "debt",
    "failure",
    "secret",
    "sensitive",
    "api key",
    "password",
    "token",
    "private key",
}


def confirmation_reason(experience: OmegaExperience, *, claim_text: str, truth_status: str) -> str | None:
    lowered = f"{experience.summary} {claim_text}".lower()
    if experience.sensitivity in {"SENSITIVE", "SECRET_EXCLUDED"}:
        return f"experience sensitivity is {experience.sensitivity.lower()}"
    if truth_status == "INFERRED":
        return "semantic claim is inferred, not directly observed"
    if experience.provenance_label == "MODEL_GENERATED":
        return "model-generated content cannot become owner memory silently"
    for hint in SENSITIVE_HINTS:
        if hint in lowered:
            return f"sensitive inferred domain: {hint}"
    return None


def requires_confirmation(experience: OmegaExperience, *, claim_text: str, truth_status: str) -> bool:
    return confirmation_reason(experience, claim_text=claim_text, truth_status=truth_status) is not None
