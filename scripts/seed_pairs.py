"""Seed additional trading pairs on Binance.

Idempotent: safe to run multiple times. Skips pairs that already exist.

Usage:
    python scripts/seed_pairs.py
"""

import asyncio

from sqlalchemy import select

from candle.db.models import Exchange, TradingPair
from candle.db.session import AsyncSessionFactory

PAIRS_TO_SEED = [
    ("ETH/USDT", "4h"),
    ("SOL/USDT", "4h"),
    ("BNB/USDT", "4h"),
    ("BTC/USDT", "1d"),
    ("ETH/USDT", "1d"),
]


async def seed() -> None:
    async with AsyncSessionFactory() as session:
        async with session.begin():
            result = await session.execute(
                select(Exchange).where(Exchange.slug == "binance")
            )
            exchange = result.scalar_one_or_none()
            if exchange is None:
                print("ERROR: Binance exchange not found. Run seed.py first.")
                return
            print(f"  Exchange: {exchange.name} (id={exchange.id})")

            for symbol, timeframe in PAIRS_TO_SEED:
                result = await session.execute(
                    select(TradingPair).where(
                        TradingPair.exchange_id == exchange.id,
                        TradingPair.symbol == symbol,
                        TradingPair.timeframe == timeframe,
                    )
                )
                pair = result.scalar_one_or_none()
                if pair is None:
                    pair = TradingPair(
                        exchange_id=exchange.id,
                        symbol=symbol,
                        timeframe=timeframe,
                        active=True,
                    )
                    session.add(pair)
                    await session.flush()
                    print(f"  Created pair: {pair.symbol} {pair.timeframe} (id={pair.id})")
                else:
                    print(f"  Pair already exists: {pair.symbol} {pair.timeframe} (id={pair.id})")

    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
