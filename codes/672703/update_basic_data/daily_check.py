
import sys
import os
import pandas as pd
import numpy as np
import datetime
from xquant.xqutils.helper import link



market_list = pd.read_excel('/data/user/013417/data_check/market_data.xlsx',header=None)[0].tolist()

# Xquant数据读入
from xquant.factordata import FactorData
factorData = FactorData()
stock_list = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/is_valid.pkl').columns.tolist()
# start_date = '20181231'
# end_date ='20191231'
# trade_dates = factorData.tradingday(start_date,end_date)
today = datetime.datetime.today().strftime('%Y%m%d')
trade_dates = [today]

error = []


database = factorData.get_factor_value('Basic_factor', stock_list, trade_dates, market_list[:-7])
all_price = market_list[:6] + market_list[26:31]
# print(database)


# 价格数据是否含0
for p in all_price:
    if 0 in database[p].values:
        flag = (0 in database[p].values)
        print('Invalid Price Data. Zero Values in: ', p)
        print(database[flag])
        error.append('Invalid Price Data. Zero Values in: ' + p)

# 价格数据是否在合理范围,不含adj价格
for p in market_list[:6]:
    temp = database[p].fillna(1).values
    if True in (temp < 0):
        print('Invalid Price Data. Price Smaller than 0: ', p)
        print(database[(temp < 0)])
        error.append('Invalid Price Data. Price Smaller than 0: '+ p)
    if True in (temp > 1500):
        print('Invalid Price Data. Price Bigger than 1500: ', p)
        print(database[(temp > 1500)])
        error.append('Invalid Price Data. Price Bigger than 1500: '+ p)

# close，open，vwap是否在high，low之间
for p in ['close', 'open', 'vwap']:
    temp = database[database['trade_status']!='停牌'][p].fillna(0).values
    if True in (temp - database[database['trade_status']!='停牌']['high'].fillna(0).values > 0.01):
        print('Invalid Price Data. Price Bigger than High_Price: ', p)
        print(database[(temp - database[database['trade_status']!='停牌']['high'].fillna(0).values > 0.01)][['open','close','high','low','vwap','trade_status','susp_reason','stpt']])
        error.append('Invalid Price Data. Price Bigger than High_Price: '+ p)
    if True in (temp - database[database['trade_status']!='停牌']['low'].fillna(0).values < -0.01):
        print('Invalid Price Data. Price Smaller than Low_Price: ', p)
        print(database[(temp - database[database['trade_status']!='停牌']['low'].fillna(0).values < -0.01)][['open','close','high','low','vwap','trade_status','susp_reason']])
        error.append('Invalid Price Data. Price Smaller than Low_Price: '+ p)

# high与low之间的间距应小于20%
flag=(database['high_badj'].values - database['low_badj'].values - 0.21 * database['pre_close_badj'].values > 0)
if True in flag:
    reason = set(database[flag]['trade_status'].tolist())
    if len(reason)>1:
        print('Invalid Price Data. Swing over 20%')
        print(database[flag])
        print('Trade Status for Wrong Stocks: ', reason)
        error.append('Invalid Price Data. Swing over 20%')


# 涨跌幅与振幅是否对上
flag = ((database['close'] - database['pre_close'] - database['chg']).abs().values > 0.00001)
# database[flag]
if True in flag:
    print('Invalid Price Data. Price_Change Data Wrong.')
    print(database[flag])
    error.append('Invalid Price Data. Price_Change Data Wrong.')

flag = ((database['high'] - database['low']) / database['pre_close'] - database['swing']).abs().values > 0.0001
if True in flag:
    print('Invalid Price Data. Swing Data Wrong.')
    print(database[flag])
    error.append('Invalid Price Data. Swing Data Wrong.')


# 涨跌幅是否在10%内
flag = (database['high_badj'].values -  1.105 * database['pre_close_badj'].values > 0.0)
temp=database[flag]
temp=temp[(temp['trade_status']=='交易')&(temp['close']>1)]
if temp.size>0:
    print(temp[['high','low','close','pre_close','pct_chg','high_badj','low_badj','close_badj','pre_close_badj','adjfactor','trade_status','stpt']])
    print('Invalid Price Data. Up Range Over 10%.')
    error.append('Invalid Price Data. Up Range Over 10%.')


flag = (database['low_badj'].values -  (1-0.105) * database['pre_close_badj'].values < 0.0)
temp=database[flag]
temp=temp[(temp['trade_status']=='交易')&(temp['close']>1)]
if temp.size>0:
    print(temp[['high','low','close','pre_close','pct_chg','high_badj','low_badj','close_badj','pre_close_badj','adjfactor','trade_status','stpt']])
    print('Invalid Price Data. Down Range Over 10%.')
    error.append('Invalid Price Data. Down Range Over 10%.')


# adjfactor是否可以对上
for p in market_list[:5]:
    if True in ((database[p]*database['adjfactor'] - database[p + '_badj']).abs() > 0.001):
        print('Invalid Price Data. Adjusted Price Wrong: ', p)
        print(database[((database[p]*database['adjfactor'] - database[p + '_badj']).abs() > 0.001)])
        error.append('Invalid Price Data. Adjusted Price Wrong: '+ p)


# 成交量数据不能小于0
flag = (database['volume'].values < 0. )
# database[['volume','amt','close','dealnum','trade_status','susp_reason']][flag]
if True in flag:
    print('Invalid Volume Data. Volume Data Wrong.')
    print(database[flag])
    error.append('Invalid Volume Data. Volume Data Wrong.')

flag = (database['amt'].values < 0. )
if True in flag:
    print('Invalid Volume Data. Amount Data Wrong.')
    print(database[flag])
    error.append('Invalid Volume Data. Amount Data Wrong.')

flag = (database['dealnum'].values < 0. )
if True in flag:
    print('Invalid Volume Data. Dealnum Data Wrong.')
    print(database[flag])
    error.append('Invalid Volume Data. Dealnum Data Wrong.')


for d in ['total_shares','free_float_shares','float_a_shares','share_totala']:
    flag = (database[d].values < 0. )
    if True in flag:
        print('Invalid Volume Data. Shares Data Wrong: ', d)
        print(database[flag])
        error.append('Invalid Volume Data. Shares Data Wrong: '+ d)


print('check finish')
if len(error)>0:
    f=False
else:
    f=True


lm = link.LinkMessage()
lm.sendMessage("{0} Daily Data Check Flag: {1}".format(today,f))