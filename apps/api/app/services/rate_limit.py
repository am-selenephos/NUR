"""Fixed-window rate limiting backed by Redis (Phase 0 skeleton).

Buckets: login (per ip+email fingerprint) and registration (per ip — the
abuse mode is mass account creation from one address).
Development fails OPEN (with a warning) so a stopped Redis doesn't brick local
auth; any non-development environment fails CLOSED (429) on limiter errors.
"""
import logging

from redis.asyncio import Redis

from app.core.config import get_settings
from app.core.logging import log

logger = logging.getLogger("nur.rate_limit")


async def _fixed_window(redis: Redis, *, key: str, max_n: int, window_s: int) -> bool:
    s = get_settings()
    try:
        n = await redis.incr(key)
        if n == 1:
            await redis.expire(key, window_s)
        allowed = n <= max_n
        if not allowed:
            log(logger, "rate limit exceeded", key=key, count=n)
        return allowed
    except Exception:
        if s.app_env == "development":
            log(logger, "rate limiter unavailable — failing OPEN (development only)")
            return True
        log(logger, "rate limiter unavailable — failing CLOSED")
        return False


async def allow_login(redis: Redis, *, ip: str, email_fp: str) -> bool:
    s = get_settings()
    return await _fixed_window(redis, key=f"rl:login:{ip}:{email_fp}",
                               max_n=s.login_rate_limit_max,
                               window_s=s.login_rate_limit_window_seconds)


async def allow_registration(redis: Redis, *, ip: str) -> bool:
    s = get_settings()
    return await _fixed_window(redis, key=f"rl:register:{ip}",
                               max_n=s.register_rate_limit_max,
                               window_s=s.register_rate_limit_window_seconds)
