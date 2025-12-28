from typing import Optional, Dict, Any, Sequence,cast, Text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import select, func, desc, or_, and_, update, exists
from sqlalchemy.orm import selectinload
import uuid
from datetime import datetime, timedelta, timezone

from ..models.post import Post, PostUpvote, PostSave, PostType, PostStatus, College
from ..schemas.post import PostCreate, PostUpdate
from .base import CRUDBase


class CRUDPost(CRUDBase[Post, PostCreate, PostUpdate]):
    async def get_with_author(self, db: AsyncSession, id: uuid.UUID, user_id: Optional[uuid.UUID] = None) -> Optional[Post]:
        query = select(Post).options(
            selectinload(Post.author)
        ).filter(Post.id == id)
        
        result = await db.execute(query)
        post = result.scalar_one_or_none()
        
        if post and user_id:
            # Check if user has upvoted/saved
            upvote_result = await db.execute(
                select(PostUpvote).filter(
                    PostUpvote.post_id == post.id,
                    PostUpvote.user_id == user_id
                )
            )
            save_result = await db.execute(
                select(PostSave).filter(
                    PostSave.post_id == post.id,
                    PostSave.user_id == user_id
                )
            )
            
            post.is_upvoted = upvote_result.scalar_one_or_none() is not None
            post.is_saved = save_result.scalar_one_or_none() is not None
        
        return post
    
    async def create_with_author(
        self, db: AsyncSession, *, obj_in: PostCreate, author_id: uuid.UUID
    ) -> Post:
        db_obj = Post(
            **obj_in.model_dump(exclude={"event_date", "event_time", "deadline"}),
            author_id=author_id,
        )
        
        # Handle date fields
        if obj_in.event_date:
            db_obj.event_date = datetime.combine(obj_in.event_date, datetime.min.time(), tzinfo=timezone.utc)
        if obj_in.event_time:
            db_obj.event_time = obj_in.event_time
        if obj_in.deadline:
            db_obj.deadline = obj_in.deadline.replace(tzinfo=timezone.utc) if obj_in.deadline.tzinfo is None else obj_in.deadline

        db.add(db_obj)
        await db.flush()

        return db_obj
    
    async def get_multi_filtered(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 20,
        type_filter: Optional[PostType] = None,
        college: Optional[College] = None,
        department: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        saved_by: Optional[uuid.UUID] = None,
        author_id: Optional[uuid.UUID] = None,
        query: Optional[str] = None,
        only_pinned: bool = False,
    ) -> Sequence[Post]:
        query_builder = select(Post).options(selectinload(Post.author))
        
        # Apply filters
        filters = []
        
        if type_filter:
            filters.append(Post.type == type_filter)
        
        if college:
            filters.append(Post.target_colleges.op("@>")([college.value]))
        
        if department:
            filters.append(Post.target_departments.op("@>")([department]))
        
        if author_id:
            filters.append(Post.author_id == author_id)
        
        if only_pinned:
            filters.append(Post.is_pinned == True)
        
        if query:
            filters.append(or_(
                Post.title.ilike(f"%{query}%"),
                Post.content.ilike(f"%{query}%"),
                Post.tags.op("@>")([query]),   # JSONB array contains string
                
            ))
        
        if saved_by:
            filters.append(Post.id.in_(select(PostSave.post_id).filter(PostSave.user_id == saved_by)))
        
        if filters:
            query_builder = query_builder.filter(and_(*filters))
        
        # Order by pinned first, then recency
        query_builder = query_builder.order_by(
            desc(Post.is_pinned),
            desc(Post.created_at)
        ).offset(skip).limit(limit)
        
        result = await db.execute(query_builder)
        posts = result.scalars().all()
        
        # Check user interactions
        if user_id:
            for post in posts:
                upvote_result = await db.execute(
                    select(PostUpvote).filter(
                        PostUpvote.post_id == post.id,
                        PostUpvote.user_id == user_id
                    )
                )
                save_result = await db.execute(
                    select(PostSave).filter(
                        PostSave.post_id == post.id,
                        PostSave.user_id == user_id
                    )
                )
                
                post.is_upvoted = upvote_result.scalar_one_or_none() is not None
                post.is_saved = save_result.scalar_one_or_none() is not None
        
        return posts
    
    async def get_trending(
        self, db: AsyncSession, *, limit: int = 10, user_id: Optional[uuid.UUID] = None
    ) -> Sequence[Post]:
        # Calculate trending score: upvotes + (comments * 3) + (views / 100)
        # Get posts from last 7 days
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        
        query = select(Post).options(selectinload(Post.author)).filter(
            Post.created_at >= week_ago,
            Post.status == PostStatus.ACTIVE,
        ).order_by(
            desc(
                Post.upvotes_count +
                (Post.comments_count * 3) +
                (Post.views / 100)
            )
        ).limit(limit)
        
        result = await db.execute(query)
        posts = result.scalars().all()
        
        # Check user interactions
        if user_id:
            for post in posts:
                upvote_result = await db.execute(
                    select(PostUpvote).filter(
                        PostUpvote.post_id == post.id,
                        PostUpvote.user_id == user_id
                    )
                )
                save_result = await db.execute(
                    select(PostSave).filter(
                        PostSave.post_id == post.id,
                        PostSave.user_id == user_id
                    )
                )
                
                post.is_upvoted = upvote_result.scalar_one_or_none() is not None
                post.is_saved = save_result.scalar_one_or_none() is not None
        
        return posts
    
    async def toggle_upvote(
        self, db: AsyncSession, *, post_id: uuid.UUID, user_id: uuid.UUID
    ) -> Dict[str, Any]:
        # Check if already upvoted
        existing = await db.execute(
            select(PostUpvote).filter(
                PostUpvote.post_id == post_id,
                PostUpvote.user_id == user_id
            )
        )
        existing = existing.scalar_one_or_none()

        if existing:
            # Remove upvote
            await db.delete(existing)
            await db.flush()

            # Decrement count
            await db.execute(
                update(Post).where(Post.id == post_id).values(
                    upvotes_count=func.greatest(Post.upvotes_count - 1, 0)
                )
            )
            result = await db.execute(select(Post.upvotes_count).where(Post.id == post_id))
            count = result.scalar_one()

            return {"upvoted": False, "count": count}
        else:
            # Add upvote
            upvote = PostUpvote(post_id=post_id, user_id=user_id)
            db.add(upvote)
            await db.flush()

            # Increment count
            await db.execute(
                update(Post).where(Post.id == post_id).values(
                    upvotes_count=Post.upvotes_count + 1
                )
            )
            result = await db.execute(select(Post.upvotes_count).where(Post.id == post_id))
            count = result.scalar_one()

            return {"upvoted": True, "count": count}
    
    async def toggle_save(
        self, db: AsyncSession, *, post_id: uuid.UUID, user_id: uuid.UUID
    ) -> Dict[str, Any]:
        # Check if already saved
        existing = await db.execute(
            select(PostSave).filter(
                PostSave.post_id == post_id,
                PostSave.user_id == user_id
            )
        )
        existing = existing.scalar_one_or_none()

        if existing:
            # Remove save
            await db.delete(existing)
            await db.flush()

            # Decrement count
            await db.execute(
                update(Post).where(Post.id == post_id).values(
                    saves_count=func.greatest(Post.saves_count - 1, 0)
                )
            )
            result = await db.execute(select(Post.saves_count).where(Post.id == post_id))
            count = result.scalar_one()

            return {"saved": False, "count": count}
        else:
            # Add save
            save = PostSave(post_id=post_id, user_id=user_id)
            db.add(save)
            await db.flush()

            # Increment count
            await db.execute(
                update(Post).where(Post.id == post_id).values(
                    saves_count=Post.saves_count + 1
                )
            )
            result = await db.execute(select(Post.saves_count).where(Post.id == post_id))
            count = result.scalar_one()

            return {"saved": True, "count": count}
    
    async def get_count_filtered(
        self,
        db: AsyncSession,
        *,
        type_filter: Optional[PostType] = None,
        college: Optional[College] = None,
        department: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        saved_by: Optional[uuid.UUID] = None,
        author_id: Optional[uuid.UUID] = None,
        query: Optional[str] = None,
        only_pinned: bool = False,
    ) -> int:
        query_builder = select(func.count(Post.id))

        # Apply filters
        filters = []

        if type_filter:
            filters.append(Post.type == type_filter)

        if college:
            filters.append(Post.target_colleges.contains([college.value]))

        if department:
            filters.append(Post.target_departments.contains([department]))

        if author_id:
            filters.append(Post.author_id == author_id)

        if only_pinned:
            filters.append(Post.is_pinned == True)

        if query:
            filters.append(or_(
                Post.title.ilike(f"%{query}%"),
                Post.content.ilike(f"%{query}%"),
                Post.tags.contains([query]),
            ))

        if saved_by:
            filters.append(Post.id.in_(select(PostSave.post_id).filter(PostSave.user_id == saved_by)))

        if filters:
            query_builder = query_builder.filter(and_(*filters))

        result = await db.execute(query_builder)
        return result.scalar_one() or 0

    async def increment_views(self, db: AsyncSession, post_id: uuid.UUID) -> None:
        await db.execute(
            update(Post).where(Post.id == post_id).values(views=Post.views + 1)
        )

    async def get_saved_post(
         self, db: AsyncSession, user_id: uuid.UUID
      ) -> Sequence[uuid.UUID]:
         result = await db.execute(
               select(PostSave.post_id).filter(PostSave.user_id == user_id)
         )
         return [row[0] for row in result.all()]
      
    async def update(
    self,
    db: AsyncSession,
    *,
    db_obj: Post,
    obj_in: PostUpdate,
) -> Post:
      update_data = obj_in.model_dump(exclude_unset=True)

      for field, value in update_data.items():
        setattr(db_obj, field, value)

      await db.commit()
      await db.refresh(db_obj)
      return db_obj

    
    



def get_post_crud():
    return CRUDPost(Post)