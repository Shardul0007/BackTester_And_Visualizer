"""
Implementation of the ATM Straddle strategy.
"""

from models.market_snapshot import MarketSnapshot
from models.portfolio_view import PortfolioView
from models.trading_signal import TradingSignal, SignalType
from engine.strategy import Strategy


class ATMStraddleStrategy(Strategy):
    """
    Executes the following logic for a given underlying:
    
    1. Determine ATM strike using the futures price.
    2. If no position exists: BUY_PAIR at ATM strike.
    3. If ATM strike changed: EXIT_PAIR for previous strike, BUY_PAIR for new strike.
    4. At end of day (e.g., 15:30:00), generate EXIT_ALL signal.
    """

    def on_snapshot(
        self,
        snapshot: MarketSnapshot,
        portfolio_view: PortfolioView,
    ) -> list[TradingSignal]:
        
        signals: list[TradingSignal] = []
        underlying = snapshot.future.instrument.underlying

        # Check if it's the end of the day (e.g., 15:30:00)
        # Assignment says "At day end close all the positions"
        if snapshot.timestamp.hour == 15 and snapshot.timestamp.minute >= 30:
            if portfolio_view.has_position:
                signals.append(
                    TradingSignal(
                        signal_type=SignalType.EXIT_ALL,
                        underlying=underlying
                    )
                )
            return signals

        atm_strike = snapshot.atm_strike

        if not portfolio_view.has_position:
            signals.append(
                TradingSignal(
                    signal_type=SignalType.BUY_PAIR,
                    underlying=underlying,
                    strike=atm_strike
                )
            )
        else:
            held_strike = portfolio_view.held_strike
            if held_strike != atm_strike:
                signals.append(
                    TradingSignal(
                        signal_type=SignalType.EXIT_PAIR,
                        underlying=underlying,
                        strike=held_strike
                    )
                )
                signals.append(
                    TradingSignal(
                        signal_type=SignalType.BUY_PAIR,
                        underlying=underlying,
                        strike=atm_strike
                    )
                )

        return signals
