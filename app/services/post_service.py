from typing import List, Optional, Dict, Any, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from datetime import datetime, timedelta

from ..crud.post import get_post_crud
from ..crud.comment import get_comment_crud
from ..models.post import PostType, PostStatus, College, Post
from ..schemas.post import PostCreate, PostUpdate


class PostService:
    @staticmethod
    async def create_post(
        db: AsyncSession,
        post_data: PostCreate,
        author_id: uuid.UUID,
        current_user: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        post_crud = get_post_crud()
        
        # Create post
        post = await post_crud.create_with_author(
            db,
            obj_in=post_data,
            author_id=author_id,
        )
        
        # Get full post
        full_post = await post_crud.get_with_author(db, post.id, user_id=author_id)
        
        return {
            "post": full_post,
            "message": "Post created successfully",
        }
    
    @staticmethod
    async def get_feed(
        db: AsyncSession,
        user_id: Optional[uuid.UUID] = None,
        college: Optional[College] = None,
        department: Optional[str] = None,
        type_filter: Optional[PostType] = None,
        skip: int = 0,
        limit: int = 20,
        query: Optional[str] = None,
    ) -> Dict[str, Any]:
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
        )
        
        return {
            "posts": posts,
            "count": len(posts),
            "skip": skip,
            "limit": limit,
        }
    
    @staticmethod
    async def get_trending(
        db: AsyncSession,
        user_id: Optional[uuid.UUID] = None,
        limit: int = 10,
        days: int = 7,
    ) -> Sequence[Post]:
        post_crud = get_post_crud()
        
        posts = await post_crud.get_trending(db, limit=limit, user_id=user_id)
        
        return posts
    
    @staticmethod
    async def search_posts(
        db: AsyncSession,
        query: str,
        user_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Dict[str, Any]:
        post_crud = get_post_crud()
        
        posts = await post_crud.get_multi_filtered(
            db,
            skip=skip,
            limit=limit,
            user_id=user_id,
            query=query,
        )
        
        return {
            "posts": posts,
            "count": len(posts),
            "query": query,
        }
    
    @staticmethod
    async def add_comment(
        db: AsyncSession,
        post_id: uuid.UUID,
        content: str,
        author_id: uuid.UUID,
        parent_id: Optional[uuid.UUID] = None,
    ) -> Dict[str, Any]:
        comment_crud = get_comment_crud()
        
        # Create comment
        from ..schemas.comment import CommentCreate
        comment_data = CommentCreate(
            post_id=str(post_id),
            content=content,
            parent_id=str(parent_id) if parent_id else None,
        )
        
        comment = await comment_crud.create_with_author(
            db,
            obj_in=comment_data,
            author_id=author_id,
        )
        
        # Get full comment
        full_comment = await comment_crud.get_with_replies(db, comment.id)
        
        return {
            "comment": full_comment,
            "message": "Comment added successfully",
        }