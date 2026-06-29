"""
Utilities for loading and normalizing raw market data files.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


class CSVLoader:
    """
    Loads raw NSE market data files into a normalized DataFrame.

    The raw dataset is tick-level data with multiple trades occurring
    within the same second. The loader aggregates these ticks by keeping
    the last trade observed for each second.
    """

    COLUMN_NAMES = [
        "Date",
        "Time",
        "Price",
        "Volume",
        "OpenInterest",
    ]

    @classmethod
    def load(cls, file_path: str | Path) -> pd.DataFrame:
        """
        Load a CSV file and return a normalized DataFrame.

        Parameters
        ----------
        file_path:
            Path to the CSV file.

        Returns
        -------
        pd.DataFrame
            One row per second ordered chronologically.
        """

        dataframe = pd.read_csv(
            file_path,
            header=None,
            names=cls.COLUMN_NAMES,
        )

        dataframe = cls._convert_types(dataframe)
        dataframe = cls._build_timestamp(dataframe)
        dataframe = cls._normalize_ticks(dataframe)

        return dataframe.reset_index(drop=True)

    @staticmethod
    def _convert_types(dataframe: pd.DataFrame) -> pd.DataFrame:
        """Convert columns to their expected data types."""

        dataframe["Date"] = dataframe["Date"].astype(str)

        dataframe["Time"] = dataframe["Time"].astype(str)

        dataframe["Price"] = dataframe["Price"].astype(float)

        dataframe["Volume"] = dataframe["Volume"].astype(int)

        dataframe["OpenInterest"] = dataframe["OpenInterest"].astype(int)

        return dataframe

    @staticmethod
    def _build_timestamp(dataframe: pd.DataFrame) -> pd.DataFrame:
        """Create a timestamp column from the date and time columns."""

        dataframe["Timestamp"] = pd.to_datetime(
            dataframe["Date"] + " " + dataframe["Time"],
            format="%Y%m%d %H:%M:%S",
        )

        return dataframe

    @staticmethod
    def _normalize_ticks(dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Convert tick data into one observation per second.

        If multiple trades occur within the same second,
        the last traded price is retained.
        """

        dataframe = (
            dataframe.sort_values("Timestamp")
            .groupby("Timestamp", as_index=False)
            .last()
        )

        return dataframe