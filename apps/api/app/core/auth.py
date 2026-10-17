from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_db
from app.models.entities import BrandMember, MemberRole

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

_jwks_cache: dict | None = None


async def get_supabase_jwks() -> dict:
    """Fetch Supabase's JWKS for ES256 token verification."""
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache

    settings = get_settings()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.supabase_url}/auth/v1/.well-known/jwks.json", timeout=5
        )
        response.raise_for_status()
        _jwks_cache = response.json()
        return _jwks_cache


@dataclass
class AuthUser:
    id: uuid.UUID
    email: str | None = None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> AuthUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    settings = get_settings()
    token = credentials.credentials

    unverified = jwt.get_unverified_header(token)
    token_alg = unverified.get("alg")

    # Try ES256 (Supabase production tokens) first
    if token_alg == "ES256":
        try:
            jwks = await get_supabase_jwks()
            kid = unverified.get("kid")

            if not kid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token missing kid",
                )
            else:
                for jwk_data in jwks.get("keys", []):
                    if jwk_data.get("kid") == kid:
                        try:
                            payload = jwt.decode(
                                token,
                                jwk_data,
                                algorithms=["ES256"],
                                audience="authenticated",
                            )
                            sub = payload.get("sub")
                            if not sub:
                                raise HTTPException(
                                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
                                )
                            return AuthUser(id=uuid.UUID(sub), email=payload.get("email"))
                        except JWTError as e:
                            logger.error(f"ES256 token decode failed: {e}")
                            raise HTTPException(
                                status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid or expired token",
                            ) from e
                logger.error(f"No matching key found for kid={kid} in JWKS")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token key",
                )
        except HTTPException:
            raise
        except (ValueError, httpx.HTTPError, KeyError) as e:
            logger.error(f"ES256 setup failed: {type(e).__name__}: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token verification failed",
            ) from e

    # Fall back to HS256 (local test tokens)
    if token_alg == "HS256":
        try:
            payload = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
            sub = payload.get("sub")
            if not sub:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
            return AuthUser(id=uuid.UUID(sub), email=payload.get("email"))
        except JWTError as e:
            logger.error(f"HS256 verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
            ) from e
        except ValueError as e:
            logger.error(f"HS256 parsing failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
            ) from e

    logger.error(f"Unsupported token algorithm: {token_alg}")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unsupported token algorithm",
    )


async def get_membership(
    brand_id: uuid.UUID,
    user: AuthUser,
    db: AsyncSession,
) -> BrandMember:
    result = await db.execute(
        select(BrandMember).where(
            BrandMember.brand_id == brand_id,
            BrandMember.user_id == user.id,
        )
    )
    membership = result.scalar_one_or_none()
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a brand member")
    return membership


def require_admin(membership: BrandMember) -> None:
    if membership.role not in (MemberRole.owner, MemberRole.admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or owner role required",
        )


async def verify_internal_secret(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> None:
    settings = get_settings()
    if credentials is None or credentials.credentials != settings.internal_job_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid job secret")
