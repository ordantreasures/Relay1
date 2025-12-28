from sqlalchemy import String, DateTime, Enum, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from ..database import Base
import enum


class NotificationType(str, enum.Enum):
    REPLY = "REPLY"
    SYSTEM = "SYSTEM"
    REMINDER = "REMINDER"
    UPVOTE = "UPVOTE"
    NEW_POST = "NEW_POST"
    COMMUNITY_INVITE = "COMMUNITY_INVITE"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType), nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    read: Mapped[bool] = mapped_column(Boolean, default=False)

    # Target relationships
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    post_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("posts.id"), nullable=True)
    comment_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("comments.id"), nullable=True)
    community_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("communities.id"), nullable=True)

    # Metadata
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # Additional data

    # Timestamps
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User")
    post = relationship("Post")
    comment = relationship("Comment")
    community = relationship("Community")

    def __repr__(self):
        return f"<Notification {self.type}: {self.message[:50]}...>"