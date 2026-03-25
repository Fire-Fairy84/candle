"""APScheduler job definitions.

Wires the data fetcher, indicator computation, screener engine, and alert sender
into scheduled jobs. Entry point for running the scheduler manually during development:

    python -m candle.scheduler.jobs --once
"""

import argparse
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from functools import partial

import ccxt.async_support as ccxt
import pandas as pd
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from candle.alerts.telegram import send_alert
from candle.config import settings
from candle.data.exchange_factory import build_exchange
from candle.data.fetcher import fetch_ohlcv
from candle.db.models import ScreenerRule
from candle.db.repository import (
    get_active_pairs,
    get_active_rules,
    get_candles,
    get_recent_alert,
    mark_alert_sent,
    save_alert,
    save_candles,
)
from candle.db.session import AsyncSessionFactory
from candle.indicators.momentum import rsi
from candle.indicators.trend import ema
from candle.indicators.volume import vwap
from candle.screener import engine as screener_engine
from candle.screener.conditions import (
    ema_crossover,
    price_above_vwap,
    rsi_range,
    volume_spike,
)
from candle.screener.rules import Rule

logger = logging.getLogger(__name__)


def _build_rule(db_rule: ScreenerRule) -> Rule:
    """Convert a ScreenerRule DB model to a callable Rule.

    Reads the conditions JSON list and binds each entry to the corresponding
    condition primitive via functools.partial.

    Supported condition types and required keys:
        - ``ema_crossover``: ``fast`` (int), ``slow`` (int)
        - ``rsi_range``:     ``min`` (float), ``max`` (float)
        - ``price_above_vwap``: no extra keys
        - ``volume_spike``:  ``multiplier`` (float)

    Args:
        db_rule: An active ScreenerRule with a populated conditions JSON list.

    Returns:
        A Rule instance with bound callable conditions.

    Raises:
        ValueError: If a condition type is not recognised.
        KeyError: If a required parameter is missing from the condition dict.
    """
    condition_fns = []
    for cond in db_rule.conditions:
        ctype = cond["type"]
        if ctype == "ema_crossover":
            condition_fns.append(partial(ema_crossover, fast=cond["fast"], slow=cond["slow"]))
        elif ctype == "rsi_range":
            condition_fns.append(partial(rsi_range, min_val=cond["min"], max_val=cond["max"]))
        elif ctype == "price_above_vwap":
            condition_fns.append(price_above_vwap)
        elif ctype == "volume_spike":
            condition_fns.append(partial(volume_spike, multiplier=cond["multiplier"]))
        else:
            raise ValueError(f"unknown condition type: {ctype!r}")
    return Rule(name=db_rule.name, conditions=condition_fns)


