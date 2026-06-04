from xdb.stockdata import StockData
import pandas as pd
import time
import os

a = StockData()

# 获取逐笔成交
df1 = a.get_trade("20230222", "000001.SZ")
# 获取逐笔委托
df2 = a.get_order("20230222", "000001.SZ")
# 获取撤单
df3 = a.get_cancel("20230222", "000001.SZ")
# 获取 1s tick
df4 = a.get_tick1s("20230222", "000001.SZ")
# 获取全息盘口 
df5 = a.get_tickfull("20230222", "000001.SZ")
# 获取交易所 tick
df6 = a.get_tickex("20230222", "000001.SZ")
