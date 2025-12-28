from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from ..models.user import College, UserRole


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: str
    username: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    display_name: str = Field(..., min_length=2, max_length=100)
    department: str = Field(..., min_length=2, max_length=100)
    college: College
    role: Optional[UserRole] = Field(default=UserRole.STUDENT)
    avatar_url: Optional[str] = Field(default=None)
    bio: Optional[str] = Field(default=None)
    interests: Optional[List[str]] = Field(default_factory=list)
    
    @validator("email")
    def validate_email_domain(cls, v):
        if not v.endswith("@stu.cu.edu.ng"):
            raise ValueError("Email must be a student email (@stu.cu.edu.ng)")
        return v
    
    @validator("interests")
    def validate_interests(cls, v):
        if v and len(v) < 3:
            raise ValueError("Select at least 3 interests")
        return v


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    display_name: str
    department: str
    college: College
    role: UserRole = UserRole.STUDENT
    interests: List[str] = Field(default_factory=list)
    bio: Optional[str] = None