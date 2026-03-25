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
    if slug not in SUPPORTED_EXCHANGES:
        raise ValueError(
            f"unsupported exchange '{slug}'. Must be one of {sorted(SUPPORTED_EXCHANGES)}"
        )

    exchange_class: type[ccxt.Exchange] = getattr(ccxt, slug)
    return exchange_class({"enableRateLimit": True, **_credentials(slug, settings)})


def _credentials(slug: str, settings: Settings) -> dict[str, str]:
    """Extract non-empty API credentials for the given exchange slug."""
    key_map: dict[str, tuple[str, str]] = {
        "binance": (settings.binance_api_key, settings.binance_api_secret),
        "kraken": (settings.kraken_api_key, settings.kraken_api_secret),
        "coinbase": (settings.coinbase_api_key, settings.coinbase_api_secret),
    }
    api_key, api_secret = key_map[slug]
    result: dict[str, str] = {}
    if api_key:
        result["apiKey"] = api_key
    if api_secret:
        result["secret"] = api_secret
    return result
