from datetime import date, datetime

import pandas as pd

from analytics.calculator import build_analytics
from analytics.models import BacktestMetadata, SystemMetrics
from analytics.strategy_insights import build_atm_strategy_insights
from dashboard.html_dashboard import generate_dashboard
from engine.portfolio import Portfolio
from models.enums import InstrumentType, OptionType, Underlying, ValidationSeverity
from models.future_quote import FutureQuote
from models.instrument import Instrument
from models.market import Market
from models.market_snapshot import MarketSnapshot
from models.option_pair_quote import OptionPairQuote
from models.option_quote import OptionQuote
from models.option_series import OptionSeries
from models.raw_market_data import RawMarketData
from models.trade import Trade
from models.validation import ValidationResult
from reporting.exporter import export_results
from reporting.html_report import generate_html_report
from reporting.pdf_report import generate_pdf_report


def test_build_analytics_core_metrics_and_data_quality():
    portfolio = Portfolio(initial_cash=100000.0)
    call = _option_instrument(18000, OptionType.CALL)
    put = _option_instrument(18000, OptionType.PUT)
    portfolio.trades.extend(
        [
            Trade(
                instrument=call,
                quantity=1,
                entry_time=datetime(2022, 11, 18, 9, 15),
                entry_price=100.0,
                exit_time=datetime(2022, 11, 18, 9, 20),
                exit_price=150.0,
            ),
            Trade(
                instrument=put,
                quantity=1,
                entry_time=datetime(2022, 11, 18, 9, 15),
                entry_price=100.0,
                exit_time=datetime(2022, 11, 18, 9, 21),
                exit_price=80.0,
            ),
        ]
    )
    portfolio.realized_pnl = 30.0
    portfolio.mark_to_market_pnl = 30.0
    portfolio.cash = 100030.0

    market = Market(trading_date=date(2022, 11, 18), underlying=Underlying.NIFTY)
    market.add_snapshot(_snapshot(datetime(2022, 11, 18, 9, 15), 18000, 100.0, 100.0))
    market.add_snapshot(_snapshot(datetime(2022, 11, 18, 9, 16), 18000, 105.0, 95.0))
    markets = {Underlying.NIFTY: market}
    raw_market_data = _raw_market_data()

    result = build_analytics(
        portfolio=portfolio,
        markets=markets,
        raw_market_data=raw_market_data,
        configuration={"initial_cash": 100000.0},
        metadata=BacktestMetadata(
            run_timestamp="2022-11-18T16:00:00",
            strategy_name="test",
            dataset="unit",
            configuration={"initial_cash": 100000.0},
        ),
        system_metrics=SystemMetrics(backtest_time=2.0),
        strategy_insights=build_atm_strategy_insights(markets),
    )

    assert result.performance.number_of_trades == 2
    assert result.performance.total_pnl == 30.0
    assert result.performance.return_percent == 0.03
    assert result.performance.win_rate == 50.0
    assert result.performance.profit_factor == 2.5
    assert result.performance.maximum_drawdown == 20.0
    assert result.backtest_quality.total_trading_days == 1
    assert result.backtest_quality.snapshots_processed == 2
    assert result.system.snapshots_per_second == 1.0
    assert result.data_quality.files_loaded == 4
    assert result.data_quality.validation_warnings == 1
    assert result.data_quality.data_coverage_percent == 100.0


def test_exports_dashboard_and_reports_are_written(tmp_path):
    portfolio = Portfolio(initial_cash=100000.0)
    portfolio.cash = 100000.0
    result = build_analytics(
        portfolio=portfolio,
        configuration={"initial_cash": 100000.0},
        metadata=BacktestMetadata(
            run_timestamp="2022-11-18T16:00:00",
            strategy_name="empty",
            dataset="unit",
            configuration={"initial_cash": 100000.0},
        ),
    )

    paths = export_results(result, tmp_path)
    dashboard_path = generate_dashboard(result, tmp_path / "dashboard.html")
    html_report_path = generate_html_report(result, tmp_path / "report.html")
    pdf_report_path = generate_pdf_report(result, tmp_path / "report.pdf")

    assert paths["analytics"].exists()
    assert paths["summary"].exists()
    assert paths["trades"].read_text(encoding="utf-8").startswith("trade_id")
    assert dashboard_path.exists()
    assert "Backtest Analytics Dashboard" in dashboard_path.read_text(encoding="utf-8")
    assert html_report_path.exists()
    assert pdf_report_path.exists()
    assert pdf_report_path.read_bytes().startswith(b"%PDF")


def _raw_market_data() -> RawMarketData:
    warning = ValidationResult()
    warning.add_issue(ValidationSeverity.WARNING, "duplicate timestamps detected")
    dataframe = pd.DataFrame(
        {
            "Timestamp": pd.to_datetime(
                ["2022-11-18 09:15:00", "2022-11-18 09:16:00"]
            ),
            "Price": [100.0, 101.0],
            "Volume": [1, 1],
            "OpenInterest": [1, 1],
        }
    )

    series = OptionSeries(
        strike=18000,
        call_instrument=_option_instrument(18000, OptionType.CALL),
        put_instrument=_option_instrument(18000, OptionType.PUT),
        call_dataframe=dataframe,
        put_dataframe=dataframe,
    )

    return RawMarketData(
        trading_date=date(2022, 11, 18),
        futures={},
        options={Underlying.NIFTY: {18000: series}},
        validation_results={
            "NIFTY-I.csv": ValidationResult(),
            "NIFTY22112418000CE.csv": warning,
            "NIFTY22112418000PE.csv": ValidationResult(),
            "NIFTY22112418100CE.csv": ValidationResult(),
        },
    )


def _snapshot(
    timestamp: datetime,
    atm_strike: int,
    call_price: float,
    put_price: float,
) -> MarketSnapshot:
    future = FutureQuote(
        instrument=Instrument(
            underlying=Underlying.NIFTY,
            instrument_type=InstrumentType.FUTURE,
            expiry=None,
            strike=None,
            option_type=None,
            symbol="NIFTY-I",
        ),
        price=float(atm_strike),
        volume=1,
        open_interest=1,
    )
    pair = OptionPairQuote(
        call=OptionQuote(
            instrument=_option_instrument(atm_strike, OptionType.CALL),
            price=call_price,
            volume=1,
            open_interest=1,
        ),
        put=OptionQuote(
            instrument=_option_instrument(atm_strike, OptionType.PUT),
            price=put_price,
            volume=1,
            open_interest=1,
        ),
    )
    return MarketSnapshot(
        timestamp=timestamp,
        future=future,
        atm_strike=atm_strike,
        option_chain={atm_strike: pair},
    )


def _option_instrument(strike: int, option_type: OptionType) -> Instrument:
    return Instrument(
        underlying=Underlying.NIFTY,
        instrument_type=InstrumentType.OPTION,
        expiry=date(2022, 11, 24),
        strike=strike,
        option_type=option_type,
        symbol=f"NIFTY221124{strike}{option_type.value}",
    )
