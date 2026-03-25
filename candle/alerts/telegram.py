"""Telegram alert sender.

Formats RuleMatch objects into human-readable messages and delivers them
via the Telegram Bot API. Never called directly from the screener.
"""

from candle.config import settings
from candle.screener.engine import RuleMatch


async def send_alert(match: RuleMatch) -> None:
    """Format a RuleMatch and send it as a Telegram message.

    Uses TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from application settings.
    Silently skips sending if either setting is empty (development mode).

    Args:
        match: The RuleMatch to format and deliver.

    Raises:
        telegram.error.TelegramError: On API-level delivery failures.
    """
    ...


def format_message(match: RuleMatch) -> str:
    """Format a RuleMatch into a Telegram-ready message string.

    Args:
        match: The RuleMatch containing rule name, symbol, and timeframe.

    Returns:
        A formatted string suitable for sending as a Telegram message.
        Uses Markdown-compatible formatting.
    """
    ...
