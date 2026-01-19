"""ORM model package exports."""

from .base import Base, TimestampedBase
from .search_query import SearchQuery
from .vacancies import Vacancy

metadata = Base.metadata

__all__ = [
    "Base",
    "TimestampedBase",
    "metadata",
    "SearchQuery",
    "Vacancy",
]
