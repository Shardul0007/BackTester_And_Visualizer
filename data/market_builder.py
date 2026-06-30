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
from data.quote_index import QuoteIndex
from models.future_quote import FutureQuote
from models.option_pair_quote import OptionPairQuote
from models.option_quote import OptionQuote
from models.quote_tick import QuoteTick


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
def _build_future_quote(
    tick: QuoteTick,
    future_series,
) -> FutureQuote:
    """
    Build a FutureQuote from a quote tick.
    """

    return FutureQuote(
        instrument=future_series.instrument,
        price=tick.price,
        volume=tick.volume,
        open_interest=tick.open_interest,
    )

def _build_option_quote(
    tick: QuoteTick,
    instrument,
) -> OptionQuote:
    """
    Build an OptionQuote from a quote tick.
    """

    return OptionQuote(
        instrument=instrument,
        price=tick.price,
        volume=tick.volume,
        open_interest=tick.open_interest,
    )

def _build_option_chain(
    timestamp: datetime,
    option_series: dict[int, OptionSeries],
    option_indices: dict[int, tuple[QuoteIndex, QuoteIndex]],
) -> dict[int, OptionPairQuote]:
    """
    Build the complete option chain for one timestamp.
    """

    option_chain = {}

    for strike, series in option_series.items():

        call_index, put_index = option_indices[strike]

        call_tick = call_index.get(timestamp)

        if call_tick is None:
            raise ValueError(
                f"Missing call quote for "
                f"{series.call_instrument.symbol} "
                f"at {timestamp}"
            )

        put_tick = put_index.get(timestamp)

        if put_tick is None:
            raise ValueError(
                f"Missing put quote for "
                f"{series.put_instrument.symbol} "
                f"at {timestamp}"
            )

        call_quote = _build_option_quote(
            call_tick,
            series.call_instrument,
        )

        put_quote = _build_option_quote(
            put_tick,
            series.put_instrument,
        )

        option_chain[strike] = OptionPairQuote(
            call=call_quote,
            put=put_quote,
        )

    return option_chain

