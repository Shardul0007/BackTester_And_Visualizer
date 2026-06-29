"""
Utilities for indexing market quotes by timestamp.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from models.quote_tick import QuoteTick

QuoteIndex = dict[datetime, QuoteTick]


def build_quote_index(dataframe: pd.DataFrame) -> QuoteIndex:
    """
    Build an O(1) lookup table for market quotes.
    """

    return {
        row.Timestamp.to_pydatetime(): QuoteTick(
            price=row.Price,
            volume=row.Volume,
            open_interest=row.OpenInterest,
        )
        for row in dataframe.itertuples(index=False)
    }