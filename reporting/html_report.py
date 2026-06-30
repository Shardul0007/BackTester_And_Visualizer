"""Print-friendly HTML report generation."""

from __future__ import annotations

from dataclasses import asdict
from html import escape
from pathlib import Path

from analytics.models import AnalyticsResult


def generate_html_report(
    result: AnalyticsResult,
    output_path: str | Path = "results/report.html",
) -> Path:
    """Write a professional, print-friendly report."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_html(result), encoding="utf-8")
    return path


def _html(result: AnalyticsResult) -> str:
    p = result.performance
    q = result.backtest_quality
    d = result.data_quality
    s = result.system

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Backtest Analytics Report</title>
  <style>
    body {{
      margin: 0;
      color: #171a1f;
      background: #ffffff;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 13px;
      line-height: 1.5;
      letter-spacing: 0;
    }}
    main {{ max-width: 1040px; margin: 0 auto; padding: 34px 42px; }}
    h1 {{ margin: 0 0 4px; font-size: 28px; line-height: 1.2; }}
    h2 {{ margin: 30px 0 10px; font-size: 17px; border-bottom: 1px solid #d8dde6; padding-bottom: 7px; }}
    h3 {{ margin: 16px 0 6px; font-size: 14px; color: #344054; }}
    a {{ color: #1f77b4; text-decoration: none; }}
    .meta {{ color: #667085; margin-bottom: 18px; }}
    .toc {{
      border: 1px solid #d8dde6;
      border-radius: 8px;
      padding: 12px 16px;
      background: #f7f8fa;
    }}
    .toc ol {{ margin: 0; padding-left: 20px; }}
    .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }}
    .metric {{ border: 1px solid #d8dde6; border-radius: 8px; padding: 12px; min-height: 74px; }}
    .label {{ color: #667085; font-size: 11px; margin-bottom: 4px; }}
    .value {{ font-size: 18px; font-weight: 700; overflow-wrap: anywhere; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
    th, td {{ padding: 7px 8px; border-bottom: 1px solid #e6e9ef; text-align: left; vertical-align: top; }}
    th {{ color: #667085; font-weight: 650; width: 34%; }}
    .positive {{ color: #17803d; }}
    .negative {{ color: #b42318; }}
    .small {{ color: #667085; font-size: 12px; }}
    @media print {{
      main {{ padding: 18px; }}
      .metric, table, h2 {{ break-inside: avoid; }}
      a {{ color: #171a1f; }}
    }}
  </style>
</head>
<body>
  <main>
    <h1>Backtest Analytics Report</h1>
    <div class="meta">{escape(_meta_line(result))}</div>

    <section class="toc">
      <h3>Table of Contents</h3>
      <ol>
        <li><a href="#executive-summary">Executive Summary</a></li>
        <li><a href="#project-metadata">Project Metadata</a></li>
        <li><a href="#architecture-summary">Architecture Summary</a></li>
        <li><a href="#performance-summary">Performance Summary</a></li>
        <li><a href="#trade-statistics">Trade Statistics</a></li>
        <li><a href="#risk-metrics">Risk Metrics</a></li>
        <li><a href="#data-quality">Data Quality</a></li>
        <li><a href="#engineering-statistics">Engineering Statistics</a></li>
        <li><a href="#conclusions">Conclusions</a></li>
      </ol>
    </section>

    <h2 id="executive-summary">Executive Summary</h2>
    <div class="grid">
      {_metric("Final Portfolio Value", p.final_portfolio_value)}
      {_metric("Total PnL", p.total_pnl, css_class=_pnl_class(p.total_pnl))}
      {_metric("Win Rate", p.win_rate, suffix="%")}
      {_metric("Profit Factor", p.profit_factor)}
      {_metric("Maximum Drawdown", p.maximum_drawdown)}
      {_metric("Trades", p.number_of_trades)}
      {_metric("Trading Days", q.total_trading_days)}
      {_metric("Data Coverage", d.data_coverage_percent, suffix="%")}
    </div>

    <h2 id="project-metadata">Project Metadata</h2>
    {_mapping_table(_metadata_table(result))}

    <h2 id="architecture-summary">Architecture Summary</h2>
    <p>The repository is organized as a modular research platform. Data loading,
    validation, time-series processing, market construction, strategy intent,
    execution, portfolio accounting, analytics, dashboarding, reporting, and
    exports are separate responsibilities.</p>
    <p class="small">Pipeline: CSV -> CSVLoader -> Validator -> TimeSeriesProcessor
    -> TradingDayLoader -> MarketBuilder -> Market -> Strategy -> TradingSignal
    -> ExecutionEngine -> Portfolio -> Analytics -> Dashboard -> Reports.</p>

    <h2 id="performance-summary">Performance Summary</h2>
    {_mapping_table(asdict(result.performance))}

    <h2 id="trade-statistics">Trade Statistics</h2>
    {_mapping_table({
        "number_of_trades": p.number_of_trades,
        "winning_trades": p.winning_trades,
        "losing_trades": p.losing_trades,
        "win_rate": p.win_rate,
        "average_profit": p.average_profit,
        "average_loss": p.average_loss,
        "largest_winner": p.largest_winner,
        "largest_loser": p.largest_loser,
        "average_trade_pnl": p.average_trade_pnl,
        "median_trade_pnl": p.median_trade_pnl,
        "average_holding_time_seconds": p.average_holding_time_seconds,
    })}

    <h2 id="risk-metrics">Risk Metrics</h2>
    {_mapping_table({
        "maximum_drawdown": p.maximum_drawdown,
        "maximum_drawdown_percent": p.maximum_drawdown_percent,
        "maximum_drawdown_duration_seconds": p.maximum_drawdown_duration_seconds,
        "profit_factor": p.profit_factor,
        "expectancy": p.expectancy,
    })}

    <h2 id="data-quality">Data Quality</h2>
    {_mapping_table(asdict(result.data_quality))}

    <h2>Validation Summary</h2>
    {_validation_table(result)}

    <h2 id="engineering-statistics">Engineering Statistics</h2>
    {_mapping_table(asdict(result.system))}

    <h2 id="conclusions">Conclusions</h2>
    <p>{escape(_conclusion(result))}</p>
  </main>
</body>
</html>
"""


def _meta_line(result: AnalyticsResult) -> str:
    meta = result.metadata
    parts = [
        meta.strategy_name,
        meta.dataset,
        meta.run_timestamp,
        f"v{meta.project_version}" if meta.project_version else None,
        f"git {meta.git_commit_hash}" if meta.git_commit_hash else None,
    ]
    return " | ".join(part for part in parts if part)


def _metadata_table(result: AnalyticsResult) -> dict[str, object]:
    meta = result.metadata
    return {
        "project_version": meta.project_version,
        "author": meta.author,
        "run_timestamp": meta.run_timestamp,
        "strategy": meta.strategy_name,
        "dataset": meta.dataset,
        "dataset_version": meta.dataset_version,
        "engine_version": meta.engine_version,
        "git_commit_hash": meta.git_commit_hash,
        "configuration": meta.configuration,
    }


def _metric(label: str, value: object, suffix: str = "", css_class: str = "") -> str:
    class_attr = f" {css_class}" if css_class else ""
    return (
        '<div class="metric">'
        f'<div class="label">{escape(label)}</div>'
        f'<div class="value{class_attr}">{escape(_format_value(value, suffix))}</div>'
        "</div>"
    )


def _mapping_table(mapping: dict[str, object]) -> str:
    rows = "".join(
        "<tr>"
        f"<th>{escape(str(key))}</th>"
        f"<td>{escape(_format_value(value))}</td>"
        "</tr>"
        for key, value in mapping.items()
    )
    return f"<table><tbody>{rows}</tbody></table>"


def _validation_table(result: AnalyticsResult) -> str:
    if not result.validation_report:
        return "<p>No validation issues were recorded.</p>"

    rows = "".join(
        "<tr>"
        f"<td>{escape(row['file'])}</td>"
        f"<td>{escape(row['severity'])}</td>"
        f"<td>{escape(row['message'])}</td>"
        "</tr>"
        for row in result.validation_report[:100]
    )
    return (
        "<table><thead><tr><th>File</th><th>Severity</th><th>Message</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
    )


def _conclusion(result: AnalyticsResult) -> str:
    performance = result.performance
    data_quality = result.data_quality

    if performance.number_of_trades == 0:
        return "No closed trades were available, so performance confidence is limited."

    quality_text = "Data validation did not record errors."
    if data_quality.validation_errors:
        quality_text = "Validation errors were recorded and should be investigated before trusting this run."
    elif data_quality.data_coverage_percent is not None and data_quality.data_coverage_percent < 90:
        quality_text = "Data coverage is below 90%, so the result should be treated as diagnostic."

    if performance.total_pnl > 0:
        return (
            "The run produced positive PnL. Review drawdown, trade concentration, "
            f"and daily outcomes before trusting the strategy out of sample. {quality_text}"
        )

    return (
        "The run did not produce positive PnL. Inspect the trade distribution, "
        f"ATM rollover behavior, and risk profile before further tuning. {quality_text}"
    )


def _format_value(value: object, suffix: str = "") -> str:
    if value is None:
        return "N/A"
    if isinstance(value, float):
        return f"{value:,.2f}{suffix}"
    if isinstance(value, dict):
        return ", ".join(f"{key}={_format_value(item)}" for key, item in value.items())
    return f"{value}{suffix}"


def _pnl_class(value: float | None) -> str:
    if value is None:
        return ""
    return "positive" if value >= 0 else "negative"
