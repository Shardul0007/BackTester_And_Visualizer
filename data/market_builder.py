"""
Builds Market domain objects from raw market data.
"""

from __future__ import annotations

from datetime import datetime

from data.quote_index import QuoteIndex, build_quote_index
from models.enums import Underlying
from models.market import Market
from models.option_series import OptionSeries
from models.raw_market_data import RawMarketData


def build_markets(
    raw_market_data: RawMarketData,
) -> dict[Underlying, Market]:
    """
    Build Market objects for every underlying present in the
    raw market data.
    """

    markets: dict[Underlying, Market] = {}

    for underlying in raw_market_data.futures:

        markets[underlying] = _build_market(
            raw_market_data,
            underlying,
        )

    return markets


def _build_market(
    raw_market_data: RawMarketData,
    underlying: Underlying,
) -> Market:
    """
    Build the complete market for one underlying.

    This function prepares all lookup structures required by the
    snapshot generation loop.
    """

    future_series = raw_market_data.futures[underlying]

    future_index = build_quote_index(
        future_series.dataframe
    )

    option_indices = _build_option_indices(
        raw_market_data.options[underlying]
    )

    available_strikes = sorted(
        option_indices.keys()
    )

    market = Market(
        trading_date=raw_market_data.trading_date,
        underlying=underlying,
    )

    #
    # Snapshot generation will happen here
    # in the next commit.
    #

    return market


def _build_option_indices(
    option_series: dict[int, OptionSeries],
) -> dict[
    int,
    tuple[
        QuoteIndex,
        QuoteIndex,
    ],
]:
    """
    Build quote indices for every option strike.

    Returns
    -------
    {
        strike:
            (
                call_quote_index,
                put_quote_index,
            )
    }
    """

    indices = {}

    for strike, series in option_series.items():

        call_index = build_quote_index(
            series.call_dataframe
        )

        put_index = build_quote_index(
            series.put_dataframe
        )

        indices[strike] = (
            call_index,
            put_index,
        )

    return indices