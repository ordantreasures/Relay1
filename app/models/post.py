# app/models/post.py
from sqlalchemy import (
    String,
    DateTime,
    Enum,
    Integer,
    ForeignKey,
    Boolean,
    JSON,
    Text,
    UniqueConstraint
)
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, Mapped, mapped_column

import uuid
from datetime import datetime
from typing import List, Optional

from ..database import Base
from .enums import PostType, PostStatus, College


class Post(Base):
    __tablename__ = "posts"

    # ─── Core ────────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    type: Mapped[PostType] = mapped_column(Enum(PostType), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(500))

    # ─── Author ──────────────────────────────────────────────────────────
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    author = relationship("User", back_populates="posts")

    # ─── Timestamps ──────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    # ─── Targeting ───────────────────────────────────────────────────────
    tags: Mapped[List[str]] = mapped_column(JSONB, default=list)
    target_colleges: Mapped[List[College]] = mapped_column(JSONB, default=list)
    target_departments: Mapped[List[str]] = mapped_column(JSONB, default=list)

    # ─── Event ───────────────────────────────────────────────────────────
    event_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    event_time: Mapped[Optional[str]] = mapped_column(String(50))
    location: Mapped[Optional[str]] = mapped_column(String(200))

    # ─── Marketplace ─────────────────────────────────────────────────────
    price: Mapped[Optional[str]] = mapped_column(String(50))
    condition: Mapped[Optional[str]] = mapped_column(String(100))
    contact_info: Mapped[Optional[str]] = mapped_column(String(200))

    # ─── Link ────────────────────────────────────────────────────────────
    link_url: Mapped[Optional[str]] = mapped_column(String(500))
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # ─── Stats (denormalized) ─────────────────────────────────────────────
    views: Mapped[int] = mapped_column(Integer, default=0)
    saves_count: Mapped[int] = mapped_column(Integer, default=0)
    comments_count: Mapped[int] = mapped_column(Integer, default=0)
    upvotes_count: Mapped[int] = mapped_column(Integer, default=0)

    # ─── Community ───────────────────────────────────────────────────────
    community_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("communities.id")
    )
    community = relationship("Community", back_populates="posts")

    # ─── State ───────────────────────────────────────────────────────────
    status: Mapped[PostStatus] = mapped_column(
        Enum(PostStatus), default=PostStatus.ACTIVE
    )
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)

    # ─── Relationships ───────────────────────────────────────────────────
    comments = relationship(
        "Comment", back_populates="post", cascade="all, delete-orphan"
    )
    upvotes = relationship(
        "PostUpvote", back_populates="post", cascade="all, delete-orphan"
    )
    saves = relationship(
        "PostSave", back_populates="post", cascade="all, delete-orphan"
    )

    # ─── Derived fields ──────────────────────────────────────────────────
    @hybrid_property
    def stats(self) -> dict:
        return {
            "views": self.views,
            "comments": self.comments_count,
            "upvotes": self.upvotes_count,
        }

    def __repr__(self):
        return f"<Post {self.title[:50]}...>"


# ─────────────────────────────────────────────────────────────────────────
# Association tables
# ─────────────────────────────────────────────────────────────────────────

class PostUpvote(Base):
    __tablename__ = "post_upvotes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("posts.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    post = relationship("Post", back_populates="upvotes")
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="unique_post_upvote"),
    )


class PostSave(Base):
    __tablename__ = "post_saves"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("posts.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    post = relationship("Post", back_populates="saves")
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="unique_post_save"),
    )
