from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from ..database import get_db
from ..core.security import verify_token
from ..crud.user import get_user_crud
from ..core.errors import UnauthorizedError, ForbiddenError

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> dict:
    token = credentials.credentials
    
    payload = verify_token(token)
    if not payload:
        raise UnauthorizedError("Invalid authentication credentials")
    
    user_crud = get_user_crud()
    user = await user_crud.get(db, uuid.UUID(payload["user_id"]))
    
    if not user:
        raise UnauthorizedError("User not found")
    
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "college": user.college,
        "department": user.department,
    }


async def get_current_active_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    return current_user


async def require_admin(
    current_user: dict = Depends(get_current_user),
) -> dict:
    if current_user["role"] != "Admin":
        raise ForbiddenError("Admin privileges required")
    return current_user