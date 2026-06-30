# Analytics And Dashboard Guide

This project keeps the core engine frozen and adds analytics as a consumer
layer. The analytics layer reads portfolio state, closed trades, markets,
validation results, configuration, and runtime metadata. It never mutates the
portfolio or changes strategy/execution behavior.

## Run

```powershell
python run_research_backtest.py --data NSE_20221118 --output results --initial-cash 1000000
```

Then open:

```text
results/dashboard.html
results/report.html
results/report.pdf
```

## Result Files

`summary.json` contains the executive summary, data-quality summary, and system
metrics.

`analytics.json` contains the complete analytics payload used by reports and
dashboards.

`trades.csv` contains one row per closed trade, including instrument, entry,
exit, PnL, and holding time.

`daily_summary.csv` contains daily PnL, cumulative PnL, win rate, drawdown, and
trade count.

`positions.csv` contains open positions at the end of the run.

`validation_report.json` contains validation warnings and errors produced by
the existing validation framework.

`configuration.json` contains run inputs such as initial cash, data path,
output path, and strategy name.

## Metric Definitions

Final Portfolio Value is the value reported by `Portfolio.portfolio_value`.

Total PnL is realized PnL plus unrealized PnL.

Return % is Total PnL divided by initial cash.

Win Rate is winning trades divided by total closed trades.

Average Profit is the average PnL of winning trades.

Average Loss is the average PnL of losing trades.

Profit Factor is gross profit divided by absolute gross loss. It is `null`
when there are no losing trades.

Expectancy is average PnL per closed trade.

Maximum Drawdown is computed from the closed-trade realized equity curve.

Maximum Drawdown Duration is the longest time the realized equity curve spent
below its previous high.

Data Coverage % is observed tradable option-pair quotes divided by expected
quotes across all market snapshots and loaded tradable strikes.

Missing Data % is `100 - Data Coverage %`.

Average Quotes Per Strike is the average of call/put quote counts for loaded
tradable option strikes.

Snapshots Per Second is snapshots processed divided by measured backtest time.

Trades Per Second is closed trades divided by measured backtest time.

## Interpreting Results

Use the executive KPIs to understand the headline outcome: total PnL, win rate,
profit factor, drawdown, trades, and trading days.

Use the main performance chart to see whether PnL came steadily or from a few
large jumps.

Use drawdown and daily PnL together. A profitable strategy with concentrated
loss days may still be fragile.

Use the trade histogram and holding-time scatter to find outliers. Large losses
with long holding periods often point to exit behavior worth reviewing.

Use the ATM strike and premium timelines for strategy-specific behavior. They
show how often the ATM moved, how long strikes were held, and how CE/PE premium
changed through the day.

Use the data-quality section before trusting results. Validation errors,
low coverage, or many missing quotes mean performance should be treated as
diagnostic rather than conclusive.

## Extensibility

Generic analytics live in `analytics/calculator.py`.

ATM straddle-specific metrics live in `analytics/strategy_insights.py`.

Exports live in `reporting/exporter.py`.

Dashboard rendering lives in `dashboard/html_dashboard.py`.

New strategies should provide their own insight helper and pass the resulting
dictionary into `build_analytics`. The generic calculator will continue to work
without strategy-specific assumptions.

## Current Instrumentation Limits

The frozen engine does not retain signal and order audit history. Metrics such
as `orders_generated`, `orders_executed`, and `signals_generated` are therefore
reported as `null` unless an execution-statistics dictionary is supplied to
`build_analytics`.

Forward-filled quote counts are also reported as `null` because the current
data layer does not expose that count as structured metadata.
