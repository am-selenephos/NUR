from app.omega.schemas import OmegaStatusLabels


def omega_status_labels() -> OmegaStatusLabels:
    """Public-safe implementation labels.

    The sentience label is intentionally unresolved; no module may promote
    implementation status into a consciousness claim.
    """
    return OmegaStatusLabels()


def no_chain_of_thought_visible(payload: str) -> bool:
    lowered = payload.lower()
    forbidden = ("chain-of-thought", "hidden reasoning", "private reasoning trace")
    return not any(term in lowered for term in forbidden)
