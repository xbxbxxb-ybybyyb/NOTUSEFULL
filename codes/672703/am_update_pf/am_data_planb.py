import sys
import os
import pandas as pd
import numpy as np
import datetime
import time
import copy
import multiprocessing as mp
import pickle
import warnings
warnings.filterwarnings("ignore")
# from xquant.marketdata import MarketData
from xquant.factordata import FactorData
import matplotlib.pyplot as plt
from xquant.xqutils.helper import link
from xquant.thirdpartydata.marketdata import MarketData

t1=time.time()
# data_store_path = '/data/user/013417/temp/'
data_store_path = '/data/group/800020/AlphaDataCenter/Basic/minute/'
stock_list=pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/minute/Close/20190103.pkl').columns.tolist()
ma = MarketData()
today = datetime.datetime.today().strftime('%Y%m%d')
all_price = ['open', 'high', 'low', 'close']
all_vol = ['volume', 'amt']

data_am = ma.getAmKline1M4ZTDataFrame(mddate=today)
stock_exist=set(data_am.unstack()['close'].columns)
stock_in=list(set(stock_list)&(stock_exist))
stock_out = list(set(stock_list)-(stock_exist))
key_map = {'open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume','amt':'Amount'}
print('Data Load Time: ',time.time()-t1)

for p in all_price:
#     print(p)
    mapper = key_map[p]
    price_data = data_am.unstack()[p]
    price_data=price_data.rename_axis(mapper=None, axis='columns')
    price_data=price_data.rename_axis(mapper=None, axis='index')
    price_data=price_data.between_time(start_time='9:30:00', end_time='11:30:00')
    price_data=price_data.fillna(method = 'ffill')
    price_data = price_data[stock_in]
    for ss in stock_out:
        price_data[ss]=np.nan
    price_data=price_data.reindex(columns=stock_list)
    price_data.to_pickle(data_store_path+mapper+'/'+today+'.pkl')

for v in all_vol:
#     print(v)
    mapper = key_map[v]
    vol_data = data_am.unstack()[v]
    vol_data=vol_data.rename_axis(mapper=None, axis='columns')
    vol_data=vol_data.rename_axis(mapper=None, axis='index')
    vol_data=vol_data.between_time(start_time='9:30:00', end_time='11:30:00')
    vol_data = vol_data[stock_in]
    for ss in stock_out:
        vol_data[ss]=np.nan
    vol_data=vol_data.fillna(0)
    vol_data=vol_data.reindex(columns=stock_list)
    vol_data.to_pickle(data_store_path+mapper+'/'+today+'.pkl')

print('Minute Basic Data Updated.')


datas = copy.deepcopy(data_am).reset_index()

def get_status(stock):
    stock_data = datas[datas.stock == stock].sort_values(by='mdtime')
    stock_data.index = stock_data.mdtime.values
    stock_data = stock_data.between_time(start_time='9:30:00', end_time='11:30:00')
    if len(stock_data)==0:
        return 1, stock
    if len(stock_data.dropna())==0:
        return 2, stock
    stock_data[['open','high','low','close']] = stock_data[['open','high','low','close']].fillna(method = 'ffill')
    stock_data[['volume','amt']] = stock_data[['volume','amt']].fillna(0)
    stock_data[['open','high','low','close']] = stock_data[['open','high','low','close']].fillna(method = 'bfill')
    if len(stock_data.dropna()) != 120:
        print(stock,'morning missing', stock,)
        return 3, stock
    if (stock_data['volume'].sum() == 0):
        print('no trade ', stock,)
        return 5, stock
    return 0, stock


def update_minute_status()
    print('MInute Status Update Start.')
    pool = mp.Pool(processes=24)
    tasks = []
    for stock in stock_list:
#         print(stock, 'Minute Status Update Start')
        tasks.append(pool.apply_async(get_status, (stock,)))
    pool.close()
    pool.join()

    error = []
    status_dict={}
    for t in tasks:
        try:
            cc = t.get()
            s = cc[-1]
            status_dict[s] = cc[0]
        except:
            error.append(0)
            pass 
    if len(error) > 0:
        print('Multi Process Error: some procecess died.')

    status_today = pd.Series(status_dict, name=pd.to_datetime(today))
    status_today = status_today.to_frame().transpose()

    if not os.path.exists(data_store_path + 'Minute_Status.pkl'):
        status_today.to_pickle(data_store_path + 'Minute_Status.pkl')
    else:
        history = pd.read_pickle(data_store_path + 'Minute_Status.pkl')
        # assert date not in history.index 
        if today in history.index:
            history = history[history.index!=today]
            print('Minute_Status Updated Again Today.')
        new = pd.concat([history, status_today])
        new = new.sort_index()
        new.to_pickle(data_store_path + 'Minute_Status.pkl')

    print('*********** Minute Data Finish Cleaning, used ', time.time()-t1, today)
update_minute_status()