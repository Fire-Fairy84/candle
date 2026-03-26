"""Seed script — inserts initial data for local development.

Idempotent: safe to run multiple times. Skips records that already exist.

Usage:
    python scripts/seed.py
"""

import asyncio

from sqlalchemy import select

from candle.db.models import Exchange, ScreenerRule, TradingPair
from candle.db.session import AsyncSessionFactory


async def seed() -> None:
    async with AsyncSessionFactory() as session:
        async with session.begin():
            # --- Exchange: Binance ---
            result = await session.execute(
                select(Exchange).where(Exchange.slug == "binance")
            )
            exchange = result.scalar_one_or_none()
            if exchange is None:
                exchange = Exchange(name="Binance", slug="binance")
                session.add(exchange)
                await session.flush()
                print(f"  Created exchange: {exchange.name} (id={exchange.id})")
            else:
                print(f"  Exchange already exists: {exchange.name} (id={exchange.id})")

            # --- TradingPair: BTC/USDT 4h on Binance ---
            result = await session.execute(
                select(TradingPair).where(
                    TradingPair.exchange_id == exchange.id,
                    TradingPair.symbol == "BTC/USDT",
                    TradingPair.timeframe == "4h",
                )
            )
            pair = result.scalar_one_or_none()
            if pair is None:
                pair = TradingPair(
                    exchange_id=exchange.id,
                    symbol="BTC/USDT",
                    timeframe="4h",
                    active=True,
                )
                session.add(pair)
                await session.flush()
                print(f"  Created pair: {pair.symbol} {pair.timeframe} (id={pair.id})")
            else:
                print(f"  Pair already exists: {pair.symbol} {pair.timeframe} (id={pair.id})")

            # --- ScreenerRule: EMA Crossover 9/21 ---
            result = await session.execute(
                select(ScreenerRule).where(ScreenerRule.name == "EMA Crossover 9/21")
            )
            rule = result.scalar_one_or_none()
            if rule is None:
                rule = ScreenerRule(
                    name="EMA Crossover 9/21",
                    description="Fast EMA (9) crosses above slow EMA (21) — bullish momentum signal.",
                    conditions=[{"type": "ema_crossover", "fast": 9, "slow": 21}],
                    active=True,
                )
                session.add(rule)
                await session.flush()
                print(f"  Created rule: {rule.name} (id={rule.id})")
            else:
                print(f"  Rule already exists: {rule.name} (id={rule.id})")

    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
