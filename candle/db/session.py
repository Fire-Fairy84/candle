"""Async SQLAlchemy engine and session factory.

All database access goes through get_session(). Never create engine or sessions
outside this module.
"""

import logging
import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from candle.config import settings

logger = logging.getLogger(__name__)

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None

# Variable names to try, in priority order.
# Railway exposes DATABASE_URL and DATABASE_PRIVATE_URL from the Postgres plugin.
_DB_URL_VARS = (
    "CANDLE_DB_URL",
    "DATABASE_PRIVATE_URL",
    "DATABASE_URL",
)


def _resolve_db_url() -> str:
    """Find the database URL from environment variables or PG* components.

    Tries CANDLE_DB_URL, DATABASE_PRIVATE_URL, and DATABASE_URL in order.
    Falls back to building the URL from PGHOST/PGPORT/PGUSER/PGPASSWORD/PGDATABASE.
    Skips empty strings.

    Returns:
        A postgresql+asyncpg:// connection URL.

    Raises:
        RuntimeError: If no database URL can be resolved.
    """
    # 1. Try well-known URL variables
    for var in _DB_URL_VARS:
        url = os.environ.get(var, "")
        if url:
            logger.info("Database URL resolved from %s", var)
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # 2. Try building from individual PG* variables (Railway always exposes these)
    host = os.environ.get("PGHOST", "")
    port = os.environ.get("PGPORT", "5432")
    user = os.environ.get("PGUSER", "")
    password = os.environ.get("PGPASSWORD", "")
    database = os.environ.get("PGDATABASE", "")
    if host and user and password and database:
        logger.info("Database URL built from PGHOST/PGUSER/PGPASSWORD/PGDATABASE")
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"

    # 3. Last resort: check if pydantic-settings found it via .env file
    if settings.candle_db_url:
        return settings.candle_db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    raise RuntimeError(
        "No database URL found. Set one of: CANDLE_DB_URL, DATABASE_PRIVATE_URL, "
        "DATABASE_URL, or PGHOST+PGUSER+PGPASSWORD+PGDATABASE."
    )


def _get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            _resolve_db_url(),
            echo=not settings.is_production,
            pool_pre_ping=True,
        )
    return _engine


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            _get_engine(),
            expire_on_commit=False,
            class_=AsyncSession,
        )
    return _session_factory


def AsyncSessionFactory() -> AsyncSession:
    """Return a new async session from the lazily-initialised factory."""
    return _get_session_factory()()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session, closing it when the context exits.

    Usage::

        async with get_session() as session:
            result = await session.execute(...)

    Yields:
        An AsyncSession bound to the configured engine.
    """
    async with _get_session_factory()() as session:
        yield session
