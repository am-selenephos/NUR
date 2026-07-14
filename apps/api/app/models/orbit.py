import datetime as dt
import uuid

from sqlalchemy import ForeignKey, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import ENUM as PGEnum, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.db.base import Base
from app.models._mixins import uuid_pk, now_utc


class Orbit(Base):
    __tablename__ = "orbits"

    id = uuid_pk()
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False, default="Personal Orbit")
    kind: Mapped[str] = mapped_column(PGEnum(
        'PROJECT', 'CREATIVE', 'RESEARCH', 'CARE', 'PERSONAL_BRIDGE',
        'PERSON', 'GROUP', 'COUNCIL', 'COMMUNITY', 'SYSTEM',
        name="orbit_kind", create_type=False,
    ), nullable=False, default="PERSONAL_BRIDGE")
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(PGEnum('ACTIVE', 'ARCHIVED', name="orbit_status", create_type=False), nullable=False, default="ACTIVE")
    current_arrival_state: Mapped[str | None] = mapped_column(String(32), nullable=True)
    active_focus_area: Mapped[str | None] = mapped_column(String(64), nullable=True)
    primary_person_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("people.id", ondelete="SET NULL")
    )
    system_slug: Mapped[str | None] = mapped_column(String(48))
    privacy_scope: Mapped[str] = mapped_column(
        String(32), default="PRIVATE_ORBIT", server_default="PRIVATE_ORBIT", nullable=False
    )
    orbit_metadata: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False
    )
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), default=now_utc, nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), default=now_utc, nullable=False)
