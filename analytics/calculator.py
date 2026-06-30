"""Core analytics calculations for completed backtest runs."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from statistics import mean, median
from typing import Any, Mapping

from data.filename_parser import FilenameParser
from engine.portfolio import Portfolio
from models.enums import InstrumentType, OptionType, ValidationSeverity
from models.market import Market
from models.raw_market_data import RawMarketData
from models.trade import Trade

from analytics.models import (
    AnalyticsResult,
    BacktestMetadata,
    BacktestQualityMetrics,
    DataQualityMetrics,
    PerformanceMetrics,
    SystemMetrics,
)


def build_analytics(
    *,
    portfolio: Portfolio,
    markets: Mapping[Any, Market] | None = None,
    raw_market_data: RawMarketData | None = None,
    configuration: Mapping[str, Any] | None = None,
    metadata: BacktestMetadata | None = None,
    system_metrics: SystemMetrics | None = None,
    strategy_insights: Mapping[str, Any] | None = None,
    execution_statistics: Mapping[str, int] | None = None,
) -> AnalyticsResult:
    """
    Build a complete analytics result without mutating engine state.

    Parameters are deliberately consumer-oriented: final Portfolio, optional
    Market objects, optional validation data, and run metadata.  Missing
    instrumentation is represented as ``None`` instead of inferred silently.
    """

    markets = markets or {}
    configuration = dict(configuration or {})
    strategy_insights = dict(strategy_insights or {})
    execution_statistics = dict(execution_statistics or {})

    if metadata is None:
        metadata = BacktestMetadata(
            run_timestamp=datetime.now().isoformat(timespec="seconds"),
            configuration=configuration,
        )

    if not metadata.configuration:
        metadata.configuration = configuration

    system = system_metrics or SystemMetrics()
    trade_rows = _build_trade_rows(portfolio.trades)
    position_rows = _build_position_rows(portfolio)
    daily_summary = _build_daily_summary(trade_rows)
    start_time = _first_market_timestamp(markets) or _first_trade_entry(portfolio.trades)
    initial_cash = _initial_cash(portfolio, configuration)
    equity_curve, drawdown_curve = _build_equity_curves(
        trade_rows=trade_rows,
        initial_cash=initial_cash,
        start_time=start_time,
    )

    performance = _build_performance_metrics(
        portfolio=portfolio,
        trade_rows=trade_rows,
        initial_cash=initial_cash,
        equity_curve=equity_curve,
    )
    backtest_quality = _build_backtest_quality(
        markets=markets,
        trade_rows=trade_rows,
        daily_summary=daily_summary,
        strategy_insights=strategy_insights,
        execution_statistics=execution_statistics,
    )
    data_quality, validation_report = _build_data_quality(
        raw_market_data=raw_market_data,
        markets=markets,
    )

    _derive_system_rates(
        system=system,
        snapshots_processed=backtest_quality.snapshots_processed,
        trades=len(trade_rows),
    )

    return AnalyticsResult(
        metadata=metadata,
        performance=performance,
        backtest_quality=backtest_quality,
        data_quality=data_quality,
        system=system,
        strategy_insights=strategy_insights,
        equity_curve=equity_curve,
        drawdown_curve=drawdown_curve,
        trade_rows=trade_rows,
        daily_summary=daily_summary,
        position_rows=position_rows,
        validation_report=validation_report,
    )


def _build_trade_rows(trades: list[Trade]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for trade_id, trade in enumerate(
        sorted(trades, key=lambda item: (item.exit_time, item.entry_time, str(item.instrument))),
        start=1,
    ):
        instrument = trade.instrument
        holding_seconds = (trade.exit_time - trade.entry_time).total_seconds()
        option_type = instrument.option_type.value if instrument.option_type else None

        rows.append(
            {
                "trade_id": trade_id,
                "instrument": instrument.display_name,
                "symbol": instrument.symbol,
                "underlying": instrument.underlying.value,
                "instrument_type": instrument.instrument_type.value,
                "option_type": option_type,
                "strike": instrument.strike,
                "expiry": instrument.expiry.isoformat() if instrument.expiry else None,
                "quantity": trade.quantity,
                "entry_time": trade.entry_time.isoformat(sep=" "),
                "exit_time": trade.exit_time.isoformat(sep=" "),
                "entry_price": trade.entry_price,
                "exit_price": trade.exit_price,
                "pnl": trade.realized_pnl,
                "holding_seconds": holding_seconds,
                "holding_minutes": holding_seconds / 60.0,
            }
        )

    return rows


def _build_position_rows(portfolio: Portfolio) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for instrument, position in sorted(
        portfolio.positions.items(),
        key=lambda item: str(item[0]),
    ):
        last_price = portfolio.last_prices.get(instrument)
        unrealized_pnl = None
        if last_price is not None:
            unrealized_pnl = (last_price - position.entry_price) * position.quantity

        rows.append(
            {
                "instrument": instrument.display_name,
                "symbol": instrument.symbol,
                "underlying": instrument.underlying.value,
                "instrument_type": instrument.instrument_type.value,
                "option_type": instrument.option_type.value if instrument.option_type else None,
                "strike": instrument.strike,
                "expiry": instrument.expiry.isoformat() if instrument.expiry else None,
                "quantity": position.quantity,
                "entry_time": position.entry_time.isoformat(sep=" "),
                "entry_price": position.entry_price,
                "last_price": last_price,
                "unrealized_pnl": unrealized_pnl,
                "status": position.status.value,
            }
        )

    return rows


def _build_daily_summary(trade_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in trade_rows:
        grouped[row["exit_time"][:10]].append(row)

    summary: list[dict[str, Any]] = []
    cumulative_pnl = 0.0
    peak_pnl = 0.0

    for trade_date in sorted(grouped):
        rows = grouped[trade_date]
        pnls = [row["pnl"] for row in rows]
        wins = [pnl for pnl in pnls if pnl > 0]
        losses = [pnl for pnl in pnls if pnl < 0]
        daily_pnl = sum(pnls)
        cumulative_pnl += daily_pnl
        peak_pnl = max(peak_pnl, cumulative_pnl)
        drawdown = peak_pnl - cumulative_pnl

        summary.append(
            {
                "date": trade_date,
                "trades": len(rows),
                "pnl": daily_pnl,
                "cumulative_pnl": cumulative_pnl,
                "winning_trades": len(wins),
                "losing_trades": len(losses),
                "win_rate": _percentage(len(wins), len(rows)),
                "drawdown": drawdown,
                "rollovers": None,
            }
        )

    return summary


def _build_equity_curves(
    *,
    trade_rows: list[dict[str, Any]],
    initial_cash: float | None,
    start_time: datetime | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    base_equity = initial_cash if initial_cash is not None else 0.0
    cumulative_pnl = 0.0
    peak_equity = base_equity
    equity_curve: list[dict[str, Any]] = []

    if start_time is not None:
        equity_curve.append(
            {
                "timestamp": start_time.isoformat(sep=" "),
                "realized_pnl": 0.0,
                "equity": base_equity,
                "running_max": peak_equity,
                "drawdown": 0.0,
                "drawdown_percent": 0.0 if peak_equity else None,
            }
        )

    for row in trade_rows:
        cumulative_pnl += row["pnl"]
        equity = base_equity + cumulative_pnl
        peak_equity = max(peak_equity, equity)
        drawdown = peak_equity - equity

        equity_curve.append(
            {
                "timestamp": row["exit_time"],
                "realized_pnl": cumulative_pnl,
                "equity": equity,
                "running_max": peak_equity,
                "drawdown": drawdown,
                "drawdown_percent": _percentage(drawdown, peak_equity),
            }
        )

    drawdown_curve = [
        {
            "timestamp": row["timestamp"],
            "drawdown": row["drawdown"],
            "drawdown_percent": row["drawdown_percent"],
            "running_max": row["running_max"],
        }
        for row in equity_curve
    ]

    return equity_curve, drawdown_curve


def _build_performance_metrics(
    *,
    portfolio: Portfolio,
    trade_rows: list[dict[str, Any]],
    initial_cash: float | None,
    equity_curve: list[dict[str, Any]],
) -> PerformanceMetrics:
    pnls = [row["pnl"] for row in trade_rows]
    wins = [pnl for pnl in pnls if pnl > 0]
    losses = [pnl for pnl in pnls if pnl < 0]
    holding_times = [row["holding_seconds"] for row in trade_rows]
    gross_profit = sum(wins)
    gross_loss = sum(losses)
    total_pnl = portfolio.realized_pnl + portfolio.unrealized_pnl
    max_drawdown = max((row["drawdown"] for row in equity_curve), default=0.0)
    max_drawdown_percent = max(
        (
            row["drawdown_percent"]
            for row in equity_curve
            if row["drawdown_percent"] is not None
        ),
        default=None,
    )

    return PerformanceMetrics(
        final_portfolio_value=portfolio.portfolio_value,
        total_pnl=total_pnl,
        realized_pnl=portfolio.realized_pnl,
        unrealized_pnl=portfolio.unrealized_pnl,
        mtm=portfolio.mark_to_market_pnl,
        return_percent=_percentage(total_pnl, initial_cash),
        number_of_trades=len(trade_rows),
        winning_trades=len(wins),
        losing_trades=len(losses),
        win_rate=_percentage(len(wins), len(trade_rows)),
        average_profit=mean(wins) if wins else None,
        average_loss=mean(losses) if losses else None,
        largest_winner=max(wins) if wins else None,
        largest_loser=min(losses) if losses else None,
        average_trade_pnl=mean(pnls) if pnls else None,
        median_trade_pnl=median(pnls) if pnls else None,
        average_holding_time_seconds=mean(holding_times) if holding_times else None,
        maximum_holding_time_seconds=max(holding_times) if holding_times else None,
        minimum_holding_time_seconds=min(holding_times) if holding_times else None,
        profit_factor=(gross_profit / abs(gross_loss)) if gross_loss else None,
        expectancy=mean(pnls) if pnls else None,
        maximum_drawdown=max_drawdown,
        maximum_drawdown_percent=max_drawdown_percent,
        maximum_drawdown_duration_seconds=_max_drawdown_duration_seconds(equity_curve),
    )


def _build_backtest_quality(
    *,
    markets: Mapping[Any, Market],
    trade_rows: list[dict[str, Any]],
    daily_summary: list[dict[str, Any]],
    strategy_insights: Mapping[str, Any],
    execution_statistics: Mapping[str, int],
) -> BacktestQualityMetrics:
    trading_dates = {market.trading_date for market in markets.values()}
    total_trading_days = len(trading_dates) if trading_dates else len(daily_summary)
    snapshots_processed = sum(len(market.snapshots) for market in markets.values())
    orders_generated = execution_statistics.get("orders_generated")
    orders_executed = execution_statistics.get("orders_executed")
    signals_generated = execution_statistics.get("signals_generated")

    return BacktestQualityMetrics(
        total_trading_days=total_trading_days,
        snapshots_processed=snapshots_processed,
        orders_generated=orders_generated,
        orders_executed=orders_executed,
        signals_generated=signals_generated,
        average_signals_per_day=_safe_divide(signals_generated, total_trading_days),
        average_orders_per_day=_safe_divide(orders_executed, total_trading_days),
        atm_strike_changes=strategy_insights.get("atm_strike_changes"),
        average_strike_holding_duration_seconds=strategy_insights.get(
            "average_strike_holding_duration_seconds"
        ),
        longest_strike_holding_duration_seconds=strategy_insights.get(
            "longest_strike_holding_duration_seconds"
        ),
        average_ce_premium=strategy_insights.get("average_ce_premium"),
        average_pe_premium=strategy_insights.get("average_pe_premium"),
        average_combined_premium=strategy_insights.get("average_combined_premium"),
        average_daily_trades=_safe_divide(len(trade_rows), total_trading_days),
        maximum_daily_trades=max(
            (row["trades"] for row in daily_summary),
            default=0,
        ),
    )


def _build_data_quality(
    *,
    raw_market_data: RawMarketData | None,
    markets: Mapping[Any, Market],
) -> tuple[DataQualityMetrics, list[dict[str, Any]]]:
    validation_report: list[dict[str, Any]] = []
    validation_results = raw_market_data.validation_results if raw_market_data else {}
    warnings = 0
    errors = 0
    files_failed = 0

    for file_name, result in sorted(validation_results.items()):
        if not result.passed:
            files_failed += 1

        for issue in result.issues:
            if issue.severity == ValidationSeverity.WARNING:
                warnings += 1
            elif issue.severity == ValidationSeverity.ERROR:
                errors += 1

            validation_report.append(
                {
                    "file": file_name,
                    "severity": issue.severity.value,
                    "message": issue.message,
                }
            )

    tradable_strikes = _tradable_strike_count(raw_market_data)
    coverage = _market_coverage(raw_market_data=raw_market_data, markets=markets)

    metrics = DataQualityMetrics(
        trading_days_loaded=1 if raw_market_data else len({m.trading_date for m in markets.values()}),
        files_loaded=len(validation_results),
        files_failed=files_failed,
        validation_warnings=warnings,
        validation_errors=errors,
        incomplete_option_pairs_filtered=_incomplete_option_pair_count(validation_results),
        tradable_strikes=tradable_strikes,
        missing_quotes_encountered=coverage["missing_quotes_encountered"],
        forward_filled_quotes=None,
        data_coverage_percent=coverage["data_coverage_percent"],
        missing_data_percent=coverage["missing_data_percent"],
        average_quotes_per_strike=_average_quotes_per_strike(raw_market_data),
    )

    return metrics, validation_report


def _market_coverage(
    *,
    raw_market_data: RawMarketData | None,
    markets: Mapping[Any, Market],
) -> dict[str, float | int | None]:
    expected_quote_pairs = 0
    observed_quote_pairs = 0

    for underlying, market in markets.items():
        if raw_market_data and underlying in raw_market_data.options:
            expected_strikes = len(raw_market_data.options[underlying])
        else:
            expected_strikes = max(
                (len(snapshot.option_chain) for snapshot in market.snapshots),
                default=0,
            )

        for snapshot in market.snapshots:
            expected_quote_pairs += expected_strikes
            observed_quote_pairs += len(snapshot.option_chain)

    if not expected_quote_pairs:
        return {
            "missing_quotes_encountered": None,
            "data_coverage_percent": None,
            "missing_data_percent": None,
        }

    missing = max(expected_quote_pairs - observed_quote_pairs, 0)
    coverage_percent = (observed_quote_pairs / expected_quote_pairs) * 100.0

    return {
        "missing_quotes_encountered": missing,
        "data_coverage_percent": coverage_percent,
        "missing_data_percent": 100.0 - coverage_percent,
    }


def _incomplete_option_pair_count(validation_results: Mapping[str, Any]) -> int | None:
    if not validation_results:
        return None

    pair_map: dict[tuple[str, str, int], set[OptionType]] = defaultdict(set)

    for file_name in validation_results:
        try:
            instrument = FilenameParser.parse(file_name)
        except (ValueError, TypeError):
            continue

        if instrument.instrument_type != InstrumentType.OPTION:
            continue

        if instrument.expiry is None or instrument.strike is None or instrument.option_type is None:
            continue

        key = (
            instrument.underlying.value,
            instrument.expiry.isoformat(),
            instrument.strike,
        )
        pair_map[key].add(instrument.option_type)

    return sum(
        1
        for option_types in pair_map.values()
        if OptionType.CALL not in option_types or OptionType.PUT not in option_types
    )


def _average_quotes_per_strike(raw_market_data: RawMarketData | None) -> float | None:
    if raw_market_data is None:
        return None

    quote_counts: list[float] = []

    for strike_map in raw_market_data.options.values():
        for series in strike_map.values():
            call_count = len(series.call_dataframe) if series.call_dataframe is not None else 0
            put_count = len(series.put_dataframe) if series.put_dataframe is not None else 0
            quote_counts.append((call_count + put_count) / 2.0)

    return mean(quote_counts) if quote_counts else None


def _tradable_strike_count(raw_market_data: RawMarketData | None) -> int:
    if raw_market_data is None:
        return 0

    return sum(len(strike_map) for strike_map in raw_market_data.options.values())


def _initial_cash(portfolio: Portfolio, configuration: Mapping[str, Any]) -> float | None:
    configured = configuration.get("initial_cash")
    if configured is not None:
        return float(configured)

    if not portfolio.positions:
        return portfolio.portfolio_value - portfolio.realized_pnl

    return None


def _first_market_timestamp(markets: Mapping[Any, Market]) -> datetime | None:
    timestamps = [
        market.snapshots[0].timestamp
        for market in markets.values()
        if market.snapshots
    ]
    return min(timestamps) if timestamps else None


def _first_trade_entry(trades: list[Trade]) -> datetime | None:
    return min((trade.entry_time for trade in trades), default=None)


def _max_drawdown_duration_seconds(equity_curve: list[dict[str, Any]]) -> float | None:
    if not equity_curve:
        return None

    underwater_start: datetime | None = None
    max_duration = 0.0

    for row in equity_curve:
        timestamp = datetime.fromisoformat(row["timestamp"])
        drawdown = row["drawdown"]

        if drawdown > 0 and underwater_start is None:
            underwater_start = timestamp
        elif drawdown == 0 and underwater_start is not None:
            max_duration = max(max_duration, (timestamp - underwater_start).total_seconds())
            underwater_start = None

    if underwater_start is not None:
        last_timestamp = datetime.fromisoformat(equity_curve[-1]["timestamp"])
        max_duration = max(max_duration, (last_timestamp - underwater_start).total_seconds())

    return max_duration


def _derive_system_rates(
    *,
    system: SystemMetrics,
    snapshots_processed: int,
    trades: int,
) -> None:
    if system.backtest_time and system.backtest_time > 0:
        system.snapshots_per_second = snapshots_processed / system.backtest_time
        system.trades_per_second = trades / system.backtest_time


def _percentage(numerator: float | int | None, denominator: float | int | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return (float(numerator) / float(denominator)) * 100.0


def _safe_divide(numerator: float | int | None, denominator: float | int | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return float(numerator) / float(denominator)
