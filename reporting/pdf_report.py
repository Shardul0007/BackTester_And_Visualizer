"""Dependency-free PDF summary generation."""

from __future__ import annotations

from pathlib import Path
from textwrap import wrap

from analytics.models import AnalyticsResult


def generate_pdf_report(
    result: AnalyticsResult,
    output_path: str | Path = "results/report.pdf",
) -> Path:
    """Write a compact PDF report without external dependencies."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = _report_lines(result)
    _write_simple_pdf(path, "Backtest Analytics Report", lines)
    return path


def _report_lines(result: AnalyticsResult) -> list[str]:
    p = result.performance
    q = result.backtest_quality
    d = result.data_quality
    s = result.system

    sections = [
        ("Table of Contents", [
            "1. Executive Summary",
            "2. Project Metadata",
            "3. Architecture Summary",
            "4. Performance Summary",
            "5. Trade Statistics",
            "6. Risk Metrics",
            "7. Data Quality",
            "8. Engineering Statistics",
            "9. Conclusions",
        ]),
        ("Executive Summary", [
            f"Final portfolio value: {_fmt(p.final_portfolio_value)}",
            f"Total PnL: {_fmt(p.total_pnl)}",
            f"Win rate: {_fmt(p.win_rate)}",
            f"Profit factor: {_fmt(p.profit_factor)}",
            f"Maximum drawdown: {_fmt(p.maximum_drawdown)}",
            f"Trades: {p.number_of_trades}",
            f"Trading days: {q.total_trading_days}",
            f"Data coverage %: {_fmt(d.data_coverage_percent)}",
        ]),
        ("Project Metadata", [
            f"Project version: {result.metadata.project_version or 'N/A'}",
            f"Author: {result.metadata.author or 'N/A'}",
            f"Strategy: {result.metadata.strategy_name or 'N/A'}",
            f"Dataset: {result.metadata.dataset or 'N/A'}",
            f"Dataset version: {result.metadata.dataset_version or 'N/A'}",
            f"Engine version: {result.metadata.engine_version or 'N/A'}",
            f"Run timestamp: {result.metadata.run_timestamp}",
            f"Git commit: {result.metadata.git_commit_hash or 'N/A'}",
        ]),
        ("Architecture Summary", [
            "CSV -> CSVLoader -> Validator -> TimeSeriesProcessor -> TradingDayLoader ->",
            "MarketBuilder -> Market -> Strategy -> TradingSignal -> ExecutionEngine ->",
            "Portfolio -> Analytics -> Dashboard -> Reports.",
        ]),
        ("Performance Summary", [
            f"Final portfolio value: {_fmt(p.final_portfolio_value)}",
            f"Total PnL: {_fmt(p.total_pnl)}",
            f"Realized PnL: {_fmt(p.realized_pnl)}",
            f"Unrealized PnL: {_fmt(p.unrealized_pnl)}",
            f"Return %: {_fmt(p.return_percent)}",
            f"Win rate: {_fmt(p.win_rate)}",
            f"Profit factor: {_fmt(p.profit_factor)}",
            f"Maximum drawdown: {_fmt(p.maximum_drawdown)}",
        ]),
        ("Trade Statistics", [
            f"Trades: {p.number_of_trades}",
            f"Winning trades: {p.winning_trades}",
            f"Losing trades: {p.losing_trades}",
            f"Average trade PnL: {_fmt(p.average_trade_pnl)}",
            f"Median trade PnL: {_fmt(p.median_trade_pnl)}",
            f"Average holding seconds: {_fmt(p.average_holding_time_seconds)}",
        ]),
        ("Risk Metrics", [
            f"Maximum drawdown: {_fmt(p.maximum_drawdown)}",
            f"Maximum drawdown %: {_fmt(p.maximum_drawdown_percent)}",
            f"Maximum drawdown duration seconds: {_fmt(p.maximum_drawdown_duration_seconds)}",
            f"Profit factor: {_fmt(p.profit_factor)}",
            f"Expectancy: {_fmt(p.expectancy)}",
        ]),
        ("Data Quality", [
            f"Files loaded: {d.files_loaded}",
            f"Files failed: {d.files_failed}",
            f"Validation warnings: {d.validation_warnings}",
            f"Validation errors: {d.validation_errors}",
            f"Tradable strikes: {d.tradable_strikes}",
            f"Data coverage %: {_fmt(d.data_coverage_percent)}",
            f"Missing data %: {_fmt(d.missing_data_percent)}",
        ]),
        ("Engineering Statistics", [
            f"Snapshots processed: {q.snapshots_processed}",
            f"ATM strike changes: {_fmt(q.atm_strike_changes)}",
            f"Average daily trades: {_fmt(q.average_daily_trades)}",
            f"CSV loading time: {_fmt(s.csv_loading_time)}",
            f"Market build time: {_fmt(s.market_build_time)}",
            f"Backtest time: {_fmt(s.backtest_time)}",
            f"Analytics time: {_fmt(s.analytics_time)}",
            f"Dashboard generation time: {_fmt(s.dashboard_generation_time)}",
            f"Peak memory MB: {_fmt(s.peak_memory_usage_mb)}",
            f"Total runtime: {_fmt(s.total_runtime)}",
        ]),
    ]

    lines: list[str] = []
    for title, body in sections:
        lines.append(title)
        lines.extend(body)
        lines.append("")

    if result.validation_report:
        lines.append("Validation Summary")
        for row in result.validation_report[:20]:
            lines.append(f"{row['severity']} {row['file']}: {row['message']}")
        lines.append("")

    lines.append("Conclusions")
    lines.extend(wrap(_conclusion(result), width=92))
    return lines


def _write_simple_pdf(path: Path, title: str, lines: list[str]) -> None:
    page_width = 612
    page_height = 792
    left = 54
    top = 744
    line_height = 14
    lines_per_page = 46
    pages = [lines[index:index + lines_per_page] for index in range(0, len(lines), lines_per_page)]
    objects: list[bytes] = []

    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    page_ids = []
    content_ids = []
    font_id = 3

    for page_index in range(len(pages)):
        page_id = 4 + page_index * 2
        content_id = page_id + 1
        page_ids.append(page_id)
        content_ids.append(content_id)

    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode("latin-1"))
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    for page_index, page_lines in enumerate(pages):
        page_id = page_ids[page_index]
        content_id = content_ids[page_index]
        objects.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page_width} {page_height}] "
                f"/Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>"
            ).encode("latin-1")
        )
        stream = _page_stream(title, page_lines, page_index + 1, len(pages), left, top, line_height)
        objects.append(
            b"<< /Length " + str(len(stream)).encode("latin-1") + b" >>\nstream\n" + stream + b"\nendstream"
        )

    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for object_id, payload in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{object_id} 0 obj\n".encode("latin-1"))
        output.extend(payload)
        output.extend(b"\nendobj\n")

    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
    output.extend(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            "startxref\n"
            f"{xref_offset}\n"
            "%%EOF\n"
        ).encode("latin-1")
    )

    path.write_bytes(bytes(output))


def _page_stream(
    title: str,
    lines: list[str],
    page_number: int,
    total_pages: int,
    left: int,
    top: int,
    line_height: int,
) -> bytes:
    commands = [
        "BT",
        "/F1 16 Tf",
        f"{left} {top} Td",
        f"({_escape_pdf(title)}) Tj",
        "ET",
    ]
    y = top - 30

    for line in lines:
        if not line:
            y -= line_height
            continue
        size = 12 if line in _section_titles() else 10
        commands.extend(
            [
                "BT",
                f"/F1 {size} Tf",
                f"{left} {y} Td",
                f"({_escape_pdf(line)}) Tj",
                "ET",
            ]
        )
        y -= line_height + (2 if size == 12 else 0)

    commands.extend(
        [
            "BT",
            "/F1 9 Tf",
            f"{left} 34 Td",
            f"(Page {page_number} of {total_pages}) Tj",
            "ET",
        ]
    )
    return "\n".join(commands).encode("latin-1", errors="replace")


def _section_titles() -> set[str]:
    return {
        "Table of Contents",
        "Executive Summary",
        "Project Metadata",
        "Architecture Summary",
        "Performance Summary",
        "Trade Statistics",
        "Risk Metrics",
        "Data Quality",
        "Engineering Statistics",
        "Validation Summary",
        "Conclusions",
    }


def _escape_pdf(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _fmt(value: object) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, float):
        return f"{value:,.2f}"
    return str(value)


def _conclusion(result: AnalyticsResult) -> str:
    performance = result.performance
    if performance.number_of_trades == 0:
        return "No closed trades were available, so performance confidence is limited."
    if performance.total_pnl > 0:
        return "The run produced positive PnL. Review drawdown, daily concentration, and validation issues before trusting the strategy out of sample."
    return "The run did not produce positive PnL. Inspect the trade distribution, ATM rollover behavior, and data quality before further tuning."
