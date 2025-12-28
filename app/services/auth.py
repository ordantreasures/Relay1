from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from ..crud.user import get_user_crud
from ..core.security import create_access_token, create_refresh_token, verify_password
from ..schemas.auth import RegisterRequest
from ..schemas.user import UserCreate
from ..models.user import UserRole


class AuthService:
    @staticmethod
    async def authenticate(
        db: AsyncSession, email: str, password: str
    ) -> Optional[Dict[str, Any]]:
        user_crud = get_user_crud()
        user = await user_crud.authenticate(db, email, password)
        
        if not user:
            return None
        
        # Create tokens
        token_data = {"user_id": str(user.id), "username": user.username}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        return {
            "user": user,
            "tokens": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
            }
        }
    
    @staticmethod
    async def register(
        db: AsyncSession, register_data: RegisterRequest
    ) -> Dict[str, Any]:
        user_crud = get_user_crud()
        
        # Check if email exists
        existing = await user_crud.get_by_email(db, register_data.email)
        if existing:
            raise ValueError("Email already registered")
        
        # Generate username
        username = register_data.email.split("@")[0]
        existing_username = await user_crud.get_by_username(db, username)
        
        if existing_username:
            import random
            username = f"{username}{random.randint(100, 999)}"
        
        # Create user
        user_create = UserCreate(
            username=username,
            email=register_data.email,
            display_name=register_data.display_name,
            password=register_data.password,
            role=UserRole.STUDENT,
            avatar_url=register_data.avatar_url,
            bio=register_data.bio,
            college=register_data.college,
            department=register_data.department,
            interests=register_data.interests or [],
        )
        
        user = await user_crud.create(db, obj_in=user_create)
        
        # Create tokens
        token_data = {"user_id": str(user.id), "username": user.username}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        return {
            "user": user,
            "tokens": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
            }
        }
    
    @staticmethod
    async def refresh_access_token(
        db: AsyncSession, refresh_token: str
    ) -> Optional[Dict[str, Any]]:
        from ..core.security import verify_token
        
        payload = verify_token(refresh_token, token_type="refresh")
        if not payload:
            return None
        
        user_crud = get_user_crud()
        user = await user_crud.get(db, uuid.UUID(payload["user_id"]))
        
        if not user:
            return None
        
        # Create new tokens
        token_data = {"user_id": str(user.id), "username": user.username}
        new_access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }