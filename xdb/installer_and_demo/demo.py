from xdb.stockdata import StockData
import pandas as pd
import time
import os

a = StockData()

# 目前只有 20230222 20230223 20230224 三个交易日数据

start = time.time()
df = a.get_trade("20230222", "000001.SZ")
end = time.time()

print(f"spent time cost = {end - start}")


df.to_pickle("/data/user/020063/data.pkl")

start = time.time()
pickle_df = pd.read_pickle("/data/user/020063/data.pkl")
end = time.time()

print(f"spent time cost for pickle = {end - start}")

# trade_df = a.get_trade("20230223", "601398.SH")
# order_df = a.get_order("20230223", "601398.SH")
# tick_df = a.get_tick("20230223", "601398.SH")
# cancel_df = a.get_cancel_order("20230223", "601398.SH")
#
# print(f"trade dataframe shape: {trade_df.shape}")
# print(f"order dataframe shape: {order_df.shape}")
# print(f"tick dataframe shape: {tick_df.shape}")
# print(f"cancel dataframe shape: {cancel_df.shape}")