import logging
import secrets
import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.core.auth_google import (
    GOOGLE_NAMESPACE,
    exchange_code_for_token,
    get_google_auth_url,
    get_google_user_info,
)
from app.schemas.api import GoogleCallbackResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/google/login")
async def google_login() -> dict[str, str]:
    """Generate and return Google OAuth login URL."""
    state = secrets.token_urlsafe(32)
    auth_url = await get_google_auth_url(state)
    return {"auth_url": auth_url, "state": state}


@router.get("/google/callback")
async def google_callback(
    code: str = Query(...),
    state: str = Query(...),
) -> GoogleCallbackResponse:
    """Handle Google OAuth callback and return user info."""
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing authorization code",
        )

    try:
        token_data = await exchange_code_for_token(code)
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No access token in response",
            )

        user_info = await get_google_user_info(access_token)
        google_id = user_info.get("id")
        email = user_info.get("email")
        name = user_info.get("name")

        if not google_id or not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing required user info from Google",
            )

        user_uuid = uuid.uuid5(GOOGLE_NAMESPACE, google_id)

        return GoogleCallbackResponse(
            user_id=str(user_uuid),
            email=email,
            name=name,
            access_token=access_token,
            message="User authenticated. Use this data to create/update user in your system.",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Google callback error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth callback failed",
        ) from e
