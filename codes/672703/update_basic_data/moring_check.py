import sys
import os
import pandas as pd
import numpy as np
import datetime
import platform
import multiprocessing as mp
import pickle
import warnings
warnings.filterwarnings("ignore")
# from xquant.marketdata import MarketData
from xquant.factordata import FactorData
import matplotlib.pyplot as plt
from xquant.xqutils.helper import link
from xquant.thirdpartydata.marketdata import MarketData


market_list = pd.read_excel('/data/user/013417/data_check/market_data.xlsx',header=None)[0].tolist()


from xquant.factordata import FactorData
factorData = FactorData()
# stock_list = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/is_valid.pkl').columns.tolist()
# start_date= '20160101'
# end_date ='20191231'
# trade_dates = factorData.tradingday(start_date,end_date)

ma = MarketData()
today = datetime.datetime.today().strftime('%Y%m%d')

market_list = pd.read_excel('/data/user/013417/data_check/market_data.xlsx',header=None)[0].tolist()
# all_price = market_list[-7:-3]
# all_vol = market_list[-3:]
all_price = ['open', 'high', 'low', 'close']
all_vol = ['volume', 'amt']




def check_data(date):
    error = []
    database = ma.getAmKline1M4ZTDataFrame(mddate=date)
    # 价格数据是否含0
    for p in all_price:
        if 0 in database[p].values:
            print(date + ' Invalid Price Data. Zero Values in: ', p)
            error.append('Invalid Price Data. Zero Values in: '+p)
    # 价格数据是否在合理范围
    for p in all_price:
        temp = database[p].fillna(1).values
        if True in (temp < 0):
            print(date + ' Invalid Price Data. Price Smaller than 0: ', p)
            error.append('Invalid Price Data. Price Smaller than 0: '+ p)
        if True in (temp > 1500):
            print(date + ' Invalid Price Data. Price Bigger than 1500: ', p)
            error.append('Invalid Price Data. Price Bigger than 1500: '+ p)
    # close，open，vwap是否在high，low之间
    for p in ['close', 'open',]:
        temp = database[p].fillna(0).values
        if True in (temp - database['high'].fillna(0).values > 0.01):
            print(date + ' Invalid Price Data. Price Bigger than High_Price: ', p)
            error.append('Invalid Price Data. Price Bigger than High_Price: '+ p)
        if True in (temp - database['low'].fillna(0).values < -0.01):
            print(date + ' Invalid Price Data. Price Smaller than Low_Price: ', p)
            error.append('Invalid Price Data. Price Smaller than Low_Price: '+ p)
    # high与low之间的间距应小于20%
    if True in (database['high'].values - database['low'].values - 0.2 * database['high'].values > 0):
        print(date + ' Invalid Price Data. Swing over 20%.')
        error.append('Invalid Price Data. Swing over 20%.')
    # 各种成交量相关数据不能小于0
    for v in all_vol:
        flag = (database[v].values < 0. )
        if True in flag:
            print(date + ' Invalid Volume Data. ' +v+ ' Data Wrong.')
            error.append('Invalid Volume Data. ' +v+ ' Data Wrong.')
    print(date,' check finish')
    return date, error

flag=False
try:
    _,error =  check_data(today)
    if len(error) > 0:
        flag=False
    else:
        flag=True
    flag1 = True
except:
    flag1 = False

print(error)
lm = link.LinkMessage()
lm.sendMessage("{0} Morning Data Exist Flag: {1}".format(today,flag1))
lm.sendMessage("{0} Morning Data Checked OK Flag: {1}".format(today,flag))