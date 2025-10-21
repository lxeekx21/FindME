from typing import List, Optional, Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose.exceptions import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.local_auth import verify_token
from app.db.session import get_db
from app.db.repositories.users import UserRepository
from app.models.user_models import UserDTO
from functools import wraps
import asyncio

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> UserDTO:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    token = credentials.credentials
    try:
        payload = verify_token(token, "access")
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from e

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    repo = UserRepository(db)
    user = await repo.get_by_id(int(user_id))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    return UserDTO.model_validate(user)


def role_required(*roles: str):
    def dependency(user: UserDTO = Depends(get_current_user)) -> UserDTO:
        if not roles:
            return user
        user_roles = {r.name for r in user.roles}
        if not any(role in user_roles for role in roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return dependency


def require_roles(*roles: str):
    """Decorator to enforce roles via dependency injection without cluttering endpoint params.

    Usage:
        @router.get("/admin")
        @require_roles("admin")
        async def endpoint(...):
            ...
    """

    def decorator(func: Callable):
        dep = role_required(*roles)
        if asyncio.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args, _user: UserDTO = Depends(dep), **kwargs):
                return await func(*args, **kwargs)

            return async_wrapper
        else:

            @wraps(func)
            def sync_wrapper(*args, _user: UserDTO = Depends(dep), **kwargs):
                return func(*args, **kwargs)

            return sync_wrapper

    return decorator
