# User Guide

This guide explains how to install, run, inspect, and interpret the backtesting
research platform.

## Installation

Use Python 3.11+ from the repository root.

```powershell
python -m pip install pandas pytest
```

The interactive dashboard loads Plotly from a browser CDN. An internet
connection is recommended when opening `results/dashboard.html`.

## Running The Backtest

Run the complete workflow:

```powershell
python run_research_backtest.py --data NSE_20221118 --output results --initial-cash 1000000
```

Optional metadata can be supplied for submission/reporting:

```powershell
python run_research_backtest.py `
  --data NSE_20221118 `
  --output results `
  --initial-cash 1000000 `
  --project-version 1.0.0 `
  --engine-version 1.0.0 `
  --author "Your Name"
```

## Configuration

`--data` points to a trading-day directory containing `Futures/` and
`Options/` folders.

`--output` controls where reports and exports are written.

`--initial-cash` is passed to `Portfolio` and used for return calculations.

`--project-version`, `--engine-version`, and `--author` are metadata fields
shown in reports and dashboards.

Current engine assumptions written to `configuration.json`:

- Position size: `1`
- Transaction cost: `0.0`
- Slippage: `0.0`

## Output Files

`dashboard.html` is the primary interactive research dashboard.

`report.html` is a print-friendly report for review.

`report.pdf` is a compact dependency-free PDF summary.

`summary.json` contains executive metrics, data quality, and system metrics.

`analytics.json` contains the full analytics payload used by dashboard and
report generation.

`trades.csv` contains closed trade records.

`daily_summary.csv` contains one row per trading day.

`positions.csv` contains open positions after the run.

`configuration.json` contains run configuration.

`validation_report.json` contains validation warnings and errors.

## Dashboard Walkthrough

The header identifies the strategy, dataset, run timestamp, trading days,
runtime, project version, and git commit.

The KPI cards answer the headline questions:

- Final Portfolio Value
- Total PnL
- Win Rate
- Profit Factor
- Max Drawdown
- Trades
- Trading Days

The cumulative performance chart shows realized PnL, portfolio value, and the
running maximum.

The drawdown chart shows realized equity declines from prior highs.

The daily PnL chart separates daily contribution from cumulative contribution.

The trade analysis charts show distribution, holding time, and whether large
PnL events are associated with longer holding periods.

The ATM strike timeline shows how the selected strike moved relative to futures
price.

The premium timeline shows CE, PE, and combined ATM premium through the run.

The data quality section summarizes coverage, missing data, warnings, and
errors.

The runtime chart shows where wall-clock time was spent in the pipeline.

Tables support search, sorting, and pagination.

## Report Walkthrough

The HTML and PDF reports are designed for review packets. They include:

- Table of contents
- Executive summary
- Project metadata
- Architecture summary
- Performance summary
- Trade statistics
- Risk metrics
- Data quality
- Engineering statistics
- Validation summary
- Conclusions

Use `report.html` for the richest printable version and `report.pdf` when a
single lightweight attachment is needed.

## Trade Export

`trades.csv` includes:

- Trade ID
- Instrument and symbol
- Underlying
- Option type
- Strike
- Expiry
- Quantity
- Entry and exit timestamps
- Entry and exit prices
- PnL
- Holding time

This file is suitable for spreadsheet review or external research notebooks.

## Analytics Interpretation

Total PnL is realized plus unrealized PnL.

Return percent is Total PnL divided by initial cash.

Win rate is winning trades divided by closed trades.

Profit factor is gross profit divided by absolute gross loss.

Expectancy is average PnL per closed trade.

Maximum drawdown is computed from the closed-trade realized equity curve.

Data coverage is observed tradable option-pair quotes divided by expected
quotes across market snapshots and loaded tradable strikes.

Treat a strategy with positive PnL but poor data coverage, high drawdown, or
large outlier dependence as unproven.

## Validation

Run all tests:

```powershell
pytest -q
```

Run syntax compilation:

```powershell
python -m compileall analytics dashboard reporting run_research_backtest.py tests
```

Run the full sample workflow:

```powershell
python run_research_backtest.py --data NSE_20221118 --output results --initial-cash 1000000
```
