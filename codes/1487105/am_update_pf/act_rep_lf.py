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
import config_path 
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
dates_.sort()

date_start = '20170101'
date_end = '20200101'
dates = [i for i in dates_ if i>=date_start and i<=date_end]
step =4
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
        if count % step == 1:
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
#    for model_type in ['pm']:
#        update_model_predict.update_model_predict(sample_date,retrain_flag,model_type)
    update_model_predict.update_model_fix_predict(root_path=config_path.model_root_path,
            today_date = sample_date,retrain_flag = retrain_flag,lookback_period_max = 240,
            model_config_list = [
                    ('XgbRegTSFourModel','pm','1300_1459_re_5d',5,240)
                        ],suffix=None)
