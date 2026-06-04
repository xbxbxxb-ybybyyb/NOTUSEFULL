import time
import pandas as pd
time1 = time.time()
import datetime 
import os 
import sys
import update_model_predict
from config_path import *

import time
import os
close = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/close.pkl')
dates = [d.strftime('%Y%m%d') for d in close.index]
train_start = '20180101'
date_start = '20200720'
date_end = '20200730'
step = 5
count = 0
lookback_period_max = 240
retrain_flag = True  
root_path = model_root_path
dates = sorted([i for i in dates if i>=date_start and i<=date_end])
for today_date in dates:
    if (count==0) or (pd.to_datetime(today_date).strftime("%w")==5):
        retrain_flag = True
    else: 
        retrain_flag = False          
    print('###########%s %s############' % (today_date,str(retrain_flag)))
    count+=1                            
    update_model_predict.update_model_day_predict(root_path,today_date,retrain_flag,lookback_period_max,
            model_config_list = [
                    ('LinearRegression','vwap','0930_1129_re_5d',5,240)
                        ])