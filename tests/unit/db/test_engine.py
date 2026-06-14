"""
Unit tests for the database engine and session helper module in src/db/engine.py.

Verifies that the SQLAlchemy async engine and sessionmaker are configured
and initialized correctly, and that the async context manager manages session life cycles.
"""

# Standart library imports
from unittest.mock import AsyncMock, MagicMock, patch

# Thirdparty imports
import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

# Local imports
from src.db.engine import connect_to_db, get_engine, get_sessionmaker


class TestDBEngine:
    """Test suite for the database engine and session helper functions."""

    def test_get_engine(self) -> None:
        """
        Verify that get_engine constructs an AsyncEngine with expected parameters.

        Returns
        -------
        None
        """
        with patch("src.db.engine.create_async_engine") as mock_create_engine:
            mock_engine = MagicMock(spec=AsyncEngine)
            mock_create_engine.return_value = mock_engine

            engine = get_engine()

            assert engine == mock_engine
            mock_create_engine.assert_called_once()
            args, kwargs = mock_create_engine.call_args
            # Verify drivername and parameters passed to create_async_engine
            assert args[0].drivername == "postgresql+asyncpg"
            assert kwargs["echo"] is False
            assert kwargs["pool_size"] == 10

    def test_get_sessionmaker(self) -> None:
        """
        Verify that get_sessionmaker returns a session factory bound to the engine.

        Returns
        -------
        None
        """
        with patch("src.db.engine.get_engine") as mock_get_engine, patch(
            "src.db.engine.async_sessionmaker"
        ) as mock_sessionmaker_cls:

            mock_engine = MagicMock(spec=AsyncEngine)
            mock_get_engine.return_value = mock_engine
            mock_factory = MagicMock(spec=async_sessionmaker)
            mock_sessionmaker_cls.return_value = mock_factory

            sessionmaker = get_sessionmaker()

            assert sessionmaker == mock_factory
            mock_get_engine.assert_called_once()
            mock_sessionmaker_cls.assert_called_once_with(bind=mock_engine, expire_on_commit=False)

    @pytest.mark.asyncio
    async def test_connect_to_db_lifecycle(self) -> None:
        """
        Verify that connect_to_db correctly yields a session and closes it on exit.

        Returns
        -------
        None
        """
        mock_session = MagicMock(spec=AsyncSession)
        mock_session.close = AsyncMock()

        # Mock sessionmaker context manager
        mock_sessionmaker = MagicMock()
        context_mock = MagicMock()
        context_mock.__aenter__ = AsyncMock(return_value=mock_session)
        context_mock.__aexit__ = AsyncMock(return_value=None)
        mock_sessionmaker.return_value = context_mock

        with patch("src.db.engine.get_sessionmaker", return_value=mock_sessionmaker):
            async with connect_to_db() as yielded_session:
                assert yielded_session == mock_session

            # Verify that session close is called on exit
            mock_session.close.assert_called_once()
