from sqlalchemy import Column, String, DateTime, Enum, Integer, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
import uuid
from datetime import datetime
from typing import Optional
from ..database import Base
import enum


class CommunityType(str, enum.Enum):
    ACADEMIC = "ACADEMIC"
    INTEREST = "INTEREST"
    OFFICIAL = "OFFICIAL"


class Community(Base):
    __tablename__ = "communities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    member_count: Mapped[int] = mapped_column(Integer, default=0)
    type: Mapped[CommunityType] = mapped_column(Enum(CommunityType), nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    college: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Optional college association

    # Creator
    creator_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    creator = relationship("User")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    members = relationship("CommunityMember", back_populates="community", cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="community", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Community {self.name}>"


class CommunityMember(Base):
    __tablename__ = "community_members"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    community_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("communities.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    community = relationship("Community", back_populates="members")
    user = relationship("User")
    
    __table_args__ = (UniqueConstraint('community_id', 'user_id', name='unique_community_member'),)