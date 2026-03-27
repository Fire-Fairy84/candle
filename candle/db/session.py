"""Async SQLAlchemy engine and session factory.

All database access goes through get_session(). Never create engine or sessions
outside this module.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

from candle.config import settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        db_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        _engine = create_async_engine(
            db_url,
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
