from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from ..models.notification import NotificationType


class NotificationCreate(BaseModel):
    user_id: str
    type: NotificationType
    message: str
    post_id: Optional[str] = None
    comment_id: Optional[str] = None
    community_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NotificationResponse(BaseModel):
    id: UUID
    type: NotificationType
    message: str
    read: bool
    post_id: Optional[str]
    comment_id: Optional[str]
    community_id: Optional[str]
    metadata: Dict[str, Any]
    created_at: datetime
    
    class Config:
        from_attributes = True