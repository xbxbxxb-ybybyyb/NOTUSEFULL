import pandas as pd

df = pd.read_pickle("000008.SZ_trade.pkl")

df1 = df.copy()

df1["HTSCSecurityID"] = "000001.SZ"

df_new = pd.concat([df, df1], axis = 0)

print(df_new["HTSCSecurityID"])

import cudf

data_big = cudf.from_pandas(df_new)
tt = data_big.groupby(['HTSCSecurityID','TradeBuyNo'])['TradePrice'].apply(lambda x:x.iloc[-1]/x.iloc[0]-1)
print(tt)
