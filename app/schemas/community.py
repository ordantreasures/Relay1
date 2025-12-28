from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from ..models.community import CommunityType
from uuid import UUID
from .user import UserResponse


class CommunityBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: str = Field(..., min_length=10, max_length=500)
    type: CommunityType
    image_url: Optional[str] = None
    college: Optional[str] = None


class CommunityCreate(CommunityBase):
    pass


class CommunityUpdate(BaseModel):
    description: Optional[str] = Field(None, min_length=10, max_length=500)
    image_url: Optional[str] = None


class CommunityResponse(CommunityBase):
    id: UUID
    creator: UserResponse
    member_count: int
    is_member: bool = False
    is_admin: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True