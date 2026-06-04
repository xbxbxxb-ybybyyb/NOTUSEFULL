from MDCDataProvider import DataProvider as MarketData
from xquant.factordata import FactorData
fa = FactorData()
stocks = fa.hset("MARKET", "20190701", "ALLA")["stock"].tolist()
import time
t1 = time.time()
ma = MarketData()
print("init time: ", time.time()-t1)
df_list = []
for stock in stocks:
    t2 = time.time()
    df = ma.get_data_by_date("KLINE1M4ZT", stock,"20190701")
    print(df.shape)
    df_list.append(df)

import pandas as pd
mdf = pd.concat(df_list, axis=0)
mdf.to_csv("merge_df.csv")
print("total: ", time.time()-t1)

