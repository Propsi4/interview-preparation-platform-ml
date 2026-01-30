"""ORM models for search queries."""

from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import TimestampedBase


class SearchQueryModel(TimestampedBase):
    """User search queries."""

    __tablename__ = "search_queries"

    query: Mapped[str] = mapped_column(nullable=False)
    total_results: Mapped[int | None] = mapped_column(nullable=True)
