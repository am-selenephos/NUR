"""Idempotent development seed. Refuses to run outside development."""
import asyncio
import secrets

from sqlalchemy import select

from app.core.config import get_settings
from app.db.rls import set_auth_context
from app.db.session import get_sessionmaker
from app.models import User
from app.services import auth_service


async def main() -> None:
    s = get_settings()
    if s.app_env != "development":
        raise SystemExit("Seed refuses to run outside APP_ENV=development.")
    email = "demo@nur.local"
    async with get_sessionmaker()() as db:
        async with db.begin():
            await set_auth_context(db)
            exists = (await db.execute(select(User.id).where(User.email == email))).scalar_one_or_none()
        if exists:
            print(f"seed: {email} already present — nothing to do")
            return
        password = secrets.token_urlsafe(12)
        await auth_service.register(db, chosen_name="Demo", email=email, password=password, consent=True)
        print(f"seed: created {email} with one-time password: {password}")


if __name__ == "__main__":
    asyncio.run(main())
