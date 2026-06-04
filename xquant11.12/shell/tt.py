import pandas as pd
import time
t1 = time.time()
df = pd.read_parquet("XSHE_Stock_Snapshot_Level2_20211207.parquet")
print(time.time()-t1)
t1 = time.time()
df["Sell1OrderDetail"] = df["Sell1OrderDetail"].fillna('[]')
df["Buy1OrderDetail"] = df["Buy1OrderDetail"].fillna('[]')

df["Sell1OrderDetail"] = df["Sell1OrderDetail"].apply(lambda x: x.replace(",", "|"))
df["Buy1OrderDetail"] = df["Buy1OrderDetail"].apply(lambda x: x.replace(",", "|"))
print(time.time()-t1)

