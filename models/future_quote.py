"""
Represents the market data of a futures contract at a specific timestamp.
"""

from __future__ import annotations

from dataclasses import dataclass

from models.instrument import Instrument


@dataclass(slots=True)
class FutureQuote:
    """
    Live market information for a futures instrument.
    """

    instrument: Instrument
    price: float
    volume: int
    open_interest: int