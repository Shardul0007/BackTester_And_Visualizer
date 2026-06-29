"""
Parses NSE instrument filenames into Instrument domain objects.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from models.enums import InstrumentType, OptionType, Underlying
from models.instrument import Instrument


class FilenameParser:
    """Converts instrument filenames into Instrument objects."""

    _UNDERLYINGS = (
        Underlying.BANKNIFTY,
        Underlying.FINNIFTY,
        Underlying.NIFTY,
    )

    @classmethod
    def parse(cls, file_path: str | Path) -> Instrument:
        """
        Parse an instrument filename.

        Examples
        --------
        NIFTY22110324500CE.csv
        BANKNIFTY22112443200PE.csv
        NIFTY-I.csv
        """

        filename = Path(file_path).stem

        if filename.endswith("-I"):
            return cls._parse_future(filename)

        return cls._parse_option(filename)

    @classmethod
    def _parse_option(cls, filename: str) -> Instrument:
        underlying = cls._extract_underlying(filename)

        remaining = filename[len(underlying.value):]

        expiry = datetime.strptime(
            remaining[:6],
            "%y%m%d",
        ).date()

        option_type = OptionType(remaining[-2:])

        strike = int(remaining[6:-2])

        return Instrument(
            underlying=underlying,
            instrument_type=InstrumentType.OPTION,
            expiry=expiry,
            strike=strike,
            option_type=option_type,
            symbol=filename,
        )

    @classmethod
    def _parse_future(cls, filename: str) -> Instrument:
        underlying = Underlying(filename[:-2])

        return Instrument(
            underlying=underlying,
            instrument_type=InstrumentType.FUTURE,
            expiry=None,
            strike=None,
            option_type=None,
            symbol=filename,
        )

    @classmethod
    def _extract_underlying(cls, filename: str) -> Underlying:
        for underlying in cls._UNDERLYINGS:
            if filename.startswith(underlying.value):
                return underlying

        raise ValueError(f"Unknown underlying: {filename}")