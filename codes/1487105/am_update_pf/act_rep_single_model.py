import time
import pandas as pd
time1 = time.time()
import datetime 
import os 
import sys
sys.path.insert(0,'am_update_pf/')
import update_basic_data
import update_tool 
import update_factor
import update_sample
import update_model_predict
from config_path import *
import pf_generator_helper
import update_valid_stock
import update_portfolio
import open_portfolio
from xquant.xqutils.helper import link
lm = link.LinkMessage()
from xquant.factordata import FactorData
s = FactorData()

close = pd.read_pickle('/data/group/800469/AlphaDataCenter/Basic/daily/close.pkl')
dates = list(close.index)
dates_ = [str(i.year)+str(i.month).zfill(2)+str(i.day).zfill(2) for i in dates]
date_start = '20210702'
date_end = '20210809'

dates_.append(date_end)#@
dates_.sort()


dates = [i for i in dates_ if i>=date_start and i<=date_end]
step = 1
count = 0
dates_train = []
for i in range(1,len(dates)):
    ds = dates[i-1]    
    de = dates[i]
    sample_date = ds
    next_month = pd.to_datetime(ds).replace(day=28) + datetime.timedelta(days=4)  # this will never fail
    last_day = next_month - datetime.timedelta(days=next_month.day)
    last_day= last_day.strftime('%Y%m%d')   
    # find gab, if gab_days>1 , or not the last day between months
    if (pd.to_datetime(de) - pd.to_datetime(ds)).days > 1 or i == 1:
        count+=1
        if step == 1:
            ref = 0
        else:
            ref = 1
        if count % step == ref:
            dates_train.append(ds)
            retrain_flag = True        
        else:
            retrain_flag = False        
        if len(dates_train)>1:
            print(ds,int(ds[-2:])-int(dates_train[-2][-2:]))
        else:
            print(ds)
    else:
        retrain_flag = False                           
    print('#########',sample_date,retrain_flag)
    # for model_type in ['vwap']:
    #     update_model_predict.update_model_predict(sample_date,retrain_flag,model_type)


               # ('XgbSP','vwap300','neu_vwap_re_5d',5,240,True),
               # ('LinearRegression','vwap300','vwap_re_5d',5,240,True),
               # ('KerasDeepFMMulti','vwap300','vwap_re_5d',5,480,False)]

    model_type = 'vwap300'
    factor_custom_info = pd.read_pickle(factor_custom_path)
    custom_params = {}
    model_config = ('KerasDeepFMMulti','vwap300','vwap_re_5d',5,480,False)
    update_model_predict.update_single_model(root_path=model_root_path,modelname=model_config[0],strategy_type=model_type,label_name=model_config[2],
                gap=model_config[3],train_window=model_config[4],sample_flag=model_config[5],factor_list=factor_custom_info[model_type][model_config[0]],
                today_date=sample_date,train_flag=retrain_flag,act_check=True,custom_params=custom_params)










