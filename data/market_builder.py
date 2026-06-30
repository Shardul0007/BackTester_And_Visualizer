"""
Builds Market domain objects from raw market data.

The central design decision here is the synchronization strategy between
the dense futures timeline and the sparse option tick data:

- The futures series is continuous (one row per second, 09:15–15:30).
  It drives the simulation loop — every second is a simulation step.

- Option series are sparse.  A strike may not trade for minutes at a time.
  The correct price at any futures timestamp is the LAST known option
  price at or before that timestamp, resolved via SparseQuoteIndex.

- If no option price is known yet at a given timestamp (the contract has
  not started trading), the strike is excluded from the option chain for
  that snapshot.  The ATM strike is then chosen from whichever strikes
  ARE available.

This means the option chain can be smaller early in the day and grows
as more contracts start trading — which faithfully represents reality.
"""

from __future__ import annotations

from datetime import datetime

from data.quote_index import (
    QuoteIndex,
    SparseQuoteIndex,
    build_quote_index,
    build_sparse_quote_index,
)
from models.enums import Underlying
from models.future_quote import FutureQuote
from models.market import Market
from models.market_snapshot import MarketSnapshot
from models.option_pair_quote import OptionPairQuote
from models.option_quote import OptionQuote
from models.option_series import OptionSeries
from models.quote_tick import QuoteTick
from models.raw_market_data import RawMarketData
from utils.strike import nearest_strike


def build_markets(
    raw_market_data: RawMarketData,
) -> dict[Underlying, Market]:
    """
    Build Market objects for every underlying present in the raw market data.
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

    The futures index drives the simulation timeline.
    Option indices are built once and queried via last-known-price lookup.
    """

    future_series = raw_market_data.futures[underlying]
    option_series = raw_market_data.options[underlying]

    # Dense index for futures — exact-match O(1) lookup.
    future_index: QuoteIndex = build_quote_index(future_series.dataframe)

    # Sparse indices for options — binary-search "at or before" lookup.
    option_indices: dict[int, tuple[SparseQuoteIndex, SparseQuoteIndex]] = (
        _build_option_indices(option_series)
    )

    market = Market(
        trading_date=raw_market_data.trading_date,
        underlying=underlying,
    )

    for timestamp in sorted(future_index.keys()):

        future_tick = future_index[timestamp]

        future_quote = FutureQuote(
            instrument=future_series.instrument,
            price=future_tick.price,
            volume=future_tick.volume,
            open_interest=future_tick.open_interest,
        )

        # Build the option chain for this timestamp.
        # Strikes where either CE or PE has no price yet are excluded.
        option_chain = _build_option_chain(
            timestamp,
            option_series,
            option_indices,
        )

        if not option_chain:
            # No options are tradable yet (very start of day edge case).
            # Skip this snapshot — the strategy cannot act without quotes.
            continue

        # ATM strike is computed from the strikes AVAILABLE in the chain,
        # not from all loaded strikes.  This ensures atm_pair always exists.
        available_strikes = sorted(option_chain.keys())

        atm_strike = nearest_strike(
            future_quote.price,
            available_strikes,
        )

        snapshot = MarketSnapshot(
            timestamp=timestamp,
            future=future_quote,
            atm_strike=atm_strike,
            option_chain=option_chain,
        )

        market.add_snapshot(snapshot)

    return market


def _build_option_indices(
    option_series: dict[int, OptionSeries],
) -> dict[int, tuple[SparseQuoteIndex, SparseQuoteIndex]]:
    """
    Build sparse quote indices for every option strike.

    Returns
    -------
    {
        strike: (call_sparse_index, put_sparse_index)
    }
    """

    indices: dict[int, tuple[SparseQuoteIndex, SparseQuoteIndex]] = {}

    for strike, series in option_series.items():

        call_index = build_sparse_quote_index(series.call_dataframe)
        put_index = build_sparse_quote_index(series.put_dataframe)

        indices[strike] = (call_index, put_index)

    return indices


def _build_option_chain(
    timestamp: datetime,
    option_series: dict[int, OptionSeries],
    option_indices: dict[int, tuple[SparseQuoteIndex, SparseQuoteIndex]],
) -> dict[int, OptionPairQuote]:
    """
    Build the option chain for one simulation timestamp.

    For each strike, resolves the last known call and put prices at or
    before this timestamp using SparseQuoteIndex.

    Strikes where either leg has no known price yet are silently excluded.
    This is correct behaviour: a contract that has not traded cannot be
    bought, so it should not appear in the chain.

    Parameters
    ----------
    timestamp:
        The current simulation second.
    option_series:
        All loaded OptionSeries for this underlying.
    option_indices:
        Pre-built SparseQuoteIndex pairs keyed by strike.

    Returns
    -------
    dict[int, OptionPairQuote]
        Tradable strikes at this timestamp.  May be empty if no option
        has started trading yet.
    """

    option_chain: dict[int, OptionPairQuote] = {}

    for strike, series in option_series.items():

        call_index, put_index = option_indices[strike]

        call_tick: QuoteTick | None = call_index.get_at_or_before(timestamp)
        put_tick: QuoteTick | None = put_index.get_at_or_before(timestamp)

        # Both legs must have a known price to form a tradable pair.
        if call_tick is None or put_tick is None:
            continue

        call_quote = OptionQuote(
            instrument=series.call_instrument,
            price=call_tick.price,
            volume=call_tick.volume,
            open_interest=call_tick.open_interest,
        )

        put_quote = OptionQuote(
            instrument=series.put_instrument,
            price=put_tick.price,
            volume=put_tick.volume,
            open_interest=put_tick.open_interest,
        )

        option_chain[strike] = OptionPairQuote(call=call_quote, put=put_quote)

    return option_chain
