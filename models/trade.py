"""
Represents a completely closed position (a completed trade).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from models.instrument import Instrument


@dataclass(frozen=True, slots=True)
class Trade:
    """
    Record of a completed trade (entry and exit).
    """

    instrument: Instrument
    quantity: int
    entry_time: datetime
    entry_price: float
    exit_time: datetime
    exit_price: float

    @property
    def realized_pnl(self) -> float:
        """
        Calculate realized profit/loss.
        Positive quantity implies a long position (BUY to open, SELL to close).
        """
        return (self.exit_price - self.entry_price) * self.quantity
