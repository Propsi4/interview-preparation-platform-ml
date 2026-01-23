"""Chat sessions schemas."""

from typing import List
from datetime import datetime

from pydantic import BaseModel, Field


class ChatSessionOverviewSchema(BaseModel):
    """Chat sessions overview schema."""

    session_id: str = Field(..., description="Session ID")
    title: str = Field(..., description="Session title")
    created_at: datetime = Field(..., description="Session creation timestamp")
    updated_at: datetime = Field(..., description="Session last update timestamp")
    total_messages: int = Field(..., description="Number of messages in the session")
    price: float = Field(..., description="Session price")


class ChatMessageSchema(BaseModel):
    """Chat message schema."""

    id: int = Field(..., description="Message ID")
    role: str = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    created_at: datetime = Field(..., description="Message creation timestamp")


class ChatSessionDetailsSchema(ChatSessionOverviewSchema):
    """Chat session details schema."""

    messages: List[ChatMessageSchema] = Field(..., description="List of messages in the session")
