"""Normalizer — converts raw ccxt OHLCV responses into clean, typed DataFrames.

This module has no knowledge of exchanges or the database. Input in, DataFrame out.
"""

from typing import Any

import pandas as pd


RawOHLCV = list[list[Any]]  # ccxt returns [[timestamp_ms, o, h, l, c, v], ...]

OHLCV_COLUMNS: list[str] = ["timestamp", "open", "high", "low", "close", "volume"]


def normalize(raw: RawOHLCV) -> pd.DataFrame:
    """Convert a raw ccxt OHLCV list into a clean DataFrame.

    Args:
        raw: Raw output from ccxt's fetch_ohlcv — a list of
             [timestamp_ms, open, high, low, close, volume] rows.

    Returns:
        DataFrame with columns [timestamp, open, high, low, close, volume].
        - timestamp is UTC-aware datetime.
        - Numeric columns are float64.
        - Rows are sorted ascending by timestamp.
        - No duplicate timestamps.

    Raises:
        ValueError: If raw is empty or has an unexpected column count.
    """
    ...
