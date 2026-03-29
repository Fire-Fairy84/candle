"""Screener engine — evaluates a list of rules against indicator output.

The engine is stateless. It receives DataFrames and rules, and returns matches.
It has no knowledge of the database or the alert delivery layer.
"""

from dataclasses import dataclass

import pandas as pd

from candle.screener.rules import Rule


@dataclass
class RuleMatch:
    """Represents a rule that fired on a specific symbol.

    Attributes:
        rule: The Rule that was triggered.
        symbol: Trading pair symbol that triggered the rule, e.g. "BTC/USDT".
        timeframe: Candle timeframe that was evaluated, e.g. "4h".
        message: Human-readable description of the match for use in alerts.
    """

    rule: Rule
    symbol: str
    timeframe: str
    message: str


_MESSAGE_TEMPLATES: dict[str, str] = {
    "EMA Crossover 9/21": "Bullish crossover detected — fast EMA crossed above slow EMA. Momentum may be shifting upward.",
    "RSI Oversold": "RSI at {rsi:.1f} — entering oversold territory. Watch for a potential bounce.",
    "RSI Overbought": "RSI at {rsi:.1f} — entering overbought territory. Consider taking profits or tightening stops.",
    "Price Above VWAP": "Trading above VWAP at {close:,.2f} (VWAP {vwap:,.2f}). Intraday bias is bullish.",
    "Volume Spike 2x": "Unusual volume detected — {ratio:.1f}x the recent average. Something is moving.",
}


def _build_message(rule_name: str, df: pd.DataFrame) -> str:
    """Build a user-friendly alert message using indicator values from df.

    Falls back to rule name if no template is defined.

    Args:
        rule_name: Name of the rule that fired.
        df: DataFrame with indicator columns for value interpolation.

    Returns:
        Formatted message string.
    """
    template = _MESSAGE_TEMPLATES.get(rule_name)
    if template is None:
        return rule_name

    last = df.iloc[-1]
    values: dict[str, float] = {}

    if "rsi" in df.columns:
        values["rsi"] = float(last["rsi"])
    if "close" in df.columns:
        values["close"] = float(last["close"])
    if "vwap" in df.columns:
        values["vwap"] = float(last["vwap"])
    if "volume" in df.columns and len(df) > 20:
        rolling_mean = df["volume"].iloc[-21:-1].mean()
        values["ratio"] = float(last["volume"] / rolling_mean) if rolling_mean > 0 else 0.0

    try:
        return template.format(**values)
    except KeyError:
        return rule_name


def run(
    rules: list[Rule],
    df: pd.DataFrame,
    symbol: str,
    timeframe: str,
) -> list[RuleMatch]:
    """Evaluate all rules against a DataFrame and return matches.

    Args:
        rules: List of Rule instances to evaluate.
        df: DataFrame with OHLCV data and pre-computed indicator columns.
        symbol: Trading pair symbol the data belongs to.
        timeframe: Candle timeframe the data belongs to.

    Returns:
        List of RuleMatch for every rule whose conditions all returned True.
        Returns an empty list if no rules matched.
    """
    matches = []
    for rule in rules:
        if rule.evaluate(df):
            matches.append(
                RuleMatch(
                    rule=rule,
                    symbol=symbol,
                    timeframe=timeframe,
                    message=_build_message(rule.name, df),
                )
            )
    return matches
