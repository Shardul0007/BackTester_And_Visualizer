import pytest
from datetime import datetime

from models.enums import Underlying, OrderAction
from models.instrument import Instrument, InstrumentType
from models.future_quote import FutureQuote
from models.market_snapshot import MarketSnapshot
from models.option_quote import OptionQuote
from models.option_pair_quote import OptionPairQuote
from models.order import Order
from models.trading_signal import TradingSignal, SignalType
from engine.portfolio import Portfolio
from engine.execution_engine import ExecutionEngine


def create_mock_snapshot(time_str: str, atm_strike: int) -> MarketSnapshot:
    dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    future = FutureQuote(
        instrument=Instrument(Underlying.NIFTY, InstrumentType.FUTURE, None, None, None, "NIFTY-I"),
        price=float(atm_strike), volume=1, open_interest=1
    )
    
    # Create OptionPairQuote for the atm_strike
    ce_inst = Instrument(Underlying.NIFTY, InstrumentType.OPTION, None, atm_strike, "CE", f"NIFTY_CE_{atm_strike}")
    pe_inst = Instrument(Underlying.NIFTY, InstrumentType.OPTION, None, atm_strike, "PE", f"NIFTY_PE_{atm_strike}")
    
    ce_quote = OptionQuote(ce_inst, 100.0, 1, 1)
    pe_quote = OptionQuote(pe_inst, 100.0, 1, 1)
    
    pair = OptionPairQuote(call=ce_quote, put=pe_quote)
    
    return MarketSnapshot(timestamp=dt, future=future, atm_strike=atm_strike, option_chain={atm_strike: pair})


def test_execution_and_portfolio():
    portfolio = Portfolio(initial_cash=100000.0)
    engine = ExecutionEngine()
    
    snapshot = create_mock_snapshot("2022-11-18 09:15:00", 18000)
    
    # Test 1: Process BUY_PAIR
    signals = [TradingSignal(SignalType.BUY_PAIR, Underlying.NIFTY, 18000)]
    orders = engine.process(signals, snapshot, portfolio)
    
    assert len(orders) == 2
    assert orders[0].action == OrderAction.BUY
    assert orders[1].action == OrderAction.BUY
    assert orders[0].price == 100.0
    
    portfolio.apply_orders(orders)
    assert len(portfolio.positions) == 2
    assert portfolio.cash == 100000.0 - 200.0
    
    # Test 2: Reject Duplicate BUY_PAIR
    orders_dup = engine.process(signals, snapshot, portfolio)
    assert len(orders_dup) == 0
    
    # Test 3: Process EXIT_PAIR
    signals_exit = [TradingSignal(SignalType.EXIT_PAIR, Underlying.NIFTY, 18000)]
    
    # Move price up to test PnL
    snapshot_later = create_mock_snapshot("2022-11-18 09:20:00", 18000)
    snapshot_later.option_chain[18000].call.price = 150.0
    snapshot_later.option_chain[18000].put.price = 80.0
    
    portfolio.mark_to_market(snapshot_later)
    assert portfolio.unrealized_pnl == (50.0 - 20.0)  # +50 on CE, -20 on PE = +30
    
    orders_exit = engine.process(signals_exit, snapshot_later, portfolio)
    assert len(orders_exit) == 2
    assert orders_exit[0].action == OrderAction.SELL
    
    portfolio.apply_orders(orders_exit)
    assert len(portfolio.positions) == 0
    assert len(portfolio.trades) == 2
    assert portfolio.realized_pnl == 30.0

if __name__ == "__main__":
    pytest.main(["-s", __file__])
