"""
Utilities for indexing market quotes by timestamp.

Two index types are provided because futures and options have different
query semantics:

QuoteIndex (dense dict)
    For futures.  The futures series is continuous, so an exact-match
    dict lookup is both correct and O(1).

SparseQuoteIndex (sorted list + binary search)
    For options.  Options are sparse tick data: many seconds have no
    trade.  The correct query is "what was the last known price at or
    before this timestamp?"  This is answered in O(log n) by a
    binary-search over the sorted timestamp list.

    If no tick exists at or before the queried timestamp (i.e., the
    option has not started trading yet), the lookup returns None.
    Callers must handle None gracefully — it means the option is not
    yet available and the strike should be skipped for this timestamp.
"""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd

from models.quote_tick import QuoteTick


# ---------------------------------------------------------------------------
# Dense index — used for futures
# ---------------------------------------------------------------------------

QuoteIndex = dict[datetime, QuoteTick]


def build_quote_index(dataframe: pd.DataFrame) -> QuoteIndex:
    """
    Build an O(1) exact-match lookup table for futures quotes.

    The dataframe must be a continuous (dense) series — every queried
    timestamp must appear as a row, otherwise the lookup returns None.
    """

    return {
        row.Timestamp.to_pydatetime(): QuoteTick(
            price=row.Price,
            volume=row.Volume,
            open_interest=row.OpenInterest,
        )
        for row in dataframe.itertuples(index=False)
    }


# ---------------------------------------------------------------------------
# Sparse index — used for options
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class SparseQuoteIndex:
    """
    A sorted, binary-searchable index for sparse option tick data.

    Attributes
    ----------
    timestamps:
        Chronologically sorted list of timestamps where trades occurred.
    ticks:
        Parallel list of QuoteTick objects corresponding to each timestamp.

    The two lists are always the same length and the same order.
    """

    timestamps: list[datetime] = field(default_factory=list)
    ticks: list[QuoteTick] = field(default_factory=list)

    def get_at_or_before(self, ts: datetime) -> QuoteTick | None:
        """
        Return the last known quote at or before the given timestamp.

        Returns None if no tick has occurred yet at or before ts
        (i.e., the option has not started trading).

        Parameters
        ----------
        ts:
            The timestamp to query.

        Returns
        -------
        QuoteTick | None
        """

        # bisect_right gives the insertion point for ts in the sorted list.
        # The element immediately to the left (index i-1) is the largest
        # timestamp that is <= ts.
        i = bisect_right(self.timestamps, ts) - 1

        if i < 0:
            return None

        return self.ticks[i]


def build_sparse_quote_index(dataframe: pd.DataFrame) -> SparseQuoteIndex:
    """
    Build a SparseQuoteIndex from a sparse option tick DataFrame.

    The dataframe must already be sorted by Timestamp (guaranteed by
    TimeSeriesProcessor.build_options).

    Parameters
    ----------
    dataframe:
        Sparse DataFrame produced by TimeSeriesProcessor.build_options.

    Returns
    -------
    SparseQuoteIndex
    """

    timestamps: list[datetime] = []
    ticks: list[QuoteTick] = []

    for row in dataframe.itertuples(index=False):
        timestamps.append(row.Timestamp.to_pydatetime())
        ticks.append(
            QuoteTick(
                price=row.Price,
                volume=row.Volume,
                open_interest=row.OpenInterest,
            )
        )

    return SparseQuoteIndex(timestamps=timestamps, ticks=ticks)