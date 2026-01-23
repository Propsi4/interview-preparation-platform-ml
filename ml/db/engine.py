"""Async SQLAlchemy engine and session helpers."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from ml.config.db import DatabaseSQLConfig, db_config


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
    resolved_config = config or db_config
    engine = create_async_engine(
        resolved_config.DATABASE_URL,
        echo=resolved_config.ECHO,
        pool_size=resolved_config.POOL_SIZE,
        max_overflow=resolved_config.MAX_OVERFLOW,
        pool_timeout=resolved_config.POOL_TIMEOUT,
    )
    return engine


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
    engine = get_engine(config)
    sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)
    return sessionmaker


@asynccontextmanager
async def connect_to_db() -> AsyncGenerator[AsyncSession]:
    """
    Get database session context manager.

    Yields
    ------
    AsyncSession
        SQLAlchemy database session.

    Notes
    -----
    The session WILL be automatically closed when exiting the context manager
    (`async with connect_to_db() as session: ...`). You do NOT need to close it manually.
    """
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        try:
            yield session
        finally:
            await session.close()
