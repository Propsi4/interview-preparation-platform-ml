"""Schemas for technical interview agent."""

from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage
from typing import List


class TechnicalInterviewResponse(BaseModel):
    """Response schema for technical interview agent."""

    interview_finished: bool = Field(False, description="Whether the interview is complete")
    response: str = Field(..., description="Next question or final summary if interview is complete")


class InterviewTurnRequest(BaseModel):
    """Input for running an interview turn.

    Parameters
    ----------
    search_query_id : int
        Search query identifier.
    chat_history : List[BaseMessage]
        Conversation history for the interview.
    query : str
        Latest user input.
    """

    search_query_id: int = Field(..., description="Search query identifier")
    chat_history: List[BaseMessage] = Field(default_factory=list)
    query: str = Field(..., description="Latest user input")
