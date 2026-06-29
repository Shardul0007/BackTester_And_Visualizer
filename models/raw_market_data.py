"""
Container for all market data required to simulate a single trading day.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

from BackTester_And_Visualizer.models.validation import ValidationResult
from models.enums import Underlying
@dataclass(slots=True)
class OptionSeries:

    strike: int

    call: pd.DataFrame

    put: pd.DataFrame
@dataclass(slots=True)
class RawMarketData:

    trading_date: date

    futures: dict[Underlying, pd.DataFrame]

    options: dict[
    Underlying,

    dict[
        int,

        OptionSeries
    ]
]

    validation_results: dict[
        str,
        ValidationResult
    ]