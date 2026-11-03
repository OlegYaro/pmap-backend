import datetime as dt
import hashlib
import secrets

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core import settings
from database.models import RefreshToken, User

ACCESS_TTL = dt.timedelta(hours=1)
REFRESH_TTL = dt.timedelta(days=30)

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerificationError:
        return False


def create_access_token(user: User) -> str:
    now = dt.datetime.now(dt.UTC)
    claims = {
        "sub": str(user.id),
        "role": user.role,
        "iat": now,
        "exp": now + ACCESS_TTL,
    }
    return jwt.encode(claims, settings.JWT_SECRET.get_secret_value(), algorithm="HS256")


def issue_refresh_token(session: AsyncSession, user: User) -> str:
    """A new random refresh token; only its hash is stored."""
    token = secrets.token_urlsafe(32)
    session.add(
        RefreshToken(
            user_id=user.id,
            token_hash=_hash_token(token),
            expires_at=dt.datetime.now(dt.UTC) + REFRESH_TTL,
        )
    )
    return token


async def authenticate(session: AsyncSession, login: str, password: str) -> User | None:
    """The active user with this login and password, or None."""
    user = await session.scalar(select(User).where(User.login == login))
    if user is None or not user.is_active or not verify_password(user.password_hash, password):
        return None
    return user


async def use_refresh_token(session: AsyncSession, token: str) -> User | None:
    """Revoke a valid refresh token and return its active user, or None.

    Each refresh token works once: the caller issues a new one in its place.
    """
    stored = await _find_refresh_token(session, token)
    now = dt.datetime.now(dt.UTC)
    if stored is None or stored.revoked_at is not None or stored.expires_at <= now:
        return None
    stored.revoked_at = now
    user = await session.get(User, stored.user_id)
    if user is None or not user.is_active:
        return None
    return user


async def revoke_refresh_token(session: AsyncSession, token: str) -> None:
    stored = await _find_refresh_token(session, token)
    if stored is not None and stored.revoked_at is None:
        stored.revoked_at = dt.datetime.now(dt.UTC)


async def _find_refresh_token(session: AsyncSession, token: str) -> RefreshToken | None:
    # FOR UPDATE: two parallel requests with the same token cannot both use it.
    query = select(RefreshToken).where(RefreshToken.token_hash == _hash_token(token))
    return await session.scalar(query.with_for_update())


def _hash_token(token: str) -> str:
    # The token is 32 random bytes, so a fast hash is enough, and it can be looked up.
    return hashlib.sha256(token.encode()).hexdigest()
