from xquant.thirdpartydata.marketdata import MarketData
ma = MarketData()
df = ma.getKLine1MOnPeriod('0940301')
print(df)
df.to_csv('df.csv')
