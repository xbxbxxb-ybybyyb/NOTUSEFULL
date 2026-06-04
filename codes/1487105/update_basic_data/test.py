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
today = '20211011'
start_date = today
end_date = today

date_list = sorted([date[:-4] for date in os.listdir(basic_minute_path+'Amount/') if (date[:-4]>=start_date)&(date[:-4]<=end_date)])
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

lm = link.LinkMessage()
lm.sendMessage("{0} Plus Data Updated.".format(today,))



universe=sorted(pd.read_pickle(basic_daily_path+'stpt.pkl').columns.tolist())
fa = FactorData()
stpt = np.ones((1, len(universe)))
temp=fa.stock_filter(universe, today, 'STPT').set_index('stock')['stock_name']
if len(temp) == 0:
    stpt = 0
else:
    idx = ~temp.reindex(universe).isnull().values
    stpt[0,idx] = 0

kk=pd.read_pickle(basic_daily_path+'stpt.pkl')
kk=kk[kk.index!=today]
kk = kk.append(pd.DataFrame(stpt,index=[pd.to_datetime(today)],columns=universe))
kk.sort_index().to_pickle(basic_daily_path+'stpt.pkl')