from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    login: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105
    expires_in: int


class UserInternal(BaseModel):
    """What the API Gateway authorizer needs to know about a token's user."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    is_active: bool
