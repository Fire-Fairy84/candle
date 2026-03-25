"""Tests for candle.indicators — trend, momentum, and volume indicators.

All tests use stable CSV fixtures with known inputs and expected outputs.
No random data. No real exchange calls.
"""

import pandas as pd
import pytest

from candle.indicators.trend import ema, sma, macd
from candle.indicators.momentum import rsi, stochastic
from candle.indicators.volume import vwap, obv, cvd


@pytest.fixture
def btc_4h() -> pd.DataFrame:
    """Load 100-candle BTC/USDT 4h fixture."""
    return pd.read_csv("tests/fixtures/btc_4h_100.csv", parse_dates=["timestamp"])


@pytest.fixture
def btc_crossover() -> pd.DataFrame:
    """Load fixture containing a known EMA crossover signal."""
    return pd.read_csv("tests/fixtures/btc_4h_crossover.csv", parse_dates=["timestamp"])


@pytest.fixture
def btc_overbought() -> pd.DataFrame:
    """Load fixture where RSI exceeds 70."""
    return pd.read_csv("tests/fixtures/btc_4h_overbought.csv", parse_dates=["timestamp"])


class TestEma:
    def test_returns_series_of_same_length(self, btc_4h):
        """EMA output length must match input DataFrame length."""
        ...

    def test_leading_values_are_nan(self, btc_4h):
        """First (period - 1) values should be NaN."""
        ...


class TestSma:
    def test_returns_series_of_same_length(self, btc_4h):
        ...

    def test_leading_values_are_nan(self, btc_4h):
        ...


class TestMacd:
    def test_returns_dataframe_with_three_columns(self, btc_4h):
        """MACD must return macd, macd_signal, macd_histogram columns."""
        ...

    def test_histogram_equals_macd_minus_signal(self, btc_4h):
        """Histogram must equal MACD line minus signal line."""
        ...


class TestRsi:
    def test_values_in_range_0_to_100(self, btc_4h):
        """All non-NaN RSI values must be within [0, 100]."""
        ...

    def test_detects_overbought_in_fixture(self, btc_overbought):
        """RSI must exceed 70 on the last candle of the overbought fixture."""
        ...


class TestStochastic:
    def test_returns_two_columns(self, btc_4h):
        ...

    def test_values_in_range_0_to_100(self, btc_4h):
        ...


class TestVwap:
    def test_no_nan_values(self, btc_4h):
        """VWAP should have no NaN values."""
        ...

    def test_within_high_low_range(self, btc_4h):
        """VWAP must always be between the session low and high."""
        ...


class TestObv:
    def test_returns_series_of_same_length(self, btc_4h):
        ...

    def test_increases_on_up_candle(self, btc_4h):
        """OBV must increase when close > previous close."""
        ...


class TestCvd:
    def test_returns_series_of_same_length(self, btc_4h):
        ...

    def test_positive_on_bullish_candle(self, btc_4h):
        """CVD delta must be positive when close > open."""
        ...
