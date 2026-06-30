from data.market_builder import build_markets
from data.trading_day_loader import TradingDayLoader

loader = TradingDayLoader("NSE_20221118")

raw_market = loader.load()

markets = build_markets(raw_market)

for underlying, market in markets.items():

    print(f"{underlying.value}")

    print(len(market))

    print(market.snapshots[0])

    print(market.snapshots[-1])

    print("-" * 60)