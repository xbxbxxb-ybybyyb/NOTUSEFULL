#%%一个backtrader的demo
import os
#import backtrader as bt
import xbrain as bt
import pandas as pd
from datetime import time

def parse_hm(hm_str):
    try:
        time_int = [int(x) for x in hm_str.split(':')]
    except:
        raise Exception('Bad time format: {}'.format(hm_str))
    if len(time_int) == 2:
        return time(time_int[0], time_int[1])
    raise Exception('Please use time format like 09:30, current: {}'.format(hm_str))


future_data = pd.read_csv('future_data.csv', index_col="Unnamed: 0")
print(future_data.head())

#新建bt实例
cerebro = bt.Cerebro()

#加数据
data = bt.feeds.PandasData(dataname = future_data, 
            timeframe = bt.TimeFrame.Minutes,
            compression = 1,
            datetime = -1,
            open=-1,
            high=-1,
            low=-1,
            close=-1,
            volume=-1,
            sessionstart = parse_hm('09:30'),
            sessionend = parse_hm('15:00'), 
            name="future_data",
            plot=True)
print(data)
a = """data = bt.feeds.PandasData(dataname = {}, 
            timeframe = {},
            compression = 1,
            datetime = -1,
            open=-1,
            high=-1,
            low=-1,
            close=-1,
            volume=-1,
            sessionstart = {},
            sessionend = {}, 
            name={},
            plot=True)""".format(future_data.head(),
                             bt.TimeFrame.Minutes,
                             parse_hm('09:30'),
                             parse_hm('15:00'),
                           "future_data")
print(a)
#需要指明数据类型是分钟K，否则读数据会报错
cerebro.adddata(data)
#实现策略类
class SmaCross(bt.Strategy):
    params = (
            ("pfast", 10),
            ("pslow", 30)
        )
    def __init__(self):
        self.close = self.datas[0].close
        sma_fast = bt.talib.SMA(self.close, timeperiod=self.params.pfast)
        sma_slow = bt.talib.SMA(self.close, timeperiod=self.params.pslow)
        # print(self.datas[0])
    def next(self):
        pass

#加策略
cerebro.addstrategy(SmaCross)

#加指标
# cerebro.addobserver(bt.observers.LogReturns)
# cerebro.addanalyzer(bt.analyzers.Returns, _name='AnnualReturn')
#运行策略
cerebro.run()

#%%
import numpy as np
future_data[np.isinf(future_data)]=1
print("finish")

#%%
future_data
