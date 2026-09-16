import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.age import is_adult
from app.common.enums import UserStatus
from app.common.security import decode_token
from app.db import get_session
from app.modules.identity.models import User

_bearer = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    session: AsyncSession = Depends(get_session),
) -> User:
    try:
        user_id: uuid.UUID = decode_token(credentials.credentials, "access")
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or expired token",
        )

    user = await session.get(User, user_id)
    ensure_active(user)
    return user


def ensure_active(user: User | None) -> None:
    """Tokens are stateless, so an account's status is what revokes them.

    A deleted account behaves as if it never existed; a suspended or banned one
    is told so.
    """
    if user is None or user.status == UserStatus.DELETED:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found"
        )
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="this account is not active"
        )


async def require_adult(current: User = Depends(get_current_user)) -> User:
    """Gate for anything that puts a member in front of other members."""
    if not is_adult(current.date_of_birth):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="date of birth required"
        )
    return current


async def get_current_admin(current: User = Depends(get_current_user)) -> User:
    if not current.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin access required")
    return current
