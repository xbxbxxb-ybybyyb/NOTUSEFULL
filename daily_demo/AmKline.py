from xquant.thirdpartydata.marketdata import MarketData
import time
t1 = time.time()
ma = MarketData()
open_df = ma.getAmKline1M4ZTDataFrame(mddate='20200623')
print(time.time()-t1)
open_df.to_csv('tmp.csv')

