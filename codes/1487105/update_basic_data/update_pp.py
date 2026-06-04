import numpy as np 
import pandas as pd 
import os
import time
import datetime
from xquant.xqutils.helper import link
from xquant.factordata import FactorData
from config_path import *
def save_data(df_update,path):
    if os.path.exists(path):
        store_data = pd.read_pickle(path)
    else:
        store_data = df_update
    if isinstance(df_update,dict):
        if sorted(df_update.keys())!=sorted(store_data.keys()):
            store_data = df_update
        else:
            for k,v in store_data.items():
                v=v.append(df_update[k])
                v = v.loc[~v.index.duplicated(keep='last')].sort_index()
                store_data[k] = v.astype(np.float64)
    else:
        store_data = store_data.append(df_update).astype(np.float64)
        store_data = store_data.loc[~store_data.index.duplicated(keep='last')].sort_index()
    pd.to_pickle(store_data,path)
    return store_data
def update_ampm(date_list):
    am = {}
    pm = {}
    for day in date_list:
        print(day)
        amt = pd.read_pickle(basic_data_path+'minute/Amount/'+day+'.pkl')
        vol = pd.read_pickle(basic_data_path+'minute/Volume/'+day+'.pkl')
        am[day] = (amt[:120].sum()/vol[:120].sum())
        pm[day] = (amt[120:].sum()/vol[120:].sum())

    am_vwap = pd.DataFrame(am).T
    pm_vwap = pd.DataFrame(pm).T
    am_vwap[~np.isfinite(am_vwap)]=np.nan
    pm_vwap[~np.isfinite(pm_vwap)]=np.nan
    am_vwap.index = pd.to_datetime(am_vwap.index)
    pm_vwap.index = pd.to_datetime(pm_vwap.index)

    adj=pd.read_pickle(basic_data_path+'daily/adjfactor.pkl').loc[am_vwap.index]
    am_vwap = am_vwap*adj
    pm_vwap = pm_vwap*adj
    save_data(am_vwap,basic_data_path+'daily/vwap_am_adj_cz.pkl')
    save_data(pm_vwap,basic_data_path+'daily/vwap_pm_adj_cz.pkl')
    print('Intro-day vwap data generated.')
def update_quarter():
    path = basic_data_path+'quarter/'
    qts = (os.listdir(path))
    # qts=[q[:-4] for q in qts]
    for q in qts:
        temp = pd.read_pickle(path+q)
        if temp.iloc[-1,:].notnull().sum() < 1:
            temp.iloc[-1,:]=temp.iloc[-2,:]
            temp.to_pickle(path+q)   
def update_amtfix(date_list):
    stock_list = pd.read_pickle(basic_daily_path+'close.pkl').columns
    amt = {}
    timepoint_list = ['0930','1000', '1030', '1100', '1300', '1330', '1400', '1430']
    for t in timepoint_list:
        amt[t] = pd.DataFrame(index=pd.to_datetime(date_list),columns=stock_list)
    for date in date_list:
        print(date)
        df = pd.read_pickle(basic_minute_path+'Amount/'+date+'.pkl')
        t = timepoint_list[0]
        for t in timepoint_list:
            amt[t].loc[date] = df.loc[pd.to_datetime(date+t+'00'):].iloc[:30].sum()
    for k,v in amt.items():
        save_data(v,basic_daily_path+'amt_'+str(k)+'.pkl')
def update_stpt():
    universe=sorted(pd.read_pickle(basic_daily_path+'stpt.pkl').columns.tolist())
    fa = FactorData()
    stpt = np.ones((1, len(universe)))
    temp=fa.stock_filter(universe, today, 'STPT').set_index('stock')['stock_name']
    if len(temp) == 0:
        stpt = 0
    else:
        idx = ~temp.reindex(universe).isnull().values
        stpt[0,idx] = 0
    stpt = pd.DataFrame(index=pd.to_datetime([today]),columns=universe,data=stpt)
    save_data(stpt,basic_daily_path+'stpt.pkl')
lm = link.LinkMessage()
try:
    factorData = FactorData()
    date_list = factorData.tradingday(today,today)
    update_stpt()
    update_ampm(date_list)
    update_amtfix(date_list)
    update_quarter()
    lm.sendMessage("{0} stpt ampmvwap amtfix quarter Updated.".format(today,))
except Exception:
    lm.sendMessage("{0} stpt ampmvwap amtfix quarter has problem.".format(today,))