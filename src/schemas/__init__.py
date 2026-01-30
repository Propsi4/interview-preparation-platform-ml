"""Shared schema exports for cross-domain use."""

from src.api.schemas import (
    HealthResponseSchema,
    ProgressResponseSchema,
    ScrapeVacanciesRequestSchema,
    ScrapeVacanciesResponseSchema,
)
from src.conversation_history.schemas import ChatMessageSchema, ChatSessionOverviewSchema
from src.scrapers.schemas.vacancy import VacanciesOverviewSchema, VacancySchema
from src.agents.implementations.technical_interview.schemas import (
    TechnicalInterviewResponseSchema,
    InterviewTurnRequestSchema,
)

__all__ = [
    "HealthResponseSchema",
    "ProgressResponseSchema",
    "ScrapeVacanciesRequestSchema",
    "ScrapeVacanciesResponseSchema",
    "ChatMessageSchema",
    "ChatSessionOverviewSchema",
    "VacancySchema",
    "VacanciesOverviewSchema",
    "InterviewTurnRequestSchema",
    "TechnicalInterviewResponseSchema",
]
