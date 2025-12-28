from sqlalchemy import String, DateTime, Enum, JSON, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from ..database import Base
import enum
from typing import List,Optional


class UserRole(str, enum.Enum):
    STUDENT = "Student"
    CREATOR = "Creator"
    BUSINESS = "Business"
    CLUB = "Club"
    FACULTY = "Faculty"
    ADMIN = "Admin"


class College(str, enum.Enum):
    COE = "COE"
    CST = "CST"
    CMSS = "CMSS"
    CLDS = "CLDS"
    GLOBAL = "GLOBAL"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.STUDENT, nullable=True)
    avatar_url: Mapped[str] = mapped_column(String(500), nullable=True)
    college: Mapped[College] = mapped_column(Enum(College), nullable=False)
    department: Mapped[str] = mapped_column(String(100), nullable=False)
    bio: Mapped[str] = mapped_column(String(500), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    interests: Mapped[List[str]] = mapped_column(JSON, default=list)  # Store as list of strings

    # Authentication
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(  # ✅ Add Optional
        DateTime(timezone=True), 
        onupdate=func.now(), 
        nullable=True  # ✅ Allow NULL
    )
    
    # Relationships will be defined in other models

    # Relationships
    posts = relationship("Post", back_populates="author", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="author", cascade="all, delete-orphan")
    upvoted_posts = relationship("PostUpvote", back_populates="user", cascade="all, delete-orphan")
    saved_posts = relationship("PostSave", back_populates="user", cascade="all, delete-orphan")
    communities = relationship("CommunityMember", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    
    # For community creation
    created_communities = relationship("Community", back_populates="creator", cascade="all, delete-orphan")
    
    
    def __repr__(self):
        return f"<User {self.username}>"