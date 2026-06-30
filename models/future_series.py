"""
Represents the complete historical time series for a futures contract.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from models.instrument import Instrument


@dataclass(slots=True)
class FutureSeries:
    """
    Stores the historical market data for one futures contract.
    """

    instrument: Instrument
    dataframe: pd.DataFrame