from fastapi import Request
from jose import jwt
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config.settings import get_settings


def _get_rate_limit_key(request: Request) -> str:
    """
    Use JWT sub (userId) as rate limit key for per-user limiting.
    Falls back to client IP if no valid Bearer token is present.

    Note: JWT is decoded WITHOUT signature verification here — this is intentional.
    The purpose is only to extract the userId as a rate limit bucket key.
    Actual authentication/authorization is enforced separately by get_current_user().
    """
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        try:
            payload = jwt.get_unverified_claims(token)
            user_id = payload.get("sub")
            if user_id:
                return str(user_id)
        except Exception:
            pass
    return get_remote_address(request)


def _build_redis_uri() -> str:
    settings = get_settings()
    if settings.redis_password:
        return f"redis://:{settings.redis_password}@{settings.redis_host}:{settings.redis_port}/1"
    return f"redis://{settings.redis_host}:{settings.redis_port}/1"


def _build_limiter() -> Limiter:
    """Try Redis storage for rate limiting; fall back to in-memory if unavailable."""
    import logging
    import redis as _redis

    logger = logging.getLogger(__name__)
    uri = _build_redis_uri()
    try:
        # Quick connectivity check before wiring slowapi to Redis
        settings = get_settings()
        r = _redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password or None,
            socket_connect_timeout=1,
        )
        r.ping()
        r.close()
        logger.info("[Limiter] Using Redis storage for rate limiting: %s", uri)
        return Limiter(key_func=_get_rate_limit_key, storage_uri=uri)
    except Exception as e:
        logger.warning(
            "[Limiter] Redis unavailable (%s). Falling back to in-memory rate limiting.",
            e,
        )
        return Limiter(key_func=_get_rate_limit_key, storage_uri="memory://")


limiter = _build_limiter()
