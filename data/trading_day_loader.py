"""
Loads all market data required for simulating a single trading day.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path

from data.csv_loader import CSVLoader
from data.filename_parser import FilenameParser
from data.time_series import TimeSeriesProcessor
from data.validator import DataValidator

from models.enums import InstrumentType, OptionType, Underlying
from models.future_series import FutureSeries
from models.option_series import OptionSeries
from models.raw_market_data import RawMarketData


class TradingDayLoader:
    """
    Loads futures and nearest-expiry option data for one trading day.
    """

    def __init__(self, trading_day_directory: str | Path):
        self.day_path = Path(trading_day_directory)

    def load(self) -> RawMarketData:

        trading_date = self._parse_trading_date()

        validation_results = {}

        futures = self._load_futures(validation_results)

        options = self._load_options(validation_results)

        return RawMarketData(
            trading_date=trading_date,
            futures=futures,
            options=options,
            validation_results=validation_results,
        )

    def _parse_trading_date(self):
        return datetime.strptime(
            self.day_path.name.split("_")[1],
            "%Y%m%d",
        ).date()

    def _load_futures(self, validation_results):

        futures = {}

        futures_path = self.day_path / "futures"

        for underlying in (
            Underlying.NIFTY,
            Underlying.BANKNIFTY,
        ):

            file_path = futures_path / f"{underlying.value}-I.csv"

            instrument = FilenameParser.parse(file_path)

            dataframe = CSVLoader.load(file_path)

            validation = DataValidator.validate(dataframe)

            validation_results[file_path.name] = validation

            if not validation.passed:
                raise ValueError(
                    f"Validation failed for {file_path.name}"
                )

            dataframe = TimeSeriesProcessor.build(dataframe)

            futures[underlying] = FutureSeries(
                instrument=instrument,
                dataframe=dataframe,
            )

        return futures

    def _load_options(self, validation_results):

        option_map = defaultdict(dict)

        nearest_expiry = self._find_nearest_expiry()

        options_path = self.day_path / "options"

        for file_path in options_path.glob("*.csv"):

            instrument = FilenameParser.parse(file_path)

            if instrument.instrument_type != InstrumentType.OPTION:
                continue

            if instrument.expiry != nearest_expiry[instrument.underlying]:
                continue

            dataframe = CSVLoader.load(file_path)

            validation = DataValidator.validate(dataframe)

            validation_results[file_path.name] = validation

            if not validation.passed:
                raise ValueError(
                    f"Validation failed for {file_path.name}"
                )

            dataframe = TimeSeriesProcessor.build(dataframe)

            strike_map = option_map[instrument.underlying]

            series = strike_map.get(instrument.strike)

            if series is None:
                series = OptionSeries(
                    strike=instrument.strike,
                )
                strike_map[instrument.strike] = series

            if instrument.option_type == OptionType.CALL:
                series.call_instrument = instrument
                series.call_dataframe = dataframe
            else:
                series.put_instrument = instrument
                series.put_dataframe = dataframe

        for underlying, strike_map in option_map.items():

            for strike, series in strike_map.items():

                if (
                    series.call_dataframe is None
                    or series.put_dataframe is None
                ):
                    raise ValueError(
                        f"Incomplete option series for "
                        f"{underlying.value} "
                        f"strike {strike}"
                    )

        return dict(option_map)

    def _find_nearest_expiry(self):

        expiry = {}

        options_path = self.day_path / "options"

        for file_path in options_path.glob("*.csv"):

            instrument = FilenameParser.parse(file_path)

            if instrument.instrument_type != InstrumentType.OPTION:
                continue

            current = expiry.get(instrument.underlying)

            if current is None or instrument.expiry < current:
                expiry[instrument.underlying] = instrument.expiry

        return expiry