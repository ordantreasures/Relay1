from typing import Optional, Dict, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from sqlalchemy import desc
import uuid

from ..models.notification import Notification, NotificationType
from ..schemas.notification import NotificationCreate
from .base import CRUDBase


class CRUDNotification(CRUDBase[Notification, NotificationCreate, BaseModel]):
    async def get_user_notifications(
        self, db: AsyncSession, user_id: uuid.UUID, skip: int = 0, limit: int = 50, unread_only: bool = False
    ) -> Sequence[Notification]:
        query = select(Notification).filter(
            Notification.user_id == user_id
        )

        if unread_only:
            query = query.filter(Notification.read == False)

        query = query.order_by(
            desc(Notification.created_at)
        ).offset(skip).limit(limit)

        result = await db.execute(query)

        return result.scalars().all()
    
    async def create_notification(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        type: NotificationType,
        message: str,
        post_id: Optional[uuid.UUID] = None,
        comment_id: Optional[uuid.UUID] = None,
        community_id: Optional[uuid.UUID] = None,
        meta: Optional[Dict] = None,
    ) -> Notification:
        db_obj = Notification(
            user_id=user_id,
            type=type,
            message=message,
            post_id=post_id,
            comment_id=comment_id,
            community_id=community_id,
            meta=meta or {},
        )
        
        db.add(db_obj)
        await db.flush()
        return db_obj
    
    async def mark_as_read(
        self, db: AsyncSession, notification_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[Notification]:
        notification = await self.get(db, notification_id)

        if notification and notification.user_id == user_id:
            notification.read = True
            db.add(notification)
            await db.flush()

        return notification
    
    async def mark_all_as_read(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> int:
        result = await db.execute(
            select(Notification).filter(
                Notification.user_id == user_id,
                Notification.read == False
            )
        )
        
        notifications = result.scalars().all()
        count = 0
        
        for notification in notifications:
            notification.read = True
            db.add(notification)
            count += 1
        
        if count > 0:
            await db.flush()
        
        return count


def get_notification_crud():
    return CRUDNotification(Notification)