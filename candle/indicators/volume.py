"""Volume indicators: VWAP, OBV, CVD."""

import pandas as pd


def vwap(df: pd.DataFrame) -> pd.Series:
    """Compute Volume-Weighted Average Price.

    Calculated as cumulative (typical_price * volume) / cumulative volume,
    where typical_price = (high + low + close) / 3.

    Args:
        df: OHLCV DataFrame with "high", "low", "close", and "volume" columns.

    Returns:
        Series of VWAP values, aligned with df index. No NaN values.
    """
    ...


def obv(df: pd.DataFrame) -> pd.Series:
    """Compute On-Balance Volume.

    Args:
        df: OHLCV DataFrame with "close" and "volume" columns.

    Returns:
        Series of cumulative OBV values, aligned with df index.
    """
    ...


def cvd(df: pd.DataFrame) -> pd.Series:
    """Compute Cumulative Volume Delta (approximation via close vs open).

    Positive delta when close > open (buying pressure),
    negative when close < open (selling pressure).

    Args:
        df: OHLCV DataFrame with "open", "close", and "volume" columns.

    Returns:
        Series of cumulative volume delta values, aligned with df index.
    """
    ...
