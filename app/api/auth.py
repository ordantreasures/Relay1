from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
import uuid

from ..database import get_db
from ..crud.user import get_user_crud
from ..core.security import create_access_token, create_refresh_token, verify_token
from ..schemas.auth import LoginRequest, RegisterRequest, Token
from ..schemas.user import UserResponse, UserCreate
from ..core.errors import APIError, ValidationError, UnauthorizedError
from ..models.user import UserRole
from .dependencies import get_current_user

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=Token)
async def register(
    register_data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    user_crud = get_user_crud()
    
    # Check if email already exists
    existing_user = await user_crud.get_by_email(db, register_data.email)
    if existing_user:
        raise APIError(
            code="EMAIL_EXISTS",
            message="Email already registered",
            status_code=status.HTTP_409_CONFLICT,
        )
    
    # Generate username from email
    username = register_data.email.split("@")[0]
    
    # Check if username exists
    existing_username = await user_crud.get_by_username(db, username)
    if existing_username:
        # Add random suffix
        import random
        username = f"{username}{random.randint(100, 999)}"
    
    # Create user
    user_create = UserCreate(
        username=username,
        email=register_data.email,
        display_name=register_data.display_name,
        password=register_data.password,
        college=register_data.college,
        department=register_data.department,
        interests=register_data.interests or [],
        role=register_data.role if register_data.role else UserRole.STUDENT,
        avatar_url=register_data.avatar_url,
        bio=register_data.bio,
    )
    
    user = await user_crud.create(db, obj_in=user_create)
    
    # Create tokens
    token_data = {"user_id": str(user.id), "username": user.username}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    user_crud = get_user_crud()
    
    # Authenticate user
    user = await user_crud.authenticate(db, login_data.email, login_data.password)
    if not user:
        raise APIError(
            code="INVALID_CREDENTIALS",
            message="Invalid email or password",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    
    # Validate email domain (double check)
    if not str(login_data.email).endswith("@stu.cu.edu.ng"):
        raise ValidationError("Email domain not allowed")
    
    # Create tokens
    token_data = {"user_id": str(user.id), "username": user.username}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }





@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db),
):
    # Verify refresh token
    payload = verify_token(refresh_token, token_type="refresh")
    if not payload:
        raise UnauthorizedError("Invalid refresh token")
    
    user_crud = get_user_crud()
    user = await user_crud.get(db, uuid.UUID(payload["user_id"]))
    
    if not user:
        raise UnauthorizedError("User not found")
    
    # Create new tokens
    token_data = {"user_id": str(user.id), "username": user.username}
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post("/logout")
async def logout(
    current_user: dict = Depends(get_current_user),
):
    # In a real app, you might want to blacklist the token
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_crud = get_user_crud()
    user = await user_crud.get(db, uuid.UUID(current_user["id"]))
    
    if not user:
        raise UnauthorizedError("User not found")
    
    return user