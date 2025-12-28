# app/schemas/post.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, date

from ..models.enums import PostType, PostStatus, College
from .user import UserResponse
from .stats import PostStats


class PostBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    content: str = Field(..., min_length=10, max_length=5000)
    type: PostType
    tags: List[str] = Field(default_factory=list)
    target_colleges: List[College] = Field(default_factory=list)
    target_departments: List[str] = Field(default_factory=list)
    image_url: Optional[str] = None


class PostCreate(PostBase):
    event_date: Optional[date] = None
    event_time: Optional[str] = None
    location: Optional[str] = None

    price: Optional[str] = None
    condition: Optional[str] = None
    contact_info: Optional[str] = None

    link_url: Optional[str] = None
    deadline: Optional[datetime] = None

    is_pinned: bool = False

    @field_validator("event_time")
    @classmethod
    def validate_event_time(cls, v):
        if v and ":" not in v:
            raise ValueError("Event time must be HH:MM")
        return v

    @field_validator("link_url")
    @classmethod
    def validate_link_url(cls, v):
        if v and not v.startswith(("http://", "https://")):
            raise ValueError("Link URL must start with http:// or https://")
        return v


class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[PostStatus] = None
    image_url: Optional[str] = None
    location: Optional[str] = None
    price: Optional[str] = None
    link_url: Optional[str] = None


class PostResponse(PostBase):
    id: UUID
    author: UserResponse
    stats: PostStats
    status: PostStatus
    is_pinned: bool
    is_saved: bool = False
    is_upvoted: bool = False

    event_date: Optional[date] = None
    event_time: Optional[str] = None
    location: Optional[str] = None
    price: Optional[str] = None
    condition: Optional[str] = None
    contact_info: Optional[str] = None
    link_url: Optional[str] = None
    deadline: Optional[datetime] = None

    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {
        "from_attributes": True
    }


class PostListResponse(BaseModel):
    data: List[PostResponse]
    pagination: Dict[str, Any]
