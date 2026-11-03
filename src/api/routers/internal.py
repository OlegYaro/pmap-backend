from fastapi import APIRouter, HTTPException, status

from api.schemas.auth import UserInternal
from database.models import User
from database.session import DbSession

# Called only by the API Gateway authorizer; the gateway does not expose /internal.
router = APIRouter(prefix="/internal", tags=["internal"])


@router.get("/users/{user_id}", status_code=status.HTTP_200_OK)
async def get_user(user_id: int, session: DbSession) -> UserInternal:
    """Whether the user behind a token exists, is active, and its role."""
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return UserInternal.model_validate(user)
