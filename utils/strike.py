"""
Utilities for working with option strikes.
"""

from __future__ import annotations

from bisect import bisect_left


def nearest_strike(
    future_price: float,
    available_strikes: list[int],
) -> int:
    """
    Return the strike closest to the current futures price.

    If two strikes are equally close,
    the lower strike is selected.
    """

    index = bisect_left(
        available_strikes,
        future_price,
    )

    if index == 0:
        return available_strikes[0]

    if index == len(available_strikes):
        return available_strikes[-1]

    lower = available_strikes[index - 1]
    upper = available_strikes[index]

    if abs(future_price - lower) <= abs(upper - future_price):
        return lower

    return upper