"""SQLAlchemy ORM models for chat history storage."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ml.db.models.base import TimestampedBase

if TYPE_CHECKING:
    from ml.db.models.chat_message import ChatMessageModel


class ChatSessionModel(TimestampedBase):
    """SQLAlchemy model for chat sessions table."""

    __tablename__ = "chat_sessions"

    session_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    interview_finished: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    messages: Mapped[list["ChatMessageModel"]] = relationship(
        "ChatMessageModel",
        back_populates="session",
        cascade="all, delete-orphan",
    )
