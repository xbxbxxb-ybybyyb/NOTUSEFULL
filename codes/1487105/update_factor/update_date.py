from xquant.factordata import FactorData
import sys 
sys.path.insert(0,'update_factor/')
from config_path import *
import pandas as pd 
import datetime
s = FactorData()
print("start")
start_end_date = {}
#today = datetime.date.today().strftime('%Y%m%d')
#today = s.tradingday(today,-1)[0]
#today = '20210715' #@
start_end_date['start_date'] = today
start_end_date['end_date'] = today
pd.to_pickle(start_end_date,update_date_path)
#import numpy as np 
#import pandas as pd 
#import os
#def save_data(df_update,path):
#    if os.path.exists(path):
#        store_data = pd.read_pickle(path)
#    else:
#        store_data = df_update
#    if isinstance(df_update,dict):
#        if sorted(df_update.keys())!=sorted(store_data.keys()):
#            store_data = df_update
#        else:
#            for k,v in store_data.items():
#                v=v.append(df_update[k])
#                v = v.loc[~v.index.duplicated(keep='last')].sort_index()
#                store_data[k] = v.astype(np.float64)
#    else:
#        store_data = store_data.append(df_update).astype(np.float64)
#        store_data = store_data.loc[~store_data.index.duplicated(keep='last')].sort_index()
#    pd.to_pickle(store_data,path)
#    return store_data
#start_date = today
#end_date = today
#date_list = sorted([date[:-4] for date in os.listdir('/data/group/800020/AlphaDataCenter/Basic/minute/Amount/') if date[:-4]>=start_date])
#stock_list = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/close.pkl').columns
#amt = {}
#timepoint_list = ['0930','1000', '1030', '1100', '1300', '1330', '1400', '1430']
#for t in timepoint_list:
#    amt[t] = pd.DataFrame(index=pd.to_datetime(date_list),columns=stock_list)
#for date in date_list:
#    print(date)
#    df = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/minute/Amount/'+date+'.pkl')
#    t = timepoint_list[0]
#    for t in timepoint_list:
#        amt[t].loc[date] = df.loc[pd.to_datetime(date+t+'00'):].iloc[:30].sum()
#for k,v in amt.items():
#    save_data(v,'/data/group/800020/AlphaDataCenter/Basic/daily/amt_'+str(k)+'.pkl')