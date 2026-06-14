"""
Shared test fixtures and configuration for the pytest suite.

This module provides mocks for SQLAlchemy async sessions, DSPy language models,
OpenAI client functions, and other environment variables to isolate unit tests
from external dependencies.
"""

# Standart library imports
from typing import Generator
from unittest.mock import AsyncMock, MagicMock, patch

# Thirdparty imports
import pytest
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Mock environment variables required by config classes to prevent initialization failures.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch utility.

    Returns
    -------
    None
    """
    monkeypatch.setenv("OPENAI_API_KEY", "sk-mock-key-for-testing-purposes-only-12345")
    monkeypatch.setenv("DB_USER", "postgres")
    monkeypatch.setenv("DB_PASSWORD", "postgres")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "test_db")


@pytest.fixture
def mock_async_session() -> MagicMock:
    """
    Provide a mocked SQLAlchemy AsyncSession.

    Returns
    -------
    MagicMock
        A mock object behaving like an AsyncSession.
    """
    session = MagicMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.get = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.close = AsyncMock()
    session.add = MagicMock()
    session.add_all = MagicMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def mock_db_connection(
    mock_async_session: MagicMock,
) -> Generator[MagicMock, None, None]:
    """
    Mock the connect_to_db context manager to yield the mock async session.

    Parameters
    ----------
    mock_async_session : MagicMock
        The mock async session fixture.

    Yields
    ------
    MagicMock
        The mock async session to be used in database calls.
    """
    with patch("src.db.engine.connect_to_db") as mock_connect_engine, patch(
        "src.conversation_history.manager.connect_to_db"
    ) as mock_connect_manager:
        # connect_to_db is an async context manager, so its __aenter__ returns the session
        context_mock = MagicMock()
        context_mock.__aenter__ = AsyncMock(return_value=mock_async_session)
        context_mock.__aexit__ = AsyncMock(return_value=None)
        mock_connect_engine.return_value = context_mock
        mock_connect_manager.return_value = context_mock
        yield mock_async_session
