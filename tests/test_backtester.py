import pytest
from datetime import datetime

from models.enums import Underlying
from models.market import Market
from engine.portfolio import Portfolio
from engine.execution_engine import ExecutionEngine
from engine.atm_straddle_strategy import ATMStraddleStrategy
from engine.backtester import Backtester
from tests.test_execution import create_mock_snapshot


def test_backtester():
    portfolio = Portfolio(initial_cash=1000000.0)
    execution = ExecutionEngine()
    backtester = Backtester(portfolio, execution)
    
    strategy = ATMStraddleStrategy()
    backtester.add_strategy(Underlying.NIFTY, strategy)
    
    market = Market(trading_date=datetime(2022, 11, 18).date(), underlying=Underlying.NIFTY)
    
    s1 = create_mock_snapshot("2022-11-18 09:15:00", 18000)
    s2 = create_mock_snapshot("2022-11-18 09:16:00", 18000)
    
    s3 = create_mock_snapshot("2022-11-18 09:17:00", 18100)
    s3.option_chain[18000] = s1.option_chain[18000]  # Add 18000 so it can be priced/exited
    
    s4 = create_mock_snapshot("2022-11-18 15:30:00", 18100)
    s4.option_chain[18000] = s1.option_chain[18000]  # Just in case (though it should be exited at s3)
    
    for s in [s1, s2, s3, s4]:
        market.add_snapshot(s)
    
    backtester.run({Underlying.NIFTY: market})
    
    assert len(portfolio.positions) == 0
    assert len(portfolio.trades) == 4

if __name__ == "__main__":
    pytest.main(["-s", __file__])
