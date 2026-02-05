"""ORM models for unified requirements."""

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import TimestampedBase


class UnifiedRequirementsModel(TimestampedBase):
    """Unified requirements for a search query."""

    __tablename__ = "unified_requirements"

    search_query_id: Mapped[int] = mapped_column(ForeignKey("search_queries.id", ondelete="CASCADE"), nullable=False)
    requirements: Mapped[str] = mapped_column(Text, nullable=False)
