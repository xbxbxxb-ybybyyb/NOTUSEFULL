from xdb.marketdata import MarketData
import pandas as pd
import time
import os

md = MarketData()

# 目前只有 20230222 20230223 20230224 三个交易日数据

trade_df = md.get_trade("20230223", "601398.SH")
order_df = md.get_order("20230223", "601398.SH")
tick_df = md.get_tick("20230223", "601398.SH")
cancel_df = md.get_cancel_order("20230223", "601398.SH")

print(f"trade dataframe shape: {trade_df.shape}")
print(f"order dataframe shape: {order_df.shape}")
print(f"tick dataframe shape: {tick_df.shape}")
print(f"cancel dataframe shape: {cancel_df.shape}")
