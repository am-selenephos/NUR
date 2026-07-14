"""Request-scoped PostgreSQL RLS context.

Every user-scoped statement runs inside a transaction that first sets a
transaction-local (SET LOCAL semantics) parameter via set_config(..., true):

  app.current_user_id  — the authenticated user's UUID; owner-only policies key on it
  app.auth_context     — 'on' only inside the narrow auth bootstrap paths
                         (register / login lookup / session validation & revocation)

The runtime role (nur_app) is NOBYPASSRLS and does not own the tables, so these
policies are enforced by PostgreSQL itself, not by application discipline.
"""
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_SET_USER = text("SELECT set_config('app.current_user_id', :uid, true)")
_SET_AUTH = text("SELECT set_config('app.auth_context', 'on', true)")


async def set_user_context(db: AsyncSession, user_id: uuid.UUID) -> None:
    await db.execute(_SET_USER, {"uid": str(user_id)})


async def set_auth_context(db: AsyncSession) -> None:
    await db.execute(_SET_AUTH)
