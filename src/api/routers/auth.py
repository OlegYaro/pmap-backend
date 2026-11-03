from fastapi import APIRouter, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.auth import LoginRequest, RefreshRequest, TokenResponse
from database.models import User
from database.session import DbSession
from services.auth import (
    ACCESS_TTL,
    authenticate,
    create_access_token,
    issue_refresh_token,
    revoke_refresh_token,
    use_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(data: LoginRequest, session: DbSession) -> TokenResponse:
    """Exchange login and password for an access and a refresh token."""
    user = await authenticate(session, data.login, data.password)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid login or password")
    return _tokens(session, user)


@router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh(data: RefreshRequest, session: DbSession) -> TokenResponse:
    """Exchange a refresh token for a new pair; the old refresh token stops working."""
    user = await use_refresh_token(session, data.refresh_token)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")
    return _tokens(session, user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(data: RefreshRequest, session: DbSession) -> None:
    """Revoke a refresh token; the access token expires on its own."""
    await revoke_refresh_token(session, data.refresh_token)


def _tokens(session: AsyncSession, user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user),
        refresh_token=issue_refresh_token(session, user),
        expires_in=int(ACCESS_TTL.total_seconds()),
    )
