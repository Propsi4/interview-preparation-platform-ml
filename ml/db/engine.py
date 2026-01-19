"""Async SQLAlchemy engine and session helpers."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from ml.config.db import DatabaseSQLConfig, db_config

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine(config: DatabaseSQLConfig | None = None) -> AsyncEngine:
    """
    Return a singleton async SQLAlchemy engine.

    Parameters
    ----------
    config : DatabaseSQLConfig | None
        Optional database configuration. If omitted, the global config is used.

    Returns
    -------
    AsyncEngine
        Initialized async SQLAlchemy engine.
    """
    global _engine

    if _engine is not None:
        return _engine

    resolved_config = config or db_config
    _engine = create_async_engine(
        resolved_config.DATABASE_URL,
        echo=resolved_config.ECHO,
        pool_size=resolved_config.POOL_SIZE,
        max_overflow=resolved_config.MAX_OVERFLOW,
        pool_timeout=resolved_config.POOL_TIMEOUT,
    )
    return _engine


def get_sessionmaker(config: DatabaseSQLConfig | None = None) -> async_sessionmaker[AsyncSession]:
    """
    Return a singleton async sessionmaker bound to the engine.

    Parameters
    ----------
    config : DatabaseSQLConfig | None
        Optional database configuration. If omitted, the global config is used.

    Returns
    -------
    async_sessionmaker[AsyncSession]
        Session factory bound to the async engine.
    """
    global _sessionmaker

    if _sessionmaker is not None:
        return _sessionmaker

    engine = get_engine(config)
    _sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)
    return _sessionmaker


async def close_engine() -> None:
    """Dispose the global async engine."""
    global _engine, _sessionmaker

    if _engine is None:
        return

    await _engine.dispose()
    _engine = None
    _sessionmaker = None
