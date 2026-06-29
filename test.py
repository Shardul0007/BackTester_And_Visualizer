from data.csv_loader import CSVLoader

df = CSVLoader.load("NIFTY-I.csv")

print(df.head())
print(df.dtypes)
print(len(df))