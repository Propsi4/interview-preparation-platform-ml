"""ORM models for search queries."""


from sqlalchemy import Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from ml.db.models.base import TimestampedBase


class VacancyModel(TimestampedBase):
    """Vacancies content captured for a search query."""

    __tablename__ = "vacancies"

    search_query_id: Mapped[int] = mapped_column(ForeignKey("search_queries.id"), nullable=False)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    company: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    scrapped: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
