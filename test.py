from data.csv_loader import CSVLoader
from data.time_series import TimeSeriesProcessor

df = CSVLoader.load("NIFTY-I.csv")

print(len(df))

continuous = TimeSeriesProcessor.build(df)

print(len(continuous))