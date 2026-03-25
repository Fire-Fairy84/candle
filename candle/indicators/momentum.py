"""Momentum indicators: RSI, Stochastic."""

import pandas as pd


def rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Compute Relative Strength Index.

    Args:
        df: OHLCV DataFrame with a "close" column.
        period: Lookback period in candles. Defaults to 14.

    Returns:
        Series of RSI values (0–100), aligned with df index.
        Leading values are NaN for the first `period` rows.
    """
    ...


def stochastic(
    df: pd.DataFrame,
    k_period: int = 14,
    d_period: int = 3,
) -> pd.DataFrame:
    """Compute Stochastic Oscillator (%K and %D lines).

    Args:
        df: OHLCV DataFrame with "high", "low", and "close" columns.
        k_period: %K lookback period. Defaults to 14.
        d_period: %D smoothing period. Defaults to 3.

    Returns:
        DataFrame with columns: stoch_k, stoch_d.
        Values range 0–100. Leading values are NaN.
    """
    ...
