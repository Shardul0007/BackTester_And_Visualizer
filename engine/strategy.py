"""
Abstract base class for all trading strategies.
"""

from abc import ABC, abstractmethod

from models.market_snapshot import MarketSnapshot
from models.portfolio_view import PortfolioView
from models.trading_signal import TradingSignal


class Strategy(ABC):
    """
    Defines the contract for all trading strategies.

    Strategies receive a MarketSnapshot and a read-only PortfolioView,
    and output a list of TradingSignals indicating their intent.
    """

    @abstractmethod
    def on_snapshot(
        self,
        snapshot: MarketSnapshot,
        portfolio_view: PortfolioView,
    ) -> list[TradingSignal]:
        """
        Process a new market snapshot and optionally generate trading signals.
        """
        pass
