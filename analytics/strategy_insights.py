"""Strategy-specific analytics helpers.

Generic analytics should work for any strategy.  Metrics that depend on the
ATM straddle idea live here and are passed into the generic calculator as an
optional plugin-style dictionary.
"""

from __future__ import annotations

from statistics import mean
from typing import Any, Mapping

from models.market import Market


def build_atm_strategy_insights(markets: Mapping[Any, Market]) -> dict[str, Any]:
    """Compute ATM strike and premium metrics from market snapshots."""

    timeline: list[dict[str, Any]] = []
    strike_holding_seconds: list[float] = []
    rollover_intervals_seconds: list[float] = []
    ce_premiums: list[float] = []
    pe_premiums: list[float] = []
    combined_premiums: list[float] = []
    premium_decay_by_underlying: dict[str, float | None] = {}
    atm_strike_changes = 0

    for underlying, market in sorted(markets.items(), key=lambda item: item[0].value):
        previous_strike = None
        previous_change_time = None
        first_combined = None
        last_combined = None

        for snapshot in market.snapshots:
            pair = snapshot.option_chain.get(snapshot.atm_strike)
            if pair is None:
                continue

            ce_premium = pair.call.price
            pe_premium = pair.put.price
            combined = ce_premium + pe_premium
            ce_premiums.append(ce_premium)
            pe_premiums.append(pe_premium)
            combined_premiums.append(combined)

            if first_combined is None:
                first_combined = combined
            last_combined = combined

            timeline.append(
                {
                    "timestamp": snapshot.timestamp.isoformat(sep=" "),
                    "underlying": underlying.value,
                    "future_price": snapshot.future.price,
                    "atm_strike": snapshot.atm_strike,
                    "ce_premium": ce_premium,
                    "pe_premium": pe_premium,
                    "combined_premium": combined,
                }
            )

            if previous_strike is None:
                previous_strike = snapshot.atm_strike
                previous_change_time = snapshot.timestamp
                continue

            if snapshot.atm_strike != previous_strike:
                atm_strike_changes += 1
                if previous_change_time is not None:
                    holding_seconds = (snapshot.timestamp - previous_change_time).total_seconds()
                    strike_holding_seconds.append(holding_seconds)
                    rollover_intervals_seconds.append(holding_seconds)

                previous_strike = snapshot.atm_strike
                previous_change_time = snapshot.timestamp

        if previous_change_time is not None and market.snapshots:
            final_holding_seconds = (
                market.snapshots[-1].timestamp - previous_change_time
            ).total_seconds()
            strike_holding_seconds.append(final_holding_seconds)

        premium_decay_by_underlying[underlying.value] = (
            first_combined - last_combined
            if first_combined is not None and last_combined is not None
            else None
        )

    return {
        "type": "atm_straddle",
        "atm_strike_timeline": timeline,
        "atm_strike_changes": atm_strike_changes,
        "number_of_rollovers": atm_strike_changes,
        "average_strike_holding_duration_seconds": (
            mean(strike_holding_seconds) if strike_holding_seconds else None
        ),
        "longest_strike_holding_duration_seconds": (
            max(strike_holding_seconds) if strike_holding_seconds else None
        ),
        "average_time_between_rollovers_seconds": (
            mean(rollover_intervals_seconds) if rollover_intervals_seconds else None
        ),
        "average_ce_premium": mean(ce_premiums) if ce_premiums else None,
        "average_pe_premium": mean(pe_premiums) if pe_premiums else None,
        "average_combined_premium": (
            mean(combined_premiums) if combined_premiums else None
        ),
        "premium_decay_through_day": premium_decay_by_underlying,
    }
