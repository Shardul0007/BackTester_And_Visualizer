"""
Container for all market data required to simulate one trading day.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from models.enums import Underlying
from models.future_series import FutureSeries
from models.option_series import OptionSeries
from models.validation import ValidationResult


@dataclass(slots=True)
class RawMarketData:
    """
    Represents all normalized market data loaded from disk
    before it is transformed into MarketSnapshots.
    """

    trading_date: date

    futures: dict[
        Underlying,
        FutureSeries,
    ]

    options: dict[
        Underlying,
        dict[
            int,
            OptionSeries,
        ],
    ]

    validation_results: dict[
        str,
        ValidationResult,
    ]