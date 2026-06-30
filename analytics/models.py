"""Serializable analytics models.

The analytics layer intentionally stores plain values only.  It should be
safe to write these objects to JSON, CSV, HTML, or PDF without importing the
backtest engine.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class BacktestMetadata:
    """Run-level metadata shown in reports and dashboards."""

    run_timestamp: str
    project_version: str = "1.0.0"
    author: str | None = None
    strategy_name: str | None = None
    dataset: str | None = None
    dataset_version: str | None = None
    engine_version: str | None = None
    git_commit_hash: str | None = None
    configuration: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class PerformanceMetrics:
    """Core PnL, trade, and risk metrics."""

    final_portfolio_value: float
    total_pnl: float
    realized_pnl: float
    unrealized_pnl: float
    mtm: float
    return_percent: float | None
    number_of_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float | None
    average_profit: float | None
    average_loss: float | None
    largest_winner: float | None
    largest_loser: float | None
    average_trade_pnl: float | None
    median_trade_pnl: float | None
    average_holding_time_seconds: float | None
    maximum_holding_time_seconds: float | None
    minimum_holding_time_seconds: float | None
    profit_factor: float | None
    expectancy: float | None
    maximum_drawdown: float
    maximum_drawdown_percent: float | None
    maximum_drawdown_duration_seconds: float | None


@dataclass(slots=True)
class BacktestQualityMetrics:
    """Metrics that explain how much work the backtest performed."""

    total_trading_days: int
    snapshots_processed: int
    orders_generated: int | None = None
    orders_executed: int | None = None
    signals_generated: int | None = None
    average_signals_per_day: float | None = None
    average_orders_per_day: float | None = None
    atm_strike_changes: int | None = None
    average_strike_holding_duration_seconds: float | None = None
    longest_strike_holding_duration_seconds: float | None = None
    average_ce_premium: float | None = None
    average_pe_premium: float | None = None
    average_combined_premium: float | None = None
    average_daily_trades: float | None = None
    maximum_daily_trades: int | None = None


@dataclass(slots=True)
class DataQualityMetrics:
    """Validation and market-data coverage metrics."""

    trading_days_loaded: int
    files_loaded: int
    files_failed: int
    validation_warnings: int
    validation_errors: int
    incomplete_option_pairs_filtered: int | None
    tradable_strikes: int
    missing_quotes_encountered: int | None
    forward_filled_quotes: int | None
    data_coverage_percent: float | None
    missing_data_percent: float | None
    average_quotes_per_strike: float | None


@dataclass(slots=True)
class SystemMetrics:
    """Engineering/runtime metrics for a run."""

    csv_loading_time: float | None = None
    market_build_time: float | None = None
    backtest_time: float | None = None
    analytics_time: float | None = None
    dashboard_generation_time: float | None = None
    peak_memory_usage_mb: float | None = None
    total_runtime: float | None = None
    snapshots_per_second: float | None = None
    trades_per_second: float | None = None


@dataclass(slots=True)
class AnalyticsResult:
    """Complete analytics payload consumed by exports and dashboards."""

    metadata: BacktestMetadata
    performance: PerformanceMetrics
    backtest_quality: BacktestQualityMetrics
    data_quality: DataQualityMetrics
    system: SystemMetrics
    strategy_insights: dict[str, Any] = field(default_factory=dict)
    equity_curve: list[dict[str, Any]] = field(default_factory=list)
    drawdown_curve: list[dict[str, Any]] = field(default_factory=list)
    trade_rows: list[dict[str, Any]] = field(default_factory=list)
    daily_summary: list[dict[str, Any]] = field(default_factory=list)
    position_rows: list[dict[str, Any]] = field(default_factory=list)
    validation_report: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly dictionary."""

        return asdict(self)
