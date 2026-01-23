"""Chat sessions schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class ChatSessionsOverview(BaseModel):
    """Chat sessions overview schema."""

    session_id: str = Field(..., description="Session ID")
    title: str = Field(..., description="Session title")
    created_at: datetime = Field(..., description="Session creation timestamp")
    updated_at: datetime = Field(..., description="Session last update timestamp")
    message_count: int = Field(..., description="Number of messages in the session")
    price: float = Field(..., description="Session price")


class ChatMessage(BaseModel):
    """Chat message schema."""

    id: int = Field(..., description="Message ID")
    role: str = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    created_at: datetime = Field(..., description="Message creation timestamp")
