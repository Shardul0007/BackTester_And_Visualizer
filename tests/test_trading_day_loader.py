from data.trading_day_loader import TradingDayLoader

loader = TradingDayLoader("allData/NSE_20221101")

raw = loader.load()

print(raw.trading_date)
print(raw.futures.keys())
print(raw.options.keys())