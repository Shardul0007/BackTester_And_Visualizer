"""
Represents all market snapshots for a single trading day.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Iterator

from models.enums import Underlying
from models.market_snapshot import MarketSnapshot


@dataclass(slots=True)
class Market:
    """
    Collection of market snapshots belonging to a single
    underlying and trading day.
    """

    trading_date: date
    underlying: Underlying
    snapshots: list[MarketSnapshot] = field(default_factory=list)

    def __iter__(self) -> Iterator[MarketSnapshot]:
        """Allows iteration over market snapshots."""
        return iter(self.snapshots)

    def __len__(self) -> int:
        """Returns the number of snapshots."""
        return len(self.snapshots)

    def add_snapshot(self, snapshot: MarketSnapshot) -> None:
        """Appends a snapshot while preserving chronological order."""
        self.snapshots.append(snapshot)