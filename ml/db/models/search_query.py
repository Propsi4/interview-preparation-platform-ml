"""ORM models for search queries."""

from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column

from ml.db.models.base import TimestampedBase


class SearchQuery(TimestampedBase):
    """User search queries for indexation."""

    __tablename__ = "search_queries"

    query: Mapped[str] = mapped_column(nullable=False)
    total_results: Mapped[int | None] = mapped_column(nullable=True)
