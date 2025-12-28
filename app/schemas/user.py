from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict, validator
from typing import Optional, List
from datetime import datetime
from ..models.user import UserRole, College


class UserBase(BaseModel):
    username: str
    display_name: str
    role: UserRole = Field(default=UserRole.STUDENT)
    avatar_url: Optional[str] = None 
    college: College
    department: str
    bio: Optional[str] = None
    is_verified: bool = False
    interests: List[str] = Field(default_factory=list)


class UserCreate(BaseModel):
   
    # Required fields
    username: str
    email: EmailStr
    
    @field_validator('email', mode="after")
    @classmethod
    def validate_email(cls, v):
       if not v.endswith("@stu.cu.edu.ng"):
          raise ValueError("only Student emails are allowed")
       return v
       
    
    password: str = Field(
       min_length=6,
       description="password must be more than 6 characters"
    )
    display_name: str
    college: College
    department: str
    
    # Optional fields with defaults
    role: UserRole = Field(default=UserRole.STUDENT)
    avatar_url: Optional[str] = Field(default=None)
    bio: Optional[str] = Field(default=None)
    interests: List[str] = Field(default_factory=list)
    is_verified: bool = Field(default=False)


class UserUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=2, max_length=100)
    avatar_url: Optional[str] = Field(None)
    bio: Optional[str] = Field(None, max_length=500)
    department: Optional[str] = Field(None, min_length=2, max_length=100)
    interests: Optional[List[str]] = None


class UserResponse(UserBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class UserStats(BaseModel):
    post_count: int
    upvote_count: int
    comment_count: int
    saved_count: int