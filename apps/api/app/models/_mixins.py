import datetime as dt
import uuid

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def uuid_pk() -> Mapped[uuid.UUID]:
    # default=uuid4 (client-side) means INSERTs never need RETURNING, so rows can
    # be written under RLS policies that grant INSERT without SELECT visibility
    # (audit_events stays append-only and unreadable to the app role).
    # server_default remains as a safety net for non-ORM writers.
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                         server_default=text("gen_random_uuid()"))


def created_at_col() -> Mapped[dt.datetime]:
    return mapped_column(server_default=func.now(), nullable=False)


def updated_at_col() -> Mapped[dt.datetime]:
    return mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)
