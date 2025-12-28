from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from .user import UserResponse


class CommentBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)


class CommentCreate(CommentBase):
    parent_id: Optional[str] = None
    content: Optional[str] = None


class CommentResponse(CommentBase):
    id: UUID
    author: UserResponse
    post_id: UUID
    parent_id: Optional[str]
    replies: List["CommentResponse"] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# For recursive model
CommentResponse.update_forward_refs()