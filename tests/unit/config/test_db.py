"""
Unit tests for the Database SQL configuration settings.

Verifies that the database connection parameters are correctly parsed,
the SQLAlchemy connection URL is properly constructed, and the engine
instantiation is triggered correctly.
"""

from typing import Any
from unittest.mock import MagicMock, patch

# Thirdparty imports
import pytest

# Local imports
from src.config.db import DatabaseSQLConfig, db_config


class TestDatabaseSQLConfig:
    """Test suite for the SQL database configuration settings."""

    def test_db_config_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        Verify that DatabaseSQLConfig parses configuration from env variables.

        Parameters
        ----------
        monkeypatch : pytest.MonkeyPatch
            Pytest monkeypatch utility.

        Returns
        -------
        None
        """
        monkeypatch.setenv("DB_USER", "postgres")
        monkeypatch.setenv("DB_PASSWORD", "postgres")
        monkeypatch.setenv("DB_HOST", "localhost")
        monkeypatch.setenv("DB_PORT", "5432")
        monkeypatch.setenv("DB_NAME", "test_db")
        monkeypatch.setenv("DB_SCHEMA", "public")

        config = DatabaseSQLConfig(
            DB_USER="postgres",
            DB_PASSWORD="postgres",
            DB_HOST="localhost",
            DB_PORT=5432,
            DB_NAME="test_db",
        )
        assert config.DB_USER == "postgres"
        assert config.DB_PASSWORD == "postgres"
        assert config.DB_HOST == "localhost"
        assert config.DB_PORT == 5432
        assert config.DB_NAME == "test_db"
        assert config.DB_SCHEMA == "public"

    def test_database_url_property(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        Verify that the DATABASE_URL property builds a correct SQLAlchemy connection URL.

        Parameters
        ----------
        monkeypatch : pytest.MonkeyPatch
            Pytest monkeypatch utility.

        Returns
        -------
        None
        """
        monkeypatch.setenv("DB_USER", "postgres")
        monkeypatch.setenv("DB_PASSWORD", "postgres")
        monkeypatch.setenv("DB_HOST", "localhost")
        monkeypatch.setenv("DB_PORT", "5432")
        monkeypatch.setenv("DB_NAME", "test_db")
        monkeypatch.setenv("DB_SCHEMA", "public")

        config = DatabaseSQLConfig(
            DB_USER="postgres",
            DB_PASSWORD="postgres",
            DB_HOST="localhost",
            DB_PORT=5432,
            DB_NAME="test_db",
        )
        url: Any = config.DATABASE_URL
        assert url.drivername == "postgresql+asyncpg"
        assert url.username == "postgres"
        assert url.password == "postgres"
        assert url.host == "localhost"
        assert url.port == 5432
        assert url.database == "test_db"

    def test_get_engine(self) -> None:
        """
        Verify that get_engine retrieves the configured async SQLAlchemy engine.

        Returns
        -------
        None
        """
        mock_engine = MagicMock()
        with patch("src.db.engine.get_engine", return_value=mock_engine) as mock_get_engine:
            engine = db_config.get_engine()
            assert engine == mock_engine
            mock_get_engine.assert_called_once_with(db_config)
