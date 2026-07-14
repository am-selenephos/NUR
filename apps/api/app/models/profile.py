import datetime as dt
import uuid

from sqlalchemy import ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Boolean, DateTime

from app.db.base import Base
from app.models._mixins import now_utc


class Profile(Base):
    __tablename__ = "profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    chosen_name: Mapped[str] = mapped_column(String(120), nullable=False)
    timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    locale: Mapped[str | None] = mapped_column(String(16), nullable=True)
    writing_preference: Mapped[str] = mapped_column(String(32), nullable=False, server_default="default", default="default")
    sound_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"), default=False)
    reduced_effects: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"), default=False)
    default_boundary: Mapped[str] = mapped_column(String(32), nullable=False, server_default="PRIVATE_ORBIT", default="PRIVATE_ORBIT")
    active_orbit_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("orbits.id", ondelete="SET NULL"), nullable=True)
    omega_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"), default=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), default=now_utc, nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), default=now_utc, nullable=False)
