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
                    message=f"[{symbol} {timeframe}] {rule.name}",
                )
            )
    return matches
