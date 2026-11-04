from typing import Annotated

from fastapi import Header, HTTPException, status
from fastapi.security import HTTPBearer

# The API Gateway checks the token. This only marks the routes that need one in Swagger
# (the lock and the Authorize button); Backend itself does not check it.
bearer = HTTPBearer(auto_error=False)


async def require_admin(x_actor_role: Annotated[str | None, Header()] = None) -> None:
    """The API Gateway sets X-Actor-Role from the checked token; only admins pass."""
    if x_actor_role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin role required")
