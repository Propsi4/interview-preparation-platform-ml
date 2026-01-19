"""ORM models for search queries."""

from __future__ import annotations

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from ml.db.models.base import TimestampedBase


class Vacancy(TimestampedBase):
    """Vacancies content captured for a search query."""

    __tablename__ = "vacancies"

    search_query_id: Mapped[int] = mapped_column(ForeignKey("search_queries.id"), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    company: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
