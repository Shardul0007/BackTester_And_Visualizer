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

    # ATM shifts to 18100; add 18000 so the EXIT_PAIR can price the old position.
    s3 = create_mock_snapshot("2022-11-18 09:17:00", 18100)
    s3.option_chain[18000] = s1.option_chain[18000]

    # End-of-day snapshot: 18000 is absent to exercise the last_prices fallback.
    s4 = create_mock_snapshot("2022-11-18 15:30:00", 18100)
    s4.option_chain.pop(18000, None)

    for s in [s1, s2, s3, s4]:
        market.add_snapshot(s)

    backtester.run({Underlying.NIFTY: market})

    assert len(portfolio.positions) == 0
    assert len(portfolio.trades) == 4


def test_backtester_closes_positions_when_strike_absent_from_last_snapshot():
    """
    Regression test for the bug where EXIT_ALL silently skipped instruments
    whose strike was missing from the final snapshot's option_chain.

    Scenario:
    - Position is entered at strike 18000 during the day.
    - The last snapshot (15:30) does NOT include strike 18000 in its chain.
    - The portfolio must still be fully closed via the last_prices fallback.
    """
    portfolio = Portfolio(initial_cash=1000000.0)
    execution = ExecutionEngine()
    backtester = Backtester(portfolio, execution)

    strategy = ATMStraddleStrategy()
    backtester.add_strategy(Underlying.NIFTY, strategy)

    market = Market(trading_date=datetime(2022, 11, 18).date(), underlying=Underlying.NIFTY)

    # Midday: buy and mark-to-market at 18000 so last_prices is populated.
    s1 = create_mock_snapshot("2022-11-18 09:15:00", 18000)
    s2 = create_mock_snapshot("2022-11-18 09:16:00", 18000)

    # End-of-day snapshot: strike 18000 intentionally absent to reproduce the bug.
    s3 = create_mock_snapshot("2022-11-18 15:30:00", 18000)
    s3.option_chain.clear()

    for s in [s1, s2, s3]:
        market.add_snapshot(s)

    backtester.run({Underlying.NIFTY: market})

    assert portfolio.positions == {}, (
        "All positions must be closed at end of day even when the held "
        "strike is absent from the final snapshot's option_chain."
    )


if __name__ == "__main__":
    pytest.main(["-s", __file__])
