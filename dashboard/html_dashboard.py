"""Single-file HTML dashboard powered by Plotly in the browser."""

from __future__ import annotations

import json
from pathlib import Path

from analytics.models import AnalyticsResult


def generate_dashboard(
    result: AnalyticsResult,
    output_path: str | Path = "results/dashboard.html",
) -> Path:
    """Write an interactive dashboard HTML file."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(result.to_dict(), default=str, allow_nan=False)
    path.write_text(_html_document(data), encoding="utf-8")
    return path


def _html_document(data_json: str) -> str:
    template = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Backtest Analytics Dashboard</title>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --text: #171a1f;
      --muted: #667085;
      --line: #d8dde6;
      --accent: #1f77b4;
      --good: #17803d;
      --bad: #b42318;
      --warn: #b56a00;
      --shadow: 0 1px 2px rgba(16, 24, 40, 0.08);
    }
    body.dark {
      color-scheme: dark;
      --bg: #101216;
      --panel: #171a20;
      --text: #eef1f5;
      --muted: #9aa4b2;
      --line: #2a303a;
      --accent: #7bb7ff;
      --good: #70d67f;
      --bad: #ff8a80;
      --warn: #ffc46b;
      --shadow: none;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 14px;
      letter-spacing: 0;
    }
    header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 18px;
      padding: 18px 28px 14px;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
      position: sticky;
      top: 0;
      z-index: 10;
    }
    h1, h2, h3 {
      margin: 0;
      font-weight: 650;
      letter-spacing: 0;
    }
    h1 { font-size: 21px; line-height: 1.2; }
    h2 { font-size: 15px; margin-bottom: 10px; }
    h3 { font-size: 13px; margin-bottom: 8px; color: var(--muted); }
    .meta {
      color: var(--muted);
      margin-top: 5px;
      font-size: 12px;
      display: flex;
      flex-wrap: wrap;
      gap: 8px 14px;
    }
    .header-actions {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-shrink: 0;
    }
    button, input, select {
      border: 1px solid var(--line);
      background: var(--panel);
      color: var(--text);
      border-radius: 6px;
      padding: 8px 10px;
      font: inherit;
    }
    button { cursor: pointer; }
    input { min-width: 220px; }
    main {
      width: min(1480px, 100%);
      margin: 0 auto;
      padding: 18px 20px 36px;
    }
    .kpis {
      display: grid;
      grid-template-columns: repeat(7, minmax(130px, 1fr));
      gap: 12px;
      margin-bottom: 16px;
    }
    .kpi, section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
    }
    .kpi {
      padding: 14px;
      min-height: 88px;
    }
    .kpi-label {
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 8px;
    }
    .kpi-value {
      font-size: clamp(17px, 1.8vw, 25px);
      font-weight: 720;
      line-height: 1.15;
      overflow-wrap: anywhere;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(12, 1fr);
      gap: 14px;
    }
    section {
      padding: 14px;
      min-width: 0;
    }
    .span-12 { grid-column: span 12; }
    .span-8 { grid-column: span 8; }
    .span-6 { grid-column: span 6; }
    .span-4 { grid-column: span 4; }
    .chart { width: 100%; height: 360px; }
    .chart.tall { height: 460px; }
    .chart.short { height: 280px; }
    .summary-grid {
      display: grid;
      grid-template-columns: repeat(6, minmax(120px, 1fr));
      gap: 10px;
    }
    .summary-item {
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px;
      min-height: 66px;
    }
    .summary-label {
      color: var(--muted);
      font-size: 11px;
      margin-bottom: 5px;
    }
    .summary-value {
      font-size: 14px;
      font-weight: 650;
      overflow-wrap: anywhere;
    }
    .table-tools {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
      margin-bottom: 10px;
      flex-wrap: wrap;
    }
    .table-meta {
      color: var(--muted);
      font-size: 12px;
    }
    .table-wrap {
      max-height: 390px;
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 8px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
    }
    th, td {
      padding: 8px 10px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      white-space: nowrap;
    }
    th {
      color: var(--muted);
      font-weight: 650;
      position: sticky;
      top: 0;
      background: var(--panel);
      cursor: pointer;
      user-select: none;
      z-index: 1;
    }
    tr:hover td { background: rgba(31, 119, 180, 0.06); }
    .positive { color: var(--good); }
    .negative { color: var(--bad); }
    .warning { color: var(--warn); }
    @media (max-width: 1180px) {
      .kpis { grid-template-columns: repeat(4, minmax(0, 1fr)); }
      .summary-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
    }
    @media (max-width: 900px) {
      header { padding: 16px; align-items: flex-start; flex-direction: column; }
      .kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .span-8, .span-6, .span-4 { grid-column: span 12; }
      main { padding: 14px; }
      input { min-width: min(260px, 100%); }
      .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>Backtest Analytics Dashboard</h1>
      <div class="meta" id="runMeta"></div>
    </div>
    <div class="header-actions">
      <button id="themeToggle" type="button" title="Toggle theme">Theme</button>
    </div>
  </header>
  <main>
    <div class="kpis" id="kpis"></div>
    <div class="grid">
      <section class="span-12">
        <h2>Run Summary</h2>
        <div class="summary-grid" id="runSummary"></div>
      </section>
      <section class="span-12">
        <h2>Cumulative Performance</h2>
        <div class="chart tall" id="performanceChart"></div>
      </section>
      <section class="span-6">
        <h2>Realized Drawdown</h2>
        <div class="chart" id="drawdownChart"></div>
      </section>
      <section class="span-6">
        <h2>Daily PnL And Cumulative PnL</h2>
        <div class="chart" id="dailyPnlChart"></div>
      </section>
      <section class="span-4">
        <h2>Trade PnL Distribution</h2>
        <div class="chart short" id="tradeHistogram"></div>
      </section>
      <section class="span-4">
        <h2>Holding Time Distribution</h2>
        <div class="chart short" id="holdingHistogram"></div>
      </section>
      <section class="span-4">
        <h2>Holding Time vs Trade PnL</h2>
        <div class="chart short" id="tradeScatter"></div>
      </section>
      <section class="span-8">
        <h2>ATM Strike And Future Timeline</h2>
        <div class="chart" id="strikeTimeline"></div>
      </section>
      <section class="span-4">
        <h2>ATM Premium Timeline</h2>
        <div class="chart" id="premiumTimeline"></div>
      </section>
      <section class="span-6">
        <h2>Data Quality Summary</h2>
        <div class="chart short" id="dataQualityChart"></div>
      </section>
      <section class="span-6">
        <h2>Pipeline Runtime Breakdown</h2>
        <div class="chart short" id="systemChart"></div>
      </section>
      <section class="span-12">
        <h2>Trade Table</h2>
        <div id="tradeTable"></div>
      </section>
      <section class="span-12">
        <h2>Daily Summary</h2>
        <div id="dailyTable"></div>
      </section>
      <section class="span-6">
        <h2>Configuration Summary</h2>
        <div id="configurationTable"></div>
      </section>
      <section class="span-6">
        <h2>Validation Summary</h2>
        <div id="validationTable"></div>
      </section>
    </div>
  </main>
  <script>
    const analytics = __ANALYTICS_DATA__;
    const css = () => getComputedStyle(document.documentElement);
    const colors = () => ({
      text: css().getPropertyValue('--text').trim(),
      muted: css().getPropertyValue('--muted').trim(),
      line: css().getPropertyValue('--line').trim(),
      accent: css().getPropertyValue('--accent').trim(),
      good: css().getPropertyValue('--good').trim(),
      bad: css().getPropertyValue('--bad').trim(),
      warn: css().getPropertyValue('--warn').trim(),
      panel: css().getPropertyValue('--panel').trim()
    });
    const tableState = {};

    const fmtNumber = (value, digits = 2) => {
      if (value === null || value === undefined || Number.isNaN(Number(value))) return 'N/A';
      return Number(value).toLocaleString(undefined, { maximumFractionDigits: digits });
    };
    const fmtPct = value => value === null || value === undefined ? 'N/A' : `${fmtNumber(value)}%`;
    const fmtSecs = value => value === null || value === undefined ? 'N/A' : `${fmtNumber(value / 60)} min`;
    const fmtText = value => value === null || value === undefined || value === '' ? 'N/A' : String(value);
    const pnlClass = value => Number(value || 0) >= 0 ? 'positive' : 'negative';

    function chartLayout(xTitle, yTitle, options = {}) {
      const c = colors();
      return {
        margin: { l: 58, r: 22, t: 18, b: 52 },
        paper_bgcolor: c.panel,
        plot_bgcolor: c.panel,
        font: { color: c.text, size: 12 },
        xaxis: { title: xTitle, gridcolor: c.line, zerolinecolor: c.line },
        yaxis: { title: yTitle, gridcolor: c.line, zerolinecolor: c.line },
        hovermode: 'x unified',
        legend: { orientation: 'h', y: 1.1, x: 0 },
        ...options
      };
    }

    function renderMeta() {
      const meta = analytics.metadata || {};
      const quality = analytics.backtest_quality || {};
      const system = analytics.system || {};
      const items = [
        meta.strategy_name,
        meta.dataset,
        meta.run_timestamp,
        quality.total_trading_days !== undefined ? `${quality.total_trading_days} trading day(s)` : null,
        system.total_runtime !== null && system.total_runtime !== undefined ? `${fmtNumber(system.total_runtime)}s runtime` : null,
        meta.project_version ? `v${meta.project_version}` : null,
        meta.git_commit_hash ? `git ${meta.git_commit_hash}` : null
      ];
      document.getElementById('runMeta').innerHTML = items.filter(Boolean).map(item => `<span>${item}</span>`).join('');
    }

    function renderKpis() {
      const p = analytics.performance || {};
      const q = analytics.backtest_quality || {};
      const items = [
        ['Final Portfolio Value', fmtNumber(p.final_portfolio_value), p.final_portfolio_value],
        ['Total PnL', fmtNumber(p.total_pnl), p.total_pnl],
        ['Win Rate', fmtPct(p.win_rate), p.win_rate],
        ['Profit Factor', fmtNumber(p.profit_factor), p.profit_factor],
        ['Max Drawdown', fmtNumber(p.maximum_drawdown), -p.maximum_drawdown],
        ['Trades', fmtNumber(p.number_of_trades, 0), p.number_of_trades],
        ['Trading Days', fmtNumber(q.total_trading_days, 0), q.total_trading_days]
      ];
      document.getElementById('kpis').innerHTML = items.map(([label, value, raw]) => `
        <div class="kpi">
          <div class="kpi-label">${label}</div>
          <div class="kpi-value ${label.includes('PnL') ? pnlClass(raw) : ''}">${value}</div>
        </div>
      `).join('');
    }

    function renderRunSummary() {
      const meta = analytics.metadata || {};
      const config = meta.configuration || {};
      const sys = analytics.system || {};
      const items = [
        ['Strategy', meta.strategy_name],
        ['Dataset', meta.dataset],
        ['Dataset Version', meta.dataset_version],
        ['Initial Cash', fmtNumber(config.initial_cash)],
        ['Position Size', config.position_size],
        ['Transaction Cost', fmtNumber(config.transaction_cost)],
        ['Slippage', fmtNumber(config.slippage)],
        ['Engine Version', meta.engine_version || config.engine_version],
        ['Project Version', meta.project_version || config.project_version],
        ['Author', meta.author],
        ['Total Runtime', sys.total_runtime === null || sys.total_runtime === undefined ? null : `${fmtNumber(sys.total_runtime)}s`],
        ['Peak Memory', sys.peak_memory_usage_mb === null || sys.peak_memory_usage_mb === undefined ? null : `${fmtNumber(sys.peak_memory_usage_mb)} MB`]
      ];
      document.getElementById('runSummary').innerHTML = items.map(([label, value]) => `
        <div class="summary-item">
          <div class="summary-label">${label}</div>
          <div class="summary-value">${fmtText(value)}</div>
        </div>
      `).join('');
    }

    function renderCharts() {
      const c = colors();
      const eq = analytics.equity_curve || [];
      const dd = analytics.drawdown_curve || [];
      const daily = analytics.daily_summary || [];
      const trades = analytics.trade_rows || [];
      const timeline = analytics.strategy_insights?.atm_strike_timeline || [];
      const sys = analytics.system || {};
      const dq = analytics.data_quality || {};

      Plotly.react('performanceChart', [
        {
          x: eq.map(r => r.timestamp),
          y: eq.map(r => r.realized_pnl),
          name: 'Realized PnL',
          type: 'scatter',
          mode: 'lines',
          hovertemplate: 'Time: %{x}<br>Realized PnL: %{y:,.2f}<extra></extra>',
          line: { color: c.accent, width: 2.2 }
        },
        {
          x: eq.map(r => r.timestamp),
          y: eq.map(r => r.equity),
          name: 'Portfolio Value',
          type: 'scatter',
          mode: 'lines',
          hovertemplate: 'Time: %{x}<br>Portfolio Value: %{y:,.2f}<extra></extra>',
          line: { color: c.good, width: 1.6 }
        },
        {
          x: eq.map(r => r.timestamp),
          y: eq.map(r => r.running_max),
          name: 'Running Maximum',
          type: 'scatter',
          mode: 'lines',
          hovertemplate: 'Time: %{x}<br>Running Max: %{y:,.2f}<extra></extra>',
          line: { color: c.muted, width: 1, dash: 'dot' }
        }
      ], chartLayout('Time', 'Value'));

      Plotly.react('drawdownChart', [
        {
          x: dd.map(r => r.timestamp),
          y: dd.map(r => -r.drawdown),
          type: 'scatter',
          fill: 'tozeroy',
          name: 'Drawdown',
          hovertemplate: 'Time: %{x}<br>Drawdown: %{y:,.2f}<extra></extra>',
          line: { color: c.bad }
        }
      ], chartLayout('Time', 'Drawdown'));

      Plotly.react('dailyPnlChart', [
        {
          x: daily.map(r => r.date),
          y: daily.map(r => r.pnl),
          type: 'bar',
          name: 'Daily PnL',
          hovertemplate: 'Date: %{x}<br>Daily PnL: %{y:,.2f}<extra></extra>',
          marker: { color: daily.map(r => r.pnl >= 0 ? c.good : c.bad) }
        },
        {
          x: daily.map(r => r.date),
          y: daily.map(r => r.cumulative_pnl),
          type: 'scatter',
          mode: 'lines+markers',
          name: 'Cumulative PnL',
          yaxis: 'y2',
          hovertemplate: 'Date: %{x}<br>Cumulative PnL: %{y:,.2f}<extra></extra>',
          line: { color: c.accent }
        }
      ], chartLayout('Date', 'Daily PnL', {
        yaxis2: { title: 'Cumulative PnL', overlaying: 'y', side: 'right', gridcolor: 'rgba(0,0,0,0)' }
      }));

      Plotly.react('tradeHistogram', [
        {
          x: trades.map(r => r.pnl),
          type: 'histogram',
          marker: { color: c.accent },
          name: 'Trade PnL',
          hovertemplate: 'PnL bucket: %{x}<br>Trades: %{y}<extra></extra>'
        }
      ], chartLayout('Trade PnL', 'Trade Count'));

      Plotly.react('holdingHistogram', [
        {
          x: trades.map(r => r.holding_minutes),
          type: 'histogram',
          marker: { color: c.muted },
          name: 'Holding Minutes',
          hovertemplate: 'Holding minutes: %{x}<br>Trades: %{y}<extra></extra>'
        }
      ], chartLayout('Holding Minutes', 'Trade Count'));

      Plotly.react('tradeScatter', [
        {
          x: trades.map(r => r.holding_minutes),
          y: trades.map(r => r.pnl),
          mode: 'markers',
          type: 'scatter',
          text: trades.map(r => r.instrument),
          hovertemplate: '%{text}<br>Holding: %{x:,.2f} min<br>PnL: %{y:,.2f}<extra></extra>',
          marker: { color: trades.map(r => r.pnl >= 0 ? c.good : c.bad), size: 8, opacity: 0.82 },
          name: 'Trades'
        }
      ], chartLayout('Holding Minutes', 'Trade PnL'));

      Plotly.react('strikeTimeline', [
        {
          x: timeline.map(r => r.timestamp),
          y: timeline.map(r => r.atm_strike),
          mode: 'lines',
          type: 'scatter',
          name: 'ATM Strike',
          hovertemplate: 'Time: %{x}<br>ATM Strike: %{y}<extra></extra>',
          line: { color: c.accent }
        },
        {
          x: timeline.map(r => r.timestamp),
          y: timeline.map(r => r.future_price),
          mode: 'lines',
          type: 'scatter',
          name: 'Future Price',
          yaxis: 'y2',
          hovertemplate: 'Time: %{x}<br>Future Price: %{y:,.2f}<extra></extra>',
          line: { color: c.muted }
        }
      ], chartLayout('Time', 'ATM Strike', {
        yaxis2: { title: 'Future Price', overlaying: 'y', side: 'right', gridcolor: 'rgba(0,0,0,0)' }
      }));

      Plotly.react('premiumTimeline', [
        {
          x: timeline.map(r => r.timestamp),
          y: timeline.map(r => r.ce_premium),
          type: 'scatter',
          mode: 'lines',
          name: 'CE',
          hovertemplate: 'Time: %{x}<br>CE Premium: %{y:,.2f}<extra></extra>',
          line: { color: c.good }
        },
        {
          x: timeline.map(r => r.timestamp),
          y: timeline.map(r => r.pe_premium),
          type: 'scatter',
          mode: 'lines',
          name: 'PE',
          hovertemplate: 'Time: %{x}<br>PE Premium: %{y:,.2f}<extra></extra>',
          line: { color: c.bad }
        },
        {
          x: timeline.map(r => r.timestamp),
          y: timeline.map(r => r.combined_premium),
          type: 'scatter',
          mode: 'lines',
          name: 'Combined',
          hovertemplate: 'Time: %{x}<br>Combined Premium: %{y:,.2f}<extra></extra>',
          line: { color: c.accent }
        }
      ], chartLayout('Time', 'Premium'));

      Plotly.react('dataQualityChart', [
        {
          x: ['Coverage %', 'Missing %', 'Warnings', 'Errors'],
          y: [dq.data_coverage_percent, dq.missing_data_percent, dq.validation_warnings, dq.validation_errors],
          type: 'bar',
          hovertemplate: '%{x}: %{y:,.2f}<extra></extra>',
          marker: { color: [c.good, c.bad, c.warn, c.bad] }
        }
      ], chartLayout('Metric', 'Value'));

      Plotly.react('systemChart', [
        {
          x: ['CSV Load', 'Market Build', 'Backtest', 'Analytics', 'Dashboard'],
          y: [sys.csv_loading_time, sys.market_build_time, sys.backtest_time, sys.analytics_time, sys.dashboard_generation_time],
          type: 'bar',
          hovertemplate: '%{x}: %{y:,.2f}s<extra></extra>',
          marker: { color: c.accent }
        }
      ], chartLayout('Pipeline Stage', 'Seconds'));
    }

    function valueForSort(value) {
      if (value === null || value === undefined) return '';
      const numberValue = Number(value);
      return Number.isNaN(numberValue) ? String(value).toLowerCase() : numberValue;
    }

    function renderTable(containerId, rows, columns, options = {}) {
      if (!tableState[containerId]) {
        tableState[containerId] = { search: '', sortKey: columns[0]?.key, sortDir: 'asc', page: 1, pageSize: options.pageSize || 25 };
      }
      const state = tableState[containerId];
      const searchable = state.search.trim().toLowerCase();
      let filtered = rows.filter(row => {
        if (!searchable) return true;
        return columns.some(column => String(row[column.key] ?? '').toLowerCase().includes(searchable));
      });
      filtered = filtered.sort((a, b) => {
        const av = valueForSort(a[state.sortKey]);
        const bv = valueForSort(b[state.sortKey]);
        if (av < bv) return state.sortDir === 'asc' ? -1 : 1;
        if (av > bv) return state.sortDir === 'asc' ? 1 : -1;
        return 0;
      });
      const pageCount = Math.max(1, Math.ceil(filtered.length / state.pageSize));
      state.page = Math.min(state.page, pageCount);
      const start = (state.page - 1) * state.pageSize;
      const pageRows = filtered.slice(start, start + state.pageSize);
      const searchId = `${containerId}-search`;
      const tableId = `${containerId}-table`;
      const metaId = `${containerId}-meta`;

      document.getElementById(containerId).innerHTML = `
        <div class="table-tools">
          <input id="${searchId}" type="search" placeholder="${options.placeholder || 'Search'}" value="${state.search}">
          <div class="header-actions">
            <button type="button" data-action="prev">Prev</button>
            <button type="button" data-action="next">Next</button>
            <span class="table-meta" id="${metaId}"></span>
          </div>
        </div>
        <div class="table-wrap">
          <table id="${tableId}">
            <thead>
              <tr>${columns.map(column => `<th data-key="${column.key}">${column.label}${state.sortKey === column.key ? (state.sortDir === 'asc' ? ' ^' : ' v') : ''}</th>`).join('')}</tr>
            </thead>
            <tbody>
              ${pageRows.map(row => `<tr>${columns.map(column => {
                const value = column.format ? column.format(row[column.key]) : fmtText(row[column.key]);
                const cssClass = column.className ? column.className(row[column.key], row) : '';
                return `<td class="${cssClass}">${value}</td>`;
              }).join('')}</tr>`).join('')}
            </tbody>
          </table>
        </div>
      `;
      document.getElementById(metaId).textContent = `${filtered.length} row(s), page ${state.page} of ${pageCount}`;
      document.getElementById(searchId).addEventListener('input', event => {
        state.search = event.target.value;
        state.page = 1;
        renderTable(containerId, rows, columns, options);
      });
      document.querySelectorAll(`#${tableId} th`).forEach(th => {
        th.addEventListener('click', () => {
          const key = th.getAttribute('data-key');
          if (state.sortKey === key) {
            state.sortDir = state.sortDir === 'asc' ? 'desc' : 'asc';
          } else {
            state.sortKey = key;
            state.sortDir = 'asc';
          }
          renderTable(containerId, rows, columns, options);
        });
      });
      document.querySelector(`#${containerId} [data-action="prev"]`).addEventListener('click', () => {
        state.page = Math.max(1, state.page - 1);
        renderTable(containerId, rows, columns, options);
      });
      document.querySelector(`#${containerId} [data-action="next"]`).addEventListener('click', () => {
        state.page = Math.min(pageCount, state.page + 1);
        renderTable(containerId, rows, columns, options);
      });
    }

    function renderTables() {
      renderTable('tradeTable', analytics.trade_rows || [], [
        { key: 'trade_id', label: '#' },
        { key: 'instrument', label: 'Instrument' },
        { key: 'underlying', label: 'Underlying' },
        { key: 'entry_time', label: 'Entry' },
        { key: 'exit_time', label: 'Exit' },
        { key: 'entry_price', label: 'Entry Price', format: fmtNumber },
        { key: 'exit_price', label: 'Exit Price', format: fmtNumber },
        { key: 'pnl', label: 'PnL', format: fmtNumber, className: pnlClass },
        { key: 'holding_seconds', label: 'Holding', format: fmtSecs }
      ], { placeholder: 'Search trades' });

      renderTable('dailyTable', analytics.daily_summary || [], [
        { key: 'date', label: 'Date' },
        { key: 'trades', label: 'Trades' },
        { key: 'pnl', label: 'PnL', format: fmtNumber, className: pnlClass },
        { key: 'cumulative_pnl', label: 'Cumulative', format: fmtNumber, className: pnlClass },
        { key: 'win_rate', label: 'Win Rate', format: fmtPct },
        { key: 'drawdown', label: 'Drawdown', format: fmtNumber },
        { key: 'rollovers', label: 'Rollovers' }
      ], { placeholder: 'Search days', pageSize: 10 });

      const configRows = Object.entries(analytics.metadata?.configuration || {}).map(([key, value]) => ({ key, value }));
      renderTable('configurationTable', configRows, [
        { key: 'key', label: 'Setting' },
        { key: 'value', label: 'Value', format: fmtText }
      ], { placeholder: 'Search configuration', pageSize: 12 });

      renderTable('validationTable', analytics.validation_report || [], [
        { key: 'file', label: 'File' },
        { key: 'severity', label: 'Severity', className: value => value === 'ERROR' ? 'negative' : 'warning' },
        { key: 'message', label: 'Message' }
      ], { placeholder: 'Search validation', pageSize: 12 });
    }

    function renderAll() {
      renderMeta();
      renderKpis();
      renderRunSummary();
      renderCharts();
      renderTables();
    }

    document.getElementById('themeToggle').addEventListener('click', () => {
      document.body.classList.toggle('dark');
      renderCharts();
    });

    renderAll();
  </script>
</body>
</html>
"""
    return template.replace("__ANALYTICS_DATA__", data_json)
