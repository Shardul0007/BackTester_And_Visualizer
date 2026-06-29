"""
Utilities for building continuous one-second market time series.
"""

from __future__ import annotations

import pandas as pd


class TimeSeriesProcessor:
    """
    Converts normalized tick data into a continuous one-second time series.

    Missing timestamps are forward-filled using the latest available quote.
    """

    @staticmethod
    def build(dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Return a continuous one-second DataFrame.

        Parameters
        ----------
        dataframe:
            Normalized DataFrame produced by CSVLoader.

        Returns
        -------
        pd.DataFrame
            Continuous one-second time series.
        """

        dataframe = dataframe.set_index("Timestamp")

        complete_index = pd.date_range(
            start=dataframe.index.min(),
            end=dataframe.index.max(),
            freq="1s",
        )

        dataframe = (
            dataframe
            .reindex(complete_index)
            .ffill()
        )

        dataframe.index.name = "Timestamp"

        dataframe = dataframe.reset_index()

        dataframe["Date"] = dataframe["Timestamp"].dt.strftime("%Y%m%d")

        dataframe["Time"] = dataframe["Timestamp"].dt.strftime("%H:%M:%S")

        return dataframe