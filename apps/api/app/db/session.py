from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

_engine = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(get_settings().database_url, pool_pre_ping=True)
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _sessionmaker


async def dispose_engine() -> None:
    """Close the database connection pool for a graceful shutdown.

    The engine is a process-level singleton; disposing it drains and closes every
    pooled connection so the process exits without leaving connections dangling
    on the server. Idempotent: a no-op if no engine was ever created.
    """
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _sessionmaker = None
