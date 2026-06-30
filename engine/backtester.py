"""
Main Backtester orchestration engine.
"""

from models.enums import Underlying
from models.market import Market
from engine.portfolio import Portfolio
from engine.execution_engine import ExecutionEngine
from engine.strategy import Strategy
from models.trading_signal import (
    TradingSignal,
    SignalType,
)


class Backtester:
    """
    Orchestrates the backtesting simulation.
    """

    def __init__(self, portfolio: Portfolio, execution_engine: ExecutionEngine):
        self.portfolio = portfolio
        self.execution_engine = execution_engine
        self.strategies: dict[Underlying, Strategy] = {}

    def add_strategy(self, underlying: Underlying, strategy: Strategy) -> None:
        """
        Assigns a strategy for a specific underlying.
        """
        self.strategies[underlying] = strategy

    def run(
        self,
        markets: dict[Underlying, Market],
    ) -> None:
        """
        Run the backtest across all markets in chronological order.

        After the simulation completes, force liquidation of any
        remaining open positions using the last available snapshot
        for that underlying.
        """

        all_timestamps = set()

        for market in markets.values():
            for snapshot in market.snapshots:
                all_timestamps.add(snapshot.timestamp)

        sorted_timestamps = sorted(all_timestamps)

        market_snapshots = {
            underlying: {
                snapshot.timestamp: snapshot
                for snapshot in market.snapshots
            }
            for underlying, market in markets.items()
        }

        # ----------------------------------------
        # Main simulation loop
        # ----------------------------------------

        for timestamp in sorted_timestamps:

            for underlying, strategy in self.strategies.items():

                snapshot_dict = market_snapshots.get(underlying)

                if snapshot_dict is None:
                    continue

                snapshot = snapshot_dict.get(timestamp)

                if snapshot is None:
                    continue

                portfolio_view = self.portfolio.get_view(
                    underlying
                )

                signals = strategy.on_snapshot(
                    snapshot,
                    portfolio_view,
                )

                if signals:

                    orders = self.execution_engine.process(
                        signals,
                        snapshot,
                        self.portfolio,
                    )

                    if orders:
                        self.portfolio.apply_orders(
                            orders
                        )

                self.portfolio.mark_to_market(
                    snapshot
                )

        # ----------------------------------------
        # Final safety liquidation
        # ----------------------------------------

        for underlying in self.strategies:

            portfolio_view = self.portfolio.get_view(
                underlying
            )

            if not portfolio_view.has_position:
                continue

            last_snapshot = markets[
                underlying
            ].snapshots[-1]

            liquidation_signal = TradingSignal(
                signal_type=SignalType.EXIT_ALL,
                underlying=underlying,
            )

            orders = self.execution_engine.process(
                [liquidation_signal],
                last_snapshot,
                self.portfolio,
            )

            if orders:
                self.portfolio.apply_orders(
                    orders
                )

            # Final MTM after liquidation
            self.portfolio.mark_to_market(
                last_snapshot
            )