"""
Domain model representing a single tradable instrument.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from models.enums import InstrumentType, OptionType, Underlying


@dataclass(frozen=True, slots=True)
class Instrument:
    """
    Represents a unique tradable instrument.

    Examples:
        NIFTY22110324500CE
        BANKNIFTY22112443200PE
        NIFTY-I
    """

    underlying: Underlying
    instrument_type: InstrumentType
    expiry: date | None
    strike: int | None
    option_type: OptionType | None
    symbol: str

    @property
    def is_option(self) -> bool:
        """Returns True if the instrument is an option."""
        return self.instrument_type == InstrumentType.OPTION

    @property
    def is_future(self) -> bool:
        """Returns True if the instrument is a futures contract."""
        return self.instrument_type == InstrumentType.FUTURE

    @property
    def display_name(self) -> str:
        """Returns a human-readable identifier."""

        if self.is_future:
            return f"{self.underlying.value}-I"

        return (
            f"{self.underlying.value}"
            f"{self.expiry.strftime('%y%m%d')}"
            f"{self.strike}"
            f"{self.option_type.value}"
        )

    def __str__(self) -> str:
        return self.display_name