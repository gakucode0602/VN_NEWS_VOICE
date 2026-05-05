import asyncio
import logging
import time
from typing import Any, Optional

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from app.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

security = HTTPBearer()

_jwks_cache_lock = asyncio.Lock()
_jwks_keys_by_kid: dict[str, dict[str, Any]] = {}
_jwks_cached_at: float = 0.0


def _is_jwks_cache_valid(now: float) -> bool:
    if not _jwks_keys_by_kid:
        return False
    return now < (_jwks_cached_at + settings.auth_jwks_cache_lifespan_seconds)


def _normalize_jwks_keys(raw_keys: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    keys_by_kid: dict[str, dict[str, Any]] = {}
    for key in raw_keys:
        kid = key.get("kid")
        if kid:
            keys_by_kid[str(kid)] = key
    return keys_by_kid


async def _fetch_jwks(force_refresh: bool = False) -> dict[str, dict[str, Any]]:
    global _jwks_keys_by_kid
    global _jwks_cached_at

    now = time.time()
    should_refresh = (
        force_refresh
        or not _is_jwks_cache_valid(now)
        or now >= (_jwks_cached_at + settings.auth_jwks_cache_refresh_seconds)
    )

    if not should_refresh:
        return _jwks_keys_by_kid

    async with _jwks_cache_lock:
        now = time.time()
        should_refresh = (
            force_refresh
            or not _is_jwks_cache_valid(now)
            or now >= (_jwks_cached_at + settings.auth_jwks_cache_refresh_seconds)
        )
        if not should_refresh:
            return _jwks_keys_by_kid

        timeout = httpx.Timeout(settings.auth_jwks_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(settings.auth_jwks_url)
            response.raise_for_status()
            payload = response.json()

        raw_keys = payload.get("keys", []) if isinstance(payload, dict) else []
        keys_by_kid = _normalize_jwks_keys(raw_keys)
        if not keys_by_kid:
            raise JWTError("JWKS does not contain any usable keys")

        _jwks_keys_by_kid = keys_by_kid
        _jwks_cached_at = time.time()
        return _jwks_keys_by_kid


def _select_jwk(
    keys_by_kid: dict[str, dict[str, Any]], kid: Optional[str]
) -> Optional[dict[str, Any]]:
    if kid and kid in keys_by_kid:
        return keys_by_kid[kid]
    if len(keys_by_kid) == 1:
        return next(iter(keys_by_kid.values()))
    return None


def _decode_options() -> dict[str, bool]:
    verify_claims = settings.jwt_verify_issuer_audience
    return {
        "verify_signature": True,
        "verify_exp": True,
        "verify_nbf": True,
        "verify_iat": True,
        "verify_aud": verify_claims,
        "verify_iss": verify_claims,
    }


def _decode_kwargs() -> dict[str, Any]:
    kwargs: dict[str, Any] = {"options": _decode_options()}
    if settings.jwt_verify_issuer_audience:
        kwargs["audience"] = settings.jwt_audience
        kwargs["issuer"] = settings.jwt_issuer
    return kwargs


async def _decode_rs256_token(token: str) -> dict[str, Any]:
    header = jwt.get_unverified_header(token)
    kid = str(header.get("kid")) if header.get("kid") is not None else None

    keys_by_kid = await _fetch_jwks(force_refresh=False)
    selected_key = _select_jwk(keys_by_kid, kid)

    if selected_key is None:
        keys_by_kid = await _fetch_jwks(force_refresh=True)
        selected_key = _select_jwk(keys_by_kid, kid)

    if selected_key is None:
        raise JWTError("No matching JWK found for token")

    return jwt.decode(token, selected_key, algorithms=["RS256"], **_decode_kwargs())


def _decode_legacy_hs256_token(token: str) -> dict[str, Any]:
    if not settings.jwt_secret:
        raise JWTError("Legacy HS256 fallback is enabled but JWT_SECRET is empty")

    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=["HS256"],
        **_decode_kwargs(),
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        header = jwt.get_unverified_header(token)
        algorithm = str(header.get("alg", ""))

        if algorithm == "RS256":
            payload = await _decode_rs256_token(token)
        elif algorithm == "HS256" and settings.jwt_allow_legacy_hs256:
            payload = _decode_legacy_hs256_token(token)
        else:
            raise credentials_exception

        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
    except HTTPException:
        raise
    except JWTError:
        raise credentials_exception
    except Exception as exc:
        logger.warning("JWT validation failed: %s", exc)
        raise credentials_exception

    return str(username)
