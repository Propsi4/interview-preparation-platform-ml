"""SQLAlchemy ORM model for vacancy interview scores."""

# Standart library imports
from typing import TYPE_CHECKING

# Thirdparty imports
from sqlalchemy import ForeignKey, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Local imports
from src.db.models.base import TimestampedBase

if TYPE_CHECKING:
    from src.db.models.search_query import SearchQueryModel
    from src.db.models.chat_session import ChatSessionModel


class VacancyInterviewScoreModel(TimestampedBase):
    """SQLAlchemy model for vacancy interview scores."""

    __tablename__ = "vacancy_interview_scores"

    search_query_id: Mapped[int] = mapped_column(ForeignKey("search_queries.id"), nullable=False)
    chat_session_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("chat_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    strong_sides: Mapped[str | None] = mapped_column(Text, nullable=True)
    weak_sides: Mapped[str | None] = mapped_column(Text, nullable=True)

    search_query: Mapped["SearchQueryModel"] = relationship("SearchQueryModel")
    chat_session: Mapped["ChatSessionModel"] = relationship("ChatSessionModel")
