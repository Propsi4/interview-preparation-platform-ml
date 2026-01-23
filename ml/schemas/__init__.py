"""Shared schema exports for cross-domain use."""

from ml.api.schemas import HealthResponse, ProgressResponse, ScrapeVacanciesRequest, ScrapeVacanciesResponse
from ml.conversation_history.schemas import ChatMessage, ChatSessionOverview
from ml.scrapers.schemas.vacancy import VacanciesOverview, Vacancy
from ml.agents.implementations.technical_interview.schemas import TechnicalInterviewResponse, InterviewTurnRequest

__all__ = [
    "HealthResponse",
    "ProgressResponse",
    "ScrapeVacanciesRequest",
    "ScrapeVacanciesResponse",
    "ChatMessage",
    "ChatSessionOverview",
    "Vacancy",
    "VacanciesOverview",
    "InterviewTurnRequest",
    "TechnicalInterviewResponse",
]
