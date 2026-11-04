from typing import Annotated

from fastapi import Header, HTTPException, status


async def require_admin(x_actor_role: Annotated[str | None, Header()] = None) -> None:
    """The API Gateway sets X-Actor-Role from the checked token; only admins pass."""
    if x_actor_role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin role required")
