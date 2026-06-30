"""
Represents the complete market state at a single timestamp.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from models.future_quote import FutureQuote
from models.option_pair_quote import OptionPairQuote


@dataclass(frozen=True, slots=True)
class MarketSnapshot:
    """
    Immutable view of the market at a single point in time.

    The strategy receives one MarketSnapshot every simulation step
    and decides whether any action should be taken.
    """

    timestamp: datetime
    future: FutureQuote
    atm_strike: int
    option_chain: dict[int, OptionPairQuote]

    @property
    def atm_pair(self) -> OptionPairQuote:
        """Return the call/put pair at the ATM strike."""
        return self.option_chain[self.atm_strike]