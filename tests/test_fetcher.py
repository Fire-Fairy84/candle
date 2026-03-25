"""Tests for candle.data.fetcher."""

import pytest
import pandas as pd

from candle.data.fetcher import fetch_ohlcv, SUPPORTED_TIMEFRAMES


class TestFetchOhlcv:
    async def test_returns_dataframe_with_expected_columns(self, mock_exchange):
        """fetch_ohlcv should return a DataFrame with the standard OHLCV columns."""
        ...

    async def test_raises_on_unsupported_timeframe(self, mock_exchange):
        """fetch_ohlcv should raise ValueError for timeframes not in SUPPORTED_TIMEFRAMES."""
        ...

    async def test_handles_network_error(self, mock_exchange):
        """fetch_ohlcv should propagate ccxt.NetworkError for the caller to handle."""
        ...

    async def test_handles_rate_limit_exceeded(self, mock_exchange):
        """fetch_ohlcv should propagate ccxt.RateLimitExceeded."""
        ...
