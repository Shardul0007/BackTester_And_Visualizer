"""
Loads all market data required for simulating a single trading day.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import pandas as pd

from data.csv_loader import CSVLoader
from data.filename_parser import FilenameParser
from data.time_series import TimeSeriesProcessor
from models.enums import InstrumentType, Underlying
from BackTester_And_Visualizer.models.raw_market_data import TradingDay


class TradingDayLoader:
    """
    Loads futures and nearest-expiry options for a trading day.
    """

    def __init__(self, trading_day_directory: str | Path):
        self.day_path = Path(trading_day_directory)

    def load(self) -> TradingDay:
        """
        Load all data required for one trading day.
        """

        trading_date = self._parse_trading_date()

        futures = self._load_futures()

        options = self._load_options()

        return TradingDay(
            trading_date=trading_date,
            futures=futures,
            options=options,
        )

    def _parse_trading_date(self):
        from datetime import datetime

        return datetime.strptime(
            self.day_path.name.split("_")[1],
            "%Y%m%d",
        ).date()

    def _load_futures(self):
        futures = {}

        futures_path = self.day_path / "futures"

        for underlying in (
            Underlying.NIFTY,
            Underlying.BANKNIFTY,
        ):
            file_path = futures_path / f"{underlying.value}-I.csv"

            dataframe = CSVLoader.load(file_path)

            dataframe = TimeSeriesProcessor.build(dataframe)

            futures[underlying] = dataframe

        return futures

    def _load_options(self):

        option_map = defaultdict(
            lambda: defaultdict(dict)
        )

        options_path = self.day_path / "options"

        nearest_expiry = self._find_nearest_expiry()

        for file_path in options_path.glob("*.csv"):

            instrument = FilenameParser.parse(file_path)

            if instrument.instrument_type != InstrumentType.OPTION:
                continue

            if instrument.expiry != nearest_expiry[
                instrument.underlying
            ]:
                continue

            dataframe = CSVLoader.load(file_path)

            dataframe = TimeSeriesProcessor.build(dataframe)

            option_map[
                instrument.underlying
            ][
                instrument.strike
            ][
                instrument.option_type.value
            ] = dataframe

        return option_map

    def _find_nearest_expiry(self):

        expiry = {}

        options_path = self.day_path / "options"

        for file_path in options_path.glob("*.csv"):

            instrument = FilenameParser.parse(file_path)

            current = expiry.get(
                instrument.underlying
            )

            if (
                current is None
                or instrument.expiry < current
            ):
                expiry[
                    instrument.underlying
                ] = instrument.expiry

        return expiry