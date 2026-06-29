"""
Represents the market data available for a single timestamp.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QuoteTick:
    """Market quote at a specific timestamp."""

    price: float
    volume: int
    open_interest: int