"""
Utilities for building continuous one-second market time series.

Two separate pipelines exist because futures and options have fundamentally
different data characteristics:

- Futures are near-continuous. Every second should have a price.
  A reindexed, forward-filled series is both correct and expected.

- Options are sparse tick data.  Many strikes only trade a few hundred
  times per day.  Reindexing them to a dense 22,500-row series would
  fabricate prices that never existed, and would still leave leading
  NaN gaps for contracts that open late.  Options must stay sparse.
"""

from __future__ import annotations

import pandas as pd


class TimeSeriesProcessor:
    """
    Converts raw tick data into a normalized market time series.

    Two processing modes are provided:

    build_futures
        Builds a continuous one-second series from 09:15:00 to 15:30:00.
        Gaps are forward-filled so every second has a valid price.
        This is correct for futures, which are essentially continuous.

    build_options
        Deduplicates intra-second ticks (keeps the last trade per second)
        and sorts chronologically.  The result is a sparse series that
        only contains rows where actual trades occurred.
        Gaps are intentional and must not be filled.
    """

    @staticmethod
    def build_futures(dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Build a dense, continuous one-second futures time series.

        Processing steps
        ----------------
        1. Sort by timestamp.
        2. Keep the last trade for every second (deduplicate intra-second
           ticks).
        3. Reindex to a complete one-second timeline from the first to
           the last observed timestamp.
        4. Forward-fill Price and OpenInterest.
        5. Set Volume to zero where no trade occurred.

        Parameters
        ----------
        dataframe:
            Normalized DataFrame produced by CSVLoader.

        Returns
        -------
        pd.DataFrame
            Continuous one-second futures market data with no gaps.
        """

        dataframe = dataframe.sort_values("Timestamp")

        dataframe = (
            dataframe
            .drop_duplicates(subset="Timestamp", keep="last")
            .set_index("Timestamp")
        )

        complete_index = pd.date_range(
            start=dataframe.index.min(),
            end=dataframe.index.max(),
            freq="1s",
        )

        dataframe = dataframe.reindex(complete_index)

        dataframe["Price"] = (
            dataframe["Price"]
            .ffill()
            .bfill()
        )

        dataframe["OpenInterest"] = (
            dataframe["OpenInterest"]
            .ffill()
            .bfill()
        )

        dataframe["Volume"] = dataframe["Volume"].fillna(0)

        dataframe.index.name = "Timestamp"
        dataframe = dataframe.reset_index()

        dataframe["Date"] = dataframe["Timestamp"].dt.strftime("%Y%m%d")
        dataframe["Time"] = dataframe["Timestamp"].dt.strftime("%H:%M:%S")
        dataframe["Volume"] = dataframe["Volume"].astype(int)
        dataframe["OpenInterest"] = dataframe["OpenInterest"].astype(int)

        return dataframe

    @staticmethod
    def build_options(dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Build a sparse, deduplicated option tick series.

        Processing steps
        ----------------
        1. Sort by timestamp.
        2. Keep the last trade for every second (deduplicate intra-second
           ticks).

        Gaps are left intentionally empty.  The caller is responsible for
        resolving the price at any given futures timestamp using a
        "last-known-quote" lookup (see SparseQuoteIndex in quote_index.py).

        Parameters
        ----------
        dataframe:
            Normalized DataFrame produced by CSVLoader.

        Returns
        -------
        pd.DataFrame
            Sparse option tick data.  One row per second where at least
            one trade occurred.  No artificial gap-filling.
        """

        dataframe = (
            dataframe
            .sort_values("Timestamp")
            .drop_duplicates(subset="Timestamp", keep="last")
            .reset_index(drop=True)
        )

        return dataframe