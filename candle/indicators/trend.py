"""Trend indicators: EMA, SMA, MACD."""

import pandas as pd


def ema(df: pd.DataFrame, period: int, column: str = "close") -> pd.Series:
    """Compute Exponential Moving Average.

    Args:
        df: OHLCV DataFrame with at least the target column.
        period: Lookback period in candles.
        column: Column to compute EMA on. Defaults to "close".

    Returns:
        Series of EMA values, aligned with df index. Leading values are NaN.
    """
    ...


def sma(df: pd.DataFrame, period: int, column: str = "close") -> pd.Series:
    """Compute Simple Moving Average.

    Args:
        df: OHLCV DataFrame with at least the target column.
        period: Lookback period in candles.
        column: Column to compute SMA on. Defaults to "close".

    Returns:
        Series of SMA values, aligned with df index. Leading values are NaN.
    """
    ...


def macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """Compute MACD line, signal line, and histogram.

    Args:
        df: OHLCV DataFrame with a "close" column.
        fast: Fast EMA period. Defaults to 12.
        slow: Slow EMA period. Defaults to 26.
        signal: Signal line EMA period. Defaults to 9.

    Returns:
        DataFrame with columns: macd, macd_signal, macd_histogram.
        Leading values are NaN until enough data is available.
    """
    ...
