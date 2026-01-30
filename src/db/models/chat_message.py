"""SQLAlchemy ORM models for chat history storage."""

# Standart library imports
from typing import TYPE_CHECKING

# Thirdparty imports
from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import TimestampedBase

if TYPE_CHECKING:
    from src.db.models.chat_session import ChatSessionModel


class ChatMessageModel(TimestampedBase):
    """SQLAlchemy model for chat messages table."""

    __tablename__ = "chat_messages"

    session_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("chat_sessions.session_id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    session: Mapped["ChatSessionModel"] = relationship("ChatSessionModel", back_populates="messages")

    # Add check constraint for role
    __table_args__ = (
        CheckConstraint("role IN ('user', 'tool', 'assistant')", name="check_role"),
        Index("idx_chat_messages_session_id", "session_id"),
        Index("idx_chat_messages_created_at", "created_at"),
    )
