import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import csrf_matches, csrf_token_for
from app.db.session import get_sessionmaker
from app.db.rls import set_user_context
from app.services import auth_service


async def get_db() -> AsyncSession:
    async with get_sessionmaker()() as session:
        yield session


DB = Annotated[AsyncSession, Depends(get_db)]


async def get_current_identity(request: Request, db: DB) -> tuple[uuid.UUID, uuid.UUID]:
    """(user_id, session_id) from the HTTP-only session cookie, else 401."""
    s = get_settings()
    resolved = await auth_service.resolve_session(db, request.cookies.get(s.session_cookie_name))
    if not resolved:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    return resolved


Identity = Annotated[tuple[uuid.UUID, uuid.UUID], Depends(get_current_identity)]


async def require_csrf(request: Request, identity: Identity) -> None:
    """Signed double-submit: the X-CSRF-Token header must equal
    HMAC(CSRF_SECRET, session_id) for the *resolved* session. A stolen or fabricated
    token from any other session cannot pass, and CSRF_SECRET rotation invalidates
    all outstanding tokens at once."""
    _, session_id = identity
    if not csrf_matches(request.headers.get("x-csrf-token"), csrf_token_for(session_id)):
        raise HTTPException(status_code=403, detail="CSRF token missing or invalid.")


async def get_scoped_db(db: DB, identity: Identity) -> AsyncSession:
    """Session with app.current_user_id armed for the CURRENT transaction.
    resolve_session commits (session bookkeeping), which drops the
    transaction-local GUC — every data route must re-arm before touching
    RLS-guarded tables."""
    await set_user_context(db, identity[0])
    return db


Scoped = Annotated[AsyncSession, Depends(get_scoped_db)]
