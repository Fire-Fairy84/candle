"""Tests for candle.alerts.telegram."""

import pytest

from candle.alerts.telegram import format_message, send_alert
from candle.screener.engine import RuleMatch
from candle.screener.rules import Rule


@pytest.fixture
def sample_match() -> RuleMatch:
    """A RuleMatch for use in alert formatting and delivery tests."""
    rule = Rule(name="EMA Crossover + RSI Oversold")
    return RuleMatch(
        rule=rule,
        symbol="BTC/USDT",
        timeframe="4h",
        message="EMA 9 crossed above EMA 21; RSI at 32",
    )


class TestFormatMessage:
    def test_includes_symbol(self, sample_match):
        """Formatted message must include the trading pair symbol."""
        ...

    def test_includes_rule_name(self, sample_match):
        """Formatted message must include the rule name."""
        ...

    def test_includes_timeframe(self, sample_match):
        """Formatted message must include the timeframe."""
        ...

    def test_returns_string(self, sample_match):
        ...


class TestSendAlert:
    async def test_calls_telegram_with_formatted_message(self, sample_match, mock_telegram, mocker):
        """send_alert must call the Telegram bot with the formatted message."""
        ...

    async def test_skips_send_when_token_not_configured(self, sample_match, mocker):
        """send_alert must not call the Telegram API when bot token is empty."""
        ...
