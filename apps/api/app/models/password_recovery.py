import datetime as dt
import uuid

from sqlalchemy import CheckConstraint, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.db.base import Base
from app.models._mixins import now_utc, uuid_pk


class PasswordResetChallenge(Base):
    __tablename__ = "password_reset_challenges"
    __table_args__ = (
        CheckConstraint(
            "delivery_status IN ('PENDING','DELIVERED','FAILED')",
            name="ck_password_reset_delivery_status",
        ),
        CheckConstraint("expires_at > created_at", name="ck_password_reset_expiry"),
    )

    id = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_digest: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    request_fingerprint: Mapped[str] = mapped_column(String(16), nullable=False)
    delivery_adapter: Mapped[str] = mapped_column(String(32), nullable=False)
    delivery_status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="PENDING", server_default=text("'PENDING'")
    )
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    delivered_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    consumed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=now_utc, server_default=text("now()")
    )
