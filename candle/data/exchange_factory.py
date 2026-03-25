"""Factory for building read-only ccxt exchange instances from application config."""

import ccxt.async_support as ccxt

from candle.config import Settings


SUPPORTED_EXCHANGES: frozenset[str] = frozenset({"binance", "kraken", "coinbase"})


def build_exchange(slug: str, settings: Settings) -> ccxt.Exchange:
    """Return a configured, read-only ccxt async exchange instance.

    Args:
        slug: Exchange identifier. Must be one of SUPPORTED_EXCHANGES.
        settings: Application settings containing optional API credentials.

    Returns:
        An async ccxt Exchange instance. API keys are set only when present in
        settings; public OHLCV endpoints work without credentials.

    Raises:
        ValueError: If slug is not in SUPPORTED_EXCHANGES.
    """
    ...
