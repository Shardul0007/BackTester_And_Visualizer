"""
Read-only view of the portfolio provided to strategies.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class PortfolioView:
    """
    Provides strategies with information about current positions
    without exposing methods to modify the portfolio directly.
    """

    held_strike: Optional[int]

    @property
    def has_position(self) -> bool:
        """Returns True if a position is currently held."""
        return self.held_strike is not None
