from fastapi import APIRouter, Depends, Query, Path, status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from ..database import get_db
from ..crud.user import get_user_crud
from ..crud.post import get_post_crud
from ..schemas.user import UserResponse, UserUpdate, UserStats
from ..schemas.post import PostResponse, PostListResponse
from ..core.errors import NotFoundError, ForbiddenError
from .dependencies import get_current_user, get_current_active_user

router = APIRouter()

# Get current user's profile
@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    user_crud = get_user_crud()
    user = await user_crud.get(db, uuid.UUID(current_user["id"]))
    
    if not user:
        raise NotFoundError("User", current_user["id"])
    
    return user

# Update current user's profile
@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    user_crud = get_user_crud()
    user = await user_crud.get(db, uuid.UUID(current_user["id"]))
    
    if not user:
        raise NotFoundError("User", current_user["id"])
    
    updated_user = await user_crud.update(db, db_obj=user, obj_in=user_data)
    
    return updated_user

# Get another user's profile by username
@router.get("/{username}", response_model=UserResponse)
async def get_user_profile(
    username: str = Path(...),
    current_user: Optional[dict] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_crud = get_user_crud()
    user = await user_crud.get_by_username(db, username)
    
    if not user:
        raise NotFoundError("User", username)
    
    return user

# Get posts by a specific user
@router.get("/{username}/posts", response_model=PostListResponse)
async def get_user_posts(
    username: str = Path(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: Optional[dict] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_crud = get_user_crud()
    user = await user_crud.get_by_username(db, username)
    
    if not user:
        raise NotFoundError("User", username)
    
    user_id = uuid.UUID(current_user["id"]) if current_user else None
    
    post_crud = get_post_crud()
    posts = await post_crud.get_multi_filtered(
        db,
        skip=skip,
        limit=limit,
        author_id=user.id,
        user_id=user_id,
    )
    
    total = len(posts)  # Simplified
    
    return {
        "data": posts,
        "pagination": {
            "page": (skip // limit) + 1,
            "limit": limit,
            "total": total,
            "hasNext": len(posts) == limit,
            "hasPrev": skip > 0,
        }
    }

# Get saved posts of the current user
@router.get("/me/saved", response_model=PostListResponse)
async def get_saved_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(current_user["id"])
    
    post_crud = get_post_crud()
    posts = await post_crud.get_multi_filtered(
        db,
        skip=skip,
        limit=limit,
        saved_by=user_id,
        user_id=user_id,
    )
    
    total = len(posts)  # Simplified
    
    return {
        "data": posts,
        "pagination": {
            "page": (skip // limit) + 1,
            "limit": limit,
            "total": total,
            "hasNext": len(posts) == limit,
            "hasPrev": skip > 0,
        }
    }

# Get user statistics
@router.get("/me/stats", response_model=UserStats)
async def get_user_stats(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    # This would be more efficient with a dedicated query
    # For now, we'll count from existing data
    
    post_crud = get_post_crud()
    user_posts = await post_crud.get_multi_filtered(
        db,
        author_id=uuid.UUID(current_user["id"]),
        limit=1000,  # Large limit to get all
    )
    
    saved_posts = await post_crud.get_multi_filtered(
        db,
        saved_by=uuid.UUID(current_user["id"]),
        limit=1000,
    )
    
    # Calculate stats
    post_count = len(user_posts)
    upvote_count = sum(post.upvotes_count for post in user_posts)
    saved_count = len(saved_posts)
    
    # Comment count would need separate query
    comment_count = 0  # Placeholder
    
    return {
        "post_count": post_count,
        "upvote_count": upvote_count,
        "comment_count": comment_count,
        "saved_count": saved_count,
    }