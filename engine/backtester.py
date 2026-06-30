"""
Main Backtester orchestration engine.
"""

from typing import Dict

from models.enums import Underlying
from models.market import Market
from engine.portfolio import Portfolio
from engine.execution_engine import ExecutionEngine
from engine.strategy import Strategy


class Backtester:
    """
    Orchestrates the backtesting simulation.
    """

    def __init__(self, portfolio: Portfolio, execution_engine: ExecutionEngine):
        self.portfolio = portfolio
        self.execution_engine = execution_engine
        self.strategies: Dict[Underlying, Strategy] = {}

    def add_strategy(self, underlying: Underlying, strategy: Strategy) -> None:
        """
        Assigns a strategy for a specific underlying.
        """
        self.strategies[underlying] = strategy

    def run(self, markets: Dict[Underlying, Market]) -> None:
        """
        Runs the simulation across all provided markets.
        Iterates through a global timeline to ensure chronological processing.
        """
        all_timestamps = set()
        for market in markets.values():
            for snapshot in market.snapshots:
                all_timestamps.add(snapshot.timestamp)
        
        sorted_timestamps = sorted(list(all_timestamps))
        
        market_snapshots = {
            underlying: {s.timestamp: s for s in market.snapshots}
            for underlying, market in markets.items()
        }

        for timestamp in sorted_timestamps:
            for underlying, strategy in self.strategies.items():
                if underlying not in market_snapshots:
                    continue
                    
                snapshot_dict = market_snapshots[underlying]
                if timestamp in snapshot_dict:
                    snapshot = snapshot_dict[timestamp]
                    
                    view = self.portfolio.get_view(underlying)
                    
                    signals = strategy.on_snapshot(snapshot, view)
                    
                    if signals:
                        orders = self.execution_engine.process(signals, snapshot, self.portfolio)
                        
                        if orders:
                            self.portfolio.apply_orders(orders)
                    
                    self.portfolio.mark_to_market(snapshot)
