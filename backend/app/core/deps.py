"""
Shared FastAPI dependencies: current-user resolution and role gating.

`get_current_user` decodes the bearer token, loads the user, and 401s on any
failure. `require_role` builds a dependency that additionally 403s unless the
user holds one of the allowed roles.
"""

from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import decode_access_token
from app.database import get_db
from app.db_models import User
from app.repositories import user_repo

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")

_CREDENTIALS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    username = decode_access_token(token)
    if username is None:
        raise _CREDENTIALS_EXC
    user = user_repo.get_by_username(db, username)
    if user is None or not user.is_active:
        raise _CREDENTIALS_EXC
    return user


def require_role(*roles: str) -> Callable[[User], User]:
    def _dependency(current_user: User = Depends(get_current_user)) -> User:
        if roles and current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this operation.",
            )
        return current_user

    return _dependency
