"""Clean result exports for post-backtest analysis."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from analytics.models import AnalyticsResult


def export_results(result: AnalyticsResult, output_dir: str | Path = "results") -> dict[str, Path]:
    """
    Write the standard result artifacts.

    The exports are intentionally flat and tool-friendly so a researcher can
    inspect the run without rerunning the simulation.
    """

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    analytics_path = output_path / "analytics.json"
    summary_path = output_path / "summary.json"
    trades_path = output_path / "trades.csv"
    daily_summary_path = output_path / "daily_summary.csv"
    positions_path = output_path / "positions.csv"
    validation_path = output_path / "validation_report.json"
    configuration_path = output_path / "configuration.json"

    payload = result.to_dict()
    _write_json(analytics_path, payload)
    _write_json(summary_path, _build_summary(result))
    _write_csv(trades_path, result.trade_rows, _trade_headers())
    _write_csv(daily_summary_path, result.daily_summary, _daily_summary_headers())
    _write_csv(positions_path, result.position_rows, _position_headers())
    _write_json(validation_path, result.validation_report)
    _write_json(configuration_path, result.metadata.configuration)

    return {
        "analytics": analytics_path,
        "summary": summary_path,
        "trades": trades_path,
        "daily_summary": daily_summary_path,
        "positions": positions_path,
        "validation_report": validation_path,
        "configuration": configuration_path,
    }


def _build_summary(result: AnalyticsResult) -> dict[str, Any]:
    return {
        "metadata": asdict(result.metadata),
        "executive_summary": {
            "final_portfolio_value": result.performance.final_portfolio_value,
            "total_pnl": result.performance.total_pnl,
            "return_percent": result.performance.return_percent,
            "win_rate": result.performance.win_rate,
            "profit_factor": result.performance.profit_factor,
            "maximum_drawdown": result.performance.maximum_drawdown,
            "number_of_trades": result.performance.number_of_trades,
            "total_trading_days": result.backtest_quality.total_trading_days,
        },
        "data_quality": asdict(result.data_quality),
        "system": asdict(result.system),
    }


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str, allow_nan=False),
        encoding="utf-8",
    )


def _write_csv(path: Path, rows: list[dict[str, Any]], headers: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _trade_headers() -> list[str]:
    return [
        "trade_id",
        "instrument",
        "symbol",
        "underlying",
        "instrument_type",
        "option_type",
        "strike",
        "expiry",
        "quantity",
        "entry_time",
        "exit_time",
        "entry_price",
        "exit_price",
        "pnl",
        "holding_seconds",
        "holding_minutes",
    ]


def _daily_summary_headers() -> list[str]:
    return [
        "date",
        "trades",
        "pnl",
        "cumulative_pnl",
        "winning_trades",
        "losing_trades",
        "win_rate",
        "drawdown",
        "rollovers",
    ]


def _position_headers() -> list[str]:
    return [
        "instrument",
        "symbol",
        "underlying",
        "instrument_type",
        "option_type",
        "strike",
        "expiry",
        "quantity",
        "entry_time",
        "entry_price",
        "last_price",
        "unrealized_pnl",
        "status",
    ]
