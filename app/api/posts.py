from fastapi import APIRouter, Depends, Query, Path, status
from typing_extensions import Annotated
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import uuid
from uuid import UUID

from ..database import get_db
from ..crud.post import get_post_crud
from ..crud.comment import get_comment_crud
from ..crud.notification import get_notification_crud
from ..schemas.post import PostCreate, PostUpdate, PostResponse, PostListResponse
from ..schemas.comment import CommentCreate, CommentResponse
from ..models import Post
from ..models.post import PostType, College
from ..models.notification import NotificationType
from ..core.errors import NotFoundError, ForbiddenError
from .dependencies import get_current_user, get_current_active_user

router = APIRouter()

# Get multiple posts with filtering and pagination
@router.get("/", response_model=PostListResponse)
async def get_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    type_filter: Optional[PostType] = Query(None),
    college: Optional[College] = Query(None),
    department: Optional[str] = Query(None),
    query: Optional[str] = Query(None),
    only_pinned: bool = Query(False),
    current_user: Optional[dict] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(current_user["id"]) if current_user else None
    
    post_crud = get_post_crud()
    posts = await post_crud.get_multi_filtered(
        db,
        skip=skip,
        limit=limit,
        type_filter=type_filter,
        college=college,
        department=department,
        user_id=user_id,
        query=query,
        only_pinned=only_pinned,
    )
    
    # Get total count for pagination
    total = len(posts)  # Simplified - in real app, get count from query
    
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

# Get trending posts
@router.get("/trending", response_model=List[PostResponse])
async def get_trending_posts(
    limit: int = Query(10, ge=1, le=50),
    current_user: Optional[dict] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(current_user["id"]) if current_user else None
    
    post_crud = get_post_crud()
    posts = await post_crud.get_trending(db, limit=limit, user_id=user_id)
    
    return posts




# Create a new post
@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_data: PostCreate,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    post_crud = get_post_crud()

    # 1️ Create the post with the current user as author
    post = await post_crud.create_with_author(
        db,
        obj_in=post_data,
        author_id=UUID(current_user["id"]),
    )

    # 2 Refresh the post to populate scalar fields
    await db.refresh(post)

    # 3 Eager-load the author relationship to avoid MissingGreenlet
    result = await db.execute(
        select(Post)
        .where(Post.id == post.id)
        .options(selectinload(Post.author))
    )
    post = result.scalar_one()

    # 4 Convert to Pydantic response using model_validate
    response = PostResponse.model_validate(post)

    # 5 Populate dynamic user-specific fields
    response.is_saved = False    # implement your logic if needed
    response.is_upvoted = False  # implement your logic if needed

    return response


# GET a single post by ID
@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: UUID = Path(...),
    current_user: Optional[dict] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(current_user["id"]) if current_user else None
    
    post_crud = get_post_crud()
    post = await post_crud.get_with_author(db, post_id, user_id)

    if not post:
        raise NotFoundError("Post", str(post_id))
    
    # Increment view count
    await post_crud.increment_views(db, post_id)
    
    return post


# Update a post
@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_data: PostUpdate,
    post_id: UUID = Path(...),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    post_crud = get_post_crud()
    post = await post_crud.get(db, post_id)
    
    if not post:
        raise NotFoundError("Post", post_id)
    
    # Check ownership (or admin)
    if str(post.author_id) != current_user["id"] and current_user["role"] != "Admin":
        raise ForbiddenError("You can only update your own posts")
    
    updated_post = await post_crud.update(db, db_obj=post, obj_in=post_data)
    
    # Get full updated post
    full_post = await post_crud.get_with_author(
        db, updated_post.id, user_id=uuid.UUID(current_user["id"])
    )
    
    return full_post


# Delete a post
@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: UUID = Path(...),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    post_crud = get_post_crud()
    post = await post_crud.get(db, post_id)
    
    if not post:
        raise NotFoundError("Post", post_id)
    
    # Check ownership (or admin)
    if str(post.author_id) != current_user["id"] and current_user["role"] != "Admin":
        raise ForbiddenError("You can only delete your own posts")
    
    await post_crud.remove(db, id=post_id)


# Toggle upvote on a post
@router.post("/{post_id}/upvote")
async def toggle_upvote(
    post_id: UUID = Path(...),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    post_crud = get_post_crud()
    
    # Check if post exists
    post = await post_crud.get(db, post_id)
    if not post:
        raise NotFoundError("Post", post_id)
    
    result = await post_crud.toggle_upvote(
        db,
        post_id=post_id,
        user_id=uuid.UUID(current_user["id"]),
    )
    
    return result


# Toggle save on a post
@router.post("/{post_id}/save")
async def toggle_save(
    post_id: UUID = Path(...),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    post_crud = get_post_crud()
    
    # Check if post exists
    post = await post_crud.get(db, post_id)
    if not post:
        raise NotFoundError("Post", post_id)
    
    result = await post_crud.toggle_save(
        db,
        post_id=post_id,
        user_id=uuid.UUID(current_user["id"]),
    )
    
    return result


# create a comment within a post
@router.post("/{post_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    post_id: Annotated[UUID, Path(...)],
    comment_data: CommentCreate,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    comment_crud = get_comment_crud()

    post_crud = get_post_crud()
    post = await post_crud.get(db, post_id)
    if not post:
        raise NotFoundError("Post", post_id)

    if comment_data.parent_id:
        parent = await comment_crud.get(db, uuid.UUID(comment_data.parent_id))
        if not parent:
            raise NotFoundError("Comment", comment_data.parent_id)

    comment = await comment_crud.create_with_author(
        db,
        obj_in=comment_data,
        author_id=uuid.UUID(current_user["id"]),
        post_id=post_id,
    )

    full_comment = await comment_crud.get_with_replies(db, comment.id)

    if str(post.author_id) != current_user["id"]:
        notification_crud = get_notification_crud()
        await notification_crud.create_notification(
            db,
            user_id=post.author_id,
            type=NotificationType.REPLY,
            message=f"{current_user['display_name']} commented on your post",
            post_id=post_id,
            comment_id=comment.id,
            meta={"commenter_id": current_user["id"]},
        )

    return full_comment

# Get comments for a post
@router.get("/{post_id}/comments", response_model=List[CommentResponse])
async def get_post_comments(
    post_id: UUID = Path(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: Optional[dict] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    post_crud = get_post_crud()
    post = await post_crud.get(db, post_id)
    
    if not post:
        raise NotFoundError("Post", str(post_id))
    
    comment_crud = get_comment_crud()
    comments = await comment_crud.get_by_post(
        db,
        post_id=post_id,
        skip=skip,
        limit=limit,
    )
    
    return comments


# Get saved posts for current user
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
        saved_by=user_id,
        skip=skip,
        limit=limit,
    )

    # Get total count for pagination
    total = await post_crud.get_count_filtered(db, saved_by=user_id)