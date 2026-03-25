"""Repository — all database queries for the Candle application.

No SQLAlchemy queries exist outside this module. Business logic must not live here;
repositories only translate between domain objects and database rows.
"""

from datetime import datetime

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from candle.db.models import Candle, Exchange, TradingPair, Alert, ScreenerRule


async def get_exchange_by_slug(session: AsyncSession, slug: str) -> Exchange | None:
    """Return an Exchange by its slug, or None if not found.

    Args:
        session: Active async database session.
        slug: Exchange slug, e.g. "binance".

    Returns:
        The Exchange instance, or None.
    """
    ...


async def get_active_pairs(session: AsyncSession) -> list[TradingPair]:
    """Return all active TradingPairs with their exchanges eagerly loaded.

    Args:
        session: Active async database session.

    Returns:
        List of active TradingPair instances.
    """
    ...


async def save_candles(
    session: AsyncSession,
    pair_id: int,
    df: pd.DataFrame,
) -> int:
    """Upsert OHLCV candles from a DataFrame into the database.

    Skips rows whose (pair_id, timestamp) already exist.

    Args:
        session: Active async database session.
        pair_id: ID of the TradingPair these candles belong to.
        df: Normalized DataFrame with columns [timestamp, open, high, low, close, volume].

    Returns:
        Number of new rows inserted.
    """
    ...


async def get_candles(
    session: AsyncSession,
    pair_id: int,
    limit: int = 500,
    since: datetime | None = None,
) -> pd.DataFrame:
    """Fetch candles for a pair from the database as a DataFrame.

    Args:
        session: Active async database session.
        pair_id: ID of the TradingPair to fetch candles for.
        limit: Maximum number of candles to return. Defaults to 500.
        since: If provided, only return candles at or after this UTC datetime.

    Returns:
        DataFrame with columns [timestamp, open, high, low, close, volume],
        sorted ascending by timestamp.
    """
    ...


async def save_alert(
    session: AsyncSession,
    rule_id: int,
    pair_id: int,
    triggered_at: datetime,
    message: str,
) -> Alert:
    """Persist a new Alert record and return it.

    Args:
        session: Active async database session.
        rule_id: ID of the ScreenerRule that triggered.
        pair_id: ID of the TradingPair that triggered the rule.
        triggered_at: UTC datetime when the rule fired.
        message: Human-readable alert description.

    Returns:
        The newly created Alert instance (unsent).
    """
    ...


async def get_active_rules(session: AsyncSession) -> list[ScreenerRule]:
    """Return all active ScreenerRule records.

    Args:
        session: Active async database session.

    Returns:
        List of active ScreenerRule instances.
    """
    ...
