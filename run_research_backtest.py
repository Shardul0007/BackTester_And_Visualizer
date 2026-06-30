"""Run the ATM straddle backtest and generate research artifacts."""

from __future__ import annotations

import argparse
import subprocess
import time
import tracemalloc
from datetime import datetime
from pathlib import Path

from analytics.calculator import build_analytics
from analytics.models import BacktestMetadata, SystemMetrics
from analytics.strategy_insights import build_atm_strategy_insights
from dashboard.html_dashboard import generate_dashboard
from data.market_builder import build_markets
from data.trading_day_loader import TradingDayLoader
from engine.atm_straddle_strategy import ATMStraddleStrategy
from engine.backtester import Backtester
from engine.execution_engine import ExecutionEngine
from engine.portfolio import Portfolio
from reporting.exporter import export_results
from reporting.html_report import generate_html_report
from reporting.pdf_report import generate_pdf_report


def main() -> None:
    args = _parse_args()
    data_path = Path(args.data)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    tracemalloc.start()
    total_start = time.perf_counter()

    load_start = time.perf_counter()
    raw_market_data = TradingDayLoader(data_path).load()
    loading_time = time.perf_counter() - load_start

    build_start = time.perf_counter()
    markets = build_markets(raw_market_data)
    market_build_time = time.perf_counter() - build_start

    portfolio = Portfolio(initial_cash=args.initial_cash)
    backtester = Backtester(portfolio=portfolio, execution_engine=ExecutionEngine())
    for underlying in markets:
        backtester.add_strategy(underlying, ATMStraddleStrategy())

    backtest_start = time.perf_counter()
    backtester.run(markets)
    backtest_time = time.perf_counter() - backtest_start

    current_memory, peak_memory = tracemalloc.get_traced_memory()
    del current_memory

    configuration = {
        "initial_cash": args.initial_cash,
        "position_size": 1,
        "transaction_cost": 0.0,
        "slippage": 0.0,
        "data": str(data_path),
        "output": str(output_dir),
        "strategy": "ATMStraddleStrategy",
        "project_version": args.project_version,
        "engine_version": args.engine_version,
        "dataset_version": data_path.name,
    }
    metadata = BacktestMetadata(
        run_timestamp=datetime.now().isoformat(timespec="seconds"),
        project_version=args.project_version,
        author=args.author,
        strategy_name="ATMStraddleStrategy",
        dataset=str(data_path),
        dataset_version=data_path.name,
        engine_version=args.engine_version,
        git_commit_hash=_git_commit_hash(),
        configuration=configuration,
    )
    system = SystemMetrics(
        csv_loading_time=loading_time,
        market_build_time=market_build_time,
        backtest_time=backtest_time,
        peak_memory_usage_mb=peak_memory / (1024 * 1024),
    )

    analytics_start = time.perf_counter()
    strategy_insights = build_atm_strategy_insights(markets)
    result = build_analytics(
        portfolio=portfolio,
        markets=markets,
        raw_market_data=raw_market_data,
        configuration=configuration,
        metadata=metadata,
        system_metrics=system,
        strategy_insights=strategy_insights,
    )
    result.system.analytics_time = time.perf_counter() - analytics_start

    dashboard_start = time.perf_counter()
    dashboard_path = generate_dashboard(result, output_dir / "dashboard.html")
    html_report_path = generate_html_report(result, output_dir / "report.html")
    pdf_report_path = generate_pdf_report(result, output_dir / "report.pdf")
    result.system.dashboard_generation_time = time.perf_counter() - dashboard_start

    result.system.total_runtime = time.perf_counter() - total_start
    export_paths = export_results(result, output_dir)

    # Regenerate HTML/PDF once so their system section includes final timings.
    dashboard_path = generate_dashboard(result, output_dir / "dashboard.html")
    html_report_path = generate_html_report(result, output_dir / "report.html")
    pdf_report_path = generate_pdf_report(result, output_dir / "report.pdf")

    tracemalloc.stop()

    print("Backtest analytics generated:")
    print(f"  Dashboard: {dashboard_path}")
    print(f"  HTML report: {html_report_path}")
    print(f"  PDF report: {pdf_report_path}")
    for name, path in export_paths.items():
        print(f"  {name}: {path}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the backtest and generate analytics/dashboard artifacts.",
    )
    parser.add_argument(
        "--data",
        default="NSE_20221118",
        help="Trading day directory containing Futures and Options folders.",
    )
    parser.add_argument(
        "--output",
        default="results",
        help="Directory where result artifacts should be written.",
    )
    parser.add_argument(
        "--initial-cash",
        type=float,
        default=1_000_000.0,
        help="Starting cash used by Portfolio and return calculations.",
    )
    parser.add_argument(
        "--project-version",
        default="1.0.0",
        help="Project version written to reports and dashboards.",
    )
    parser.add_argument(
        "--engine-version",
        default="1.0.0",
        help="Backtest engine version written to reports and dashboards.",
    )
    parser.add_argument(
        "--author",
        default=None,
        help="Optional author name written to reports and dashboards.",
    )
    return parser.parse_args()


def _git_commit_hash() -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None

    return completed.stdout.strip() or None


if __name__ == "__main__":
    main()
