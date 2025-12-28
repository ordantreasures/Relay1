from fastapi import APIRouter, Depends, Query, Path, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from ..database import get_db
from ..crud.notification import get_notification_crud
from ..schemas.notification import NotificationResponse
from ..core.errors import NotFoundError, ForbiddenError
from .dependencies import get_current_active_user

router = APIRouter()

# Get user notifications with pagination and filtering
@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    notification_crud = get_notification_crud()
    notifications = await notification_crud.get_user_notifications(
        db,
        user_id=uuid.UUID(current_user["id"]),
        skip=skip,
        limit=limit,
        unread_only=unread_only,
    )

    return notifications

# Mark a notification as read
@router.post("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str = Path(...),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    notification_crud = get_notification_crud()
    
    notification = await notification_crud.mark_as_read(
        db,
        notification_id=uuid.UUID(notification_id),
        user_id=uuid.UUID(current_user["id"]),
    )
    
    if not notification:
        raise NotFoundError("Notification", notification_id)
    
    return {"message": "Notification marked as read"}

# Mark all notifications as read
@router.post("/read-all")
async def mark_all_notifications_as_read(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    notification_crud = get_notification_crud()
    
    count = await notification_crud.mark_all_as_read(
        db, user_id=uuid.UUID(current_user["id"])
    )
    
    return {"message": f"{count} notifications marked as read"}

# Delete a notification
@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: str = Path(...),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    notification_crud = get_notification_crud()
    
    notification = await notification_crud.get(db, uuid.UUID(notification_id))
    
    if not notification:
        raise NotFoundError("Notification", notification_id)
    
    # Check ownership
    if str(notification.user_id) != current_user["id"]:
        raise ForbiddenError("You can only delete your own notifications")
    
    await notification_crud.remove(db, id=uuid.UUID(notification_id))