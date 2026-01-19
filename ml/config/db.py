"""
SQL (Postgres) database configuration settings.

Provides configuration for SQLAlchemy async engine using the asyncpg driver.
Environment variables use the prefix SQL_ (e.g., SQL_POSTGRES_URL).
"""

# Thirdparty imports
from typing import TYPE_CHECKING

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings
from sqlalchemy import URL

load_dotenv(override=True)


class ConnectionConfig(BaseSettings):
    """
    Connection configuration for the SQL database of the interview preparation platform.

    Parameters
    ----------
    DB_USER: str
        Database user
    DB_PASSWORD: str
        Database password
    DB_HOST: str
        Database host
    DB_PORT: int
        Database port
    DB_NAME: str
        Database name

    Examples
    --------
    >>> cfg = ConnectionConfig()
    >>> print(cfg.DB_USER)
    username
    """

    DB_USER: str = Field(
        description="Database user",
    )
    DB_PASSWORD: str = Field(
        description="Database password",
    )
    DB_SCHEMA: str = Field(
        default="public",
        description="Database schema",
    )
    DB_HOST: str = Field(
        description="Database host",
    )
    DB_PORT: int = Field(
        description="Database port",
    )
    DB_NAME: str = Field(
        description="Database name",
    )


class DatabaseSQLConfig(ConnectionConfig, BaseSettings):
    """
    SQL database configuration of the interview preparation platform.

    Parameters
    ----------
    DATABASE_URL : str
        SQLAlchemy URL (e.g., postgresql+psycopg2://user:pass@host:5432/db)
    ECHO : bool
        Echo SQL statements to the log
    POOL_SIZE : int
        Connection pool size
    MAX_OVERFLOW : int
        Max overflow connections beyond pool size
    POOL_TIMEOUT : int
        Seconds to wait for a connection from the pool
    """

    ECHO: bool = Field(default=False, description="Echo SQL statements to the log")
    POOL_SIZE: int = Field(default=10, description="Connection pool size")
    MAX_OVERFLOW: int = Field(default=10, description="Pool max overflow")
    POOL_TIMEOUT: int = Field(default=30, description="Pool timeout seconds")

    @property
    def DATABASE_URL(self) -> str:
        """Constructs the SQLAlchemy connection URL from individual components."""
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=self.DB_PORT,
            database=self.DB_NAME,
        )

    def get_engine(self) -> "AsyncEngine":
        """Return the global async SQLAlchemy engine.

        Returns
        -------
        AsyncEngine
            Initialized async SQLAlchemy engine.
        """
        from ml.db.engine import get_engine

        return get_engine(self)


if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine


db_config = DatabaseSQLConfig()
