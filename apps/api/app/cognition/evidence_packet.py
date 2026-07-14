import uuid

from app.ai.schemas import EvidenceRef
from app.cognition.schemas import EvidencePacket


def build_evidence_packet(*, orbit_id: uuid.UUID | None, retrieval: list[EvidenceRef]) -> EvidencePacket:
    return EvidencePacket(orbit_id=orbit_id, retrieval=retrieval, withheld=[])