def _compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add all standard indicator columns to a candle DataFrame in-place.

    Computes EMA 9, 21, 50, 200; RSI(14); and VWAP. These columns cover all
    condition primitives defined in candle.screener.conditions.

    Args:
        df: OHLCV DataFrame with open, high, low, close, volume columns.

    Returns:
        The same DataFrame with indicator columns added.
    """
    df["ema_9"] = ema(df, 9)
    df["ema_21"] = ema(df, 21)
    df["ema_50"] = ema(df, 50)
    df["ema_200"] = ema(df, 200)
    df["rsi"] = rsi(df)
    df["vwap"] = vwap(df)
    return df


async def fetch_job() -> None:
    """Fetch OHLCV data for all active pairs and persist to the database.

    Iterates over all active TradingPairs, fetches candles from the corresponding
    exchange, and calls repository.save_candles(). Handles exchange errors per pair
    without stopping the full run.
    """
    logger.info("fetch_job started")

    async with AsyncSessionFactory() as session:
        pairs = await get_active_pairs(session)

    logger.info("fetch_job: %d active pairs", len(pairs))

    for pair in pairs:
        exchange = build_exchange(pair.exchange.slug, settings)
        try:
            df = await fetch_ohlcv(exchange, pair.symbol, pair.timeframe)
            async with AsyncSessionFactory() as session:
                async with session.begin():
                    saved = await save_candles(session, pair.id, df)
            logger.info(
                "fetch: %s/%s %s — %d new candles",
                pair.exchange.slug,
                pair.symbol,
                pair.timeframe,
                saved,
            )
        except (ccxt.NetworkError, ccxt.ExchangeError, ccxt.RateLimitExceeded) as exc:
            logger.error(
                "exchange error for %s/%s %s: %s",
                pair.exchange.slug,
                pair.symbol,
                pair.timeframe,
                exc,
            )
        finally:
            await exchange.close()

    logger.info("fetch_job done")


async def screen_job() -> None:
    """Load candles, compute indicators, evaluate rules, and send alerts.

    For each active TradingPair:
    1. Load recent candles from the database.
    2. Compute all required indicators.
    3. Run all active ScreenerRules through the engine.
    4. Persist and deliver any RuleMatches via the alerts layer.

    Deduplication: an alert is skipped when the same rule already fired on the
    same pair within the last ``settings.alert_dedup_hours`` hours.
    """
    logger.info("screen_job started")

    async with AsyncSessionFactory() as session:
        pairs = await get_active_pairs(session)
        db_rules = await get_active_rules(session)

    if not db_rules:
        logger.info("screen_job: no active rules — skipping")
        return

    # Build callable Rules from DB models; skip malformed rules without crashing.
    rules: list[tuple[ScreenerRule, Rule]] = []
    for db_rule in db_rules:
        try:
            rules.append((db_rule, _build_rule(db_rule)))
        except (ValueError, KeyError) as exc:
            logger.error("skipping rule %r — invalid conditions: %s", db_rule.name, exc)

    if not rules:
        logger.warning("screen_job: all rules failed to build — skipping")
        return

    dedup_window = timedelta(hours=settings.alert_dedup_hours)
    callable_rules = [rule for _, rule in rules]

    for pair in pairs:
        async with AsyncSessionFactory() as session:
            df = await get_candles(session, pair.id, limit=500)

        if df.empty:
            logger.warning("no candles for %s/%s — skipping", pair.symbol, pair.timeframe)
            continue

        _compute_indicators(df)
        matches = screener_engine.run(callable_rules, df, pair.symbol, pair.timeframe)

        if not matches:
            continue

        now = datetime.now(tz=timezone.utc)
        for match in matches:
            db_rule = next(dr for dr, r in rules if r.name == match.rule.name)

            async with AsyncSessionFactory() as session:
                async with session.begin():
                    recent = await get_recent_alert(
                        session,
                        rule_id=db_rule.id,
                        pair_id=pair.id,
                        since=now - dedup_window,
                    )
                    if recent is not None:
                        logger.debug(
                            "dedup: skipping %s / %s (last alert at %s)",
                            pair.symbol,
                            db_rule.name,
                            recent.triggered_at,
                        )
                        continue

                    alert = await save_alert(
                        session,
                        rule_id=db_rule.id,
                        pair_id=pair.id,
                        triggered_at=now,
                        message=match.message,
                    )

            try:
                await send_alert(match)
                async with AsyncSessionFactory() as session:
                    async with session.begin():
                        await mark_alert_sent(session, alert.id)
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "failed to deliver alert for %s / %s: %s",
                    pair.symbol,
                    db_rule.name,
                    exc,
                )

    logger.info("screen_job done")


def build_scheduler() -> AsyncIOScheduler:
    """Build and return a configured AsyncIOScheduler.

    Returns:
        An APScheduler AsyncIOScheduler with fetch_job and screen_job registered
        according to FETCH_INTERVAL_MINUTES and SCREEN_INTERVAL_MINUTES from settings.
    """
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        fetch_job,
        trigger=IntervalTrigger(minutes=settings.fetch_interval_minutes),
        id="fetch_job",
        name="Fetch OHLCV candles",
        misfire_grace_time=300,
    )
    scheduler.add_job(
        screen_job,
        trigger=IntervalTrigger(minutes=settings.screen_interval_minutes),
        id="screen_job",
        name="Screen rules and send alerts",
        misfire_grace_time=300,
    )
    return scheduler


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
