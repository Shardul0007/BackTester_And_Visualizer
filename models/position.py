"""
Represents an active position in the portfolio.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from models.enums import PositionStatus
from models.instrument import Instrument


@dataclass(slots=True)
class Position:
    """
    Represents an open position held by the backtester.
    """

    instrument: Instrument
    quantity: int
    entry_time: datetime
    entry_price: float
    status: PositionStatus = PositionStatus.OPEN