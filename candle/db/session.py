"""Async SQLAlchemy engine and session factory.

All database access goes through get_session(). Never create engine or sessions
outside this module.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from candle.config import settings


engine = create_async_engine(
    settings.database_url,
    echo=not settings.is_production,
    pool_pre_ping=True,
)

AsyncSessionFactory = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session, closing it when the context exits.

    Usage::

        async with get_session() as session:
            result = await session.execute(...)

    Yields:
        An AsyncSession bound to the configured engine.
    """
    async with AsyncSessionFactory() as session:
        yield session
