import pytest
from datetime import datetime

from models.enums import Underlying
from models.instrument import Instrument, InstrumentType
from models.future_quote import FutureQuote
from models.market_snapshot import MarketSnapshot
from models.portfolio_view import PortfolioView
from models.trading_signal import SignalType
from engine.atm_straddle_strategy import ATMStraddleStrategy


def create_snapshot(time_str: str, atm_strike: int) -> MarketSnapshot:
    dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    future = FutureQuote(
        instrument=Instrument(
            underlying=Underlying.NIFTY, 
            instrument_type=InstrumentType.FUTURE, 
            expiry=None, 
            strike=None, 
            option_type=None, 
            symbol="NIFTY-I"
        ),
        price=float(atm_strike), 
        volume=1, 
        open_interest=1
    )
    return MarketSnapshot(timestamp=dt, future=future, atm_strike=atm_strike, option_chain={})


def test_atm_straddle_strategy():
    strategy = ATMStraddleStrategy()
    
    # 1. No position initially -> Buy Pair
    snapshot = create_snapshot("2022-11-18 09:15:00", 18000)
    view = PortfolioView(held_strike=None)
    signals = strategy.on_snapshot(snapshot, view)
    
    assert len(signals) == 1
    assert signals[0].signal_type == SignalType.BUY_PAIR
    assert signals[0].strike == 18000

    # 2. Position exists, no strike change -> No signals
    snapshot = create_snapshot("2022-11-18 09:16:00", 18000)
    view = PortfolioView(held_strike=18000)
    signals = strategy.on_snapshot(snapshot, view)
    
    assert len(signals) == 0

    # 3. Position exists, strike changed -> Exit old, Buy new
    snapshot = create_snapshot("2022-11-18 09:17:00", 18100)
    view = PortfolioView(held_strike=18000)
    signals = strategy.on_snapshot(snapshot, view)
    
    assert len(signals) == 2
    assert signals[0].signal_type == SignalType.EXIT_PAIR
    assert signals[0].strike == 18000
    assert signals[1].signal_type == SignalType.BUY_PAIR
    assert signals[1].strike == 18100

    # 4. End of day -> Exit all
    snapshot = create_snapshot("2022-11-18 15:30:00", 18100)
    view = PortfolioView(held_strike=18100)
    signals = strategy.on_snapshot(snapshot, view)
    
    assert len(signals) == 1
    assert signals[0].signal_type == SignalType.EXIT_ALL

if __name__ == "__main__":
    pytest.main(["-s", __file__])
