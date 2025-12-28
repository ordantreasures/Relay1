from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from sqlalchemy.future import select
from sqlalchemy import update
from sqlalchemy.orm import selectinload, joinedload
import uuid
from pydantic import BaseModel

from ..models.comment import Comment
from ..models.user import User
from ..models.post import Post
from ..schemas.comment import CommentCreate
from .base import CRUDBase


class CRUDComment(CRUDBase[Comment, CommentCreate, BaseModel]):
    async def create_with_author(
        self,
        db: AsyncSession,
        *,
        obj_in: CommentCreate,
        author_id: UUID,
        post_id: UUID,
    ) -> Comment:
            db_obj = Comment(
                content=obj_in.content,
                parent_id=obj_in.parent_id,
                author_id=author_id,
                post_id=post_id,
            )
    
            db.add(db_obj)
    
            try:
                await db.commit()
            except Exception:
                await db.rollback()
                raise
    
            await db.refresh(db_obj)
            return db_obj
    
    async def get_by_post(
        self, db: AsyncSession, post_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Comment]:
        # Get top-level comments (no parent)
        result = await db.execute(
            select(Comment).options(
                selectinload(Comment.author),
                selectinload(Comment.replies).selectinload(Comment.author)
            ).filter(
                Comment.post_id == post_id,
                Comment.parent_id == None
            ).order_by(Comment.created_at.asc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_with_replies(
        self, db: AsyncSession, comment_id: uuid.UUID
    ) -> Optional[Comment]:
        result = await db.execute(
            select(Comment).options(
                selectinload(Comment.author),
                selectinload(Comment.replies).selectinload(Comment.author)
            ).filter(Comment.id == comment_id)
        )
        
        return result.scalar_one_or_none()


def get_comment_crud():
    return CRUDComment(Comment)