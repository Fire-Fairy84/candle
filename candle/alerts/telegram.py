"""Telegram alert sender.

Formats RuleMatch objects into human-readable messages and delivers them
via the Telegram Bot API. Never called directly from the screener.
"""

import logging

from telegram import Bot
from telegram.error import TelegramError  # noqa: F401 — re-exported for callers

from candle.config import settings
from candle.screener.engine import RuleMatch

logger = logging.getLogger(__name__)


def format_message(match: RuleMatch) -> str:
    """Format a RuleMatch into a Telegram-ready message string.

    Args:
        match: The RuleMatch containing rule name, symbol, and timeframe.

    Returns:
        A formatted string suitable for sending as a Telegram message.
        Uses Markdown-compatible formatting.
    """
    return (
        f"\U0001f525 *{match.symbol}* `{match.timeframe}`\n"
        f"Rule triggered: *{match.rule.name}*\n"
        f"{match.message}"
    )


async def send_alert(match: RuleMatch, bot: Bot | None = None) -> None:
    """Format a RuleMatch and send it as a Telegram message.

    Uses TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from application settings.
    Silently skips sending if either setting is empty (development mode).

    If bot is provided it is used directly; otherwise a Bot instance is created
    from settings. Pass a bot explicitly to reuse a single connection across
    multiple calls in the same job run, or to inject a mock in tests.

    Args:
        match: The RuleMatch to format and deliver.
        bot: Optional pre-configured Bot instance.

    Raises:
        telegram.error.TelegramError: On API-level delivery failures.
    """
    if bot is None:
        if not settings.telegram_bot_token:
            logger.warning("TELEGRAM_BOT_TOKEN not configured — skipping alert delivery")
            return
        bot = Bot(token=settings.telegram_bot_token)

    text = format_message(match)
    await bot.send_message(
        chat_id=settings.telegram_chat_id,
        text=text,
        parse_mode="Markdown",
    )
    logger.info("alert sent: %s / %s [%s]", match.symbol, match.rule.name, match.timeframe)
