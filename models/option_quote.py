"""
Represents the market data of an option contract at a specific timestamp.
"""

from __future__ import annotations

from dataclasses import dataclass

from models.instrument import Instrument
@dataclass(slots=True)
class OptionQuote:
    """
    Live market information for an option instrument.
    """

    instrument: Instrument
    price: float
    volume: int
    open_interest: int