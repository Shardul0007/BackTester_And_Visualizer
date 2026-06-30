from dataclasses import dataclass
from typing import Optional

import pandas as pd

from models.instrument import Instrument


@dataclass(slots=True)
class OptionSeries:
    """
    Stores the historical market data for both option contracts
    belonging to a single strike.
    """

    strike: int

    call_instrument: Optional[Instrument] = None
    put_instrument: Optional[Instrument] = None

    call_dataframe: Optional[pd.DataFrame] = None
    put_dataframe: Optional[pd.DataFrame] = None