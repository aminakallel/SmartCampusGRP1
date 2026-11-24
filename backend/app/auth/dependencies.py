from functools import lru_cache
import os
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.models import UserAccount, UserRole
from app.auth.postgres_repository import DatabaseUnavailable, PostgresUserRepository
from app.auth.repository import InMemoryUserRepository, UserRepository
from app.auth.security import InvalidToken, JWTSettings, decode_access_token


_bearer = HTTPBearer(auto_error=False)


@lru_cache
def get_user_repository() -> UserRepository:
    """Use PostgreSQL by default; permit memory storage only when explicitly enabled."""
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if database_url:
        return PostgresUserRepository(database_url)
    if os.environ.get("AUTH_USE_IN_MEMORY", "").lower() == "true":
        return InMemoryUserRepository()
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Account database is not configured",
    )


def get_jwt_settings() -> JWTSettings:
    return JWTSettings.from_environment()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    repository: UserRepository = Depends(get_user_repository),
) -> UserAccount:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer authentication is required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        settings = JWTSettings.from_environment()
        claims = decode_access_token(credentials.credentials, settings)
        user_id = UUID(str(claims["sub"]))
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured",
        ) from exc
    except (InvalidToken, ValueError, KeyError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    try:
        user = repository.get_by_id(user_id)
    except DatabaseUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Account database is unavailable",
        ) from exc
    if user is None or not user.est_actif:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_roles(*allowed_roles: UserRole | str):
    allowed = {UserRole(role) for role in allowed_roles}

    def role_dependency(user: UserAccount = Depends(get_current_user)) -> UserAccount:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role",
            )
        return user

    return role_dependency


require_candidate = require_roles(UserRole.CANDIDAT)
require_admin = require_roles(UserRole.ADMIN)
