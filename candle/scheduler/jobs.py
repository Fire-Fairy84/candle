"""APScheduler job definitions.

Wires the data fetcher, indicator computation, screener engine, and alert sender
into scheduled jobs. Entry point for running the scheduler manually during development:

    python -m candle.scheduler.jobs --once
"""

import argparse
import asyncio

from candle.config import settings


async def fetch_job() -> None:
    """Fetch OHLCV data for all active pairs and persist to the database.

    Iterates over all active TradingPairs, fetches candles from the corresponding
    exchange, and calls repository.save_candles(). Handles exchange errors per pair
    without stopping the full run.
    """
    ...


async def screen_job() -> None:
    """Load candles, compute indicators, evaluate rules, and send alerts.

    For each active TradingPair:
    1. Load recent candles from the database.
    2. Compute all required indicators.
    3. Run all active ScreenerRules through the engine.
    4. Persist and deliver any RuleMatches via the alerts layer.
    """
    ...


def build_scheduler():  # type: ignore[return]
    """Build and return a configured AsyncIOScheduler.

    Returns:
        An APScheduler AsyncIOScheduler with fetch_job and screen_job registered
        according to FETCH_INTERVAL_MINUTES and SCREEN_INTERVAL_MINUTES from settings.
    """
    ...


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Candle scheduler jobs")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run fetch and screen jobs once and exit (development mode)",
    )
    args = parser.parse_args()

    if args.once:
        asyncio.run(fetch_job())
        asyncio.run(screen_job())
    else:
        scheduler = build_scheduler()
        scheduler.start()
