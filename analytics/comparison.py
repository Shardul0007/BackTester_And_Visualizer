"""Compare multiple analytics results side by side."""

from __future__ import annotations

from analytics.models import AnalyticsResult


def compare_analytics(results: list[AnalyticsResult]) -> list[dict[str, object]]:
    """Return a compact comparison table for two or more backtests."""

    rows: list[dict[str, object]] = []

    for result in results:
        performance = result.performance
        rows.append(
            {
                "strategy": result.metadata.strategy_name,
                "dataset": result.metadata.dataset,
                "final_pnl": performance.total_pnl,
                "return_percent": performance.return_percent,
                "win_rate": performance.win_rate,
                "maximum_drawdown": performance.maximum_drawdown,
                "trades": performance.number_of_trades,
                "average_holding_time_seconds": performance.average_holding_time_seconds,
                "profit_factor": performance.profit_factor,
            }
        )

    return rows
