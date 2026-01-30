"""Shared schema exports for cross-domain use."""

from ml.api.schemas import (
    HealthResponseSchema,
    ProgressResponseSchema,
    ScrapeVacanciesRequestSchema,
    ScrapeVacanciesResponseSchema,
)
from ml.conversation_history.schemas import ChatMessageSchema, ChatSessionOverviewSchema
from ml.scrapers.schemas.vacancy import VacanciesOverviewSchema, VacancySchema
from ml.agents.implementations.technical_interview.schemas import (
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
