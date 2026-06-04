import os
import time
import datetime
import numpy as np
import pandas as pd
from xquant.xqutils.helper import link
from xquant.factordata import FactorData

from MinuteUpdateXquant import MinuteUpdateXquant
from DailyDataUpdateXquant import DailyDataUpdateXquant
from config_path import * 
def daily_data_update_flag(today,flag):    
    flag_path = pool_manage_path+'DataDailyUpdateFlag.pkl'
    today_flag = pd.DataFrame(flag,index=[today],columns=['flag'])
    if os.path.exists(flag_path):
        flag_df = pd.read_pickle(flag_path)
        if today in flag_df.index:
            flag_df.loc[today] = flag
        else:
            flag_df = pd.concat([flag_df,today_flag],axis=0)
        flag_df.to_pickle(flag_path)
    else:
        today_flag.to_pickle(flag_path)
        
def daily_data_update(start_date,end_date):
    print('update data from {0} to {1}'.format(start_date,end_date))
    date_list = FactorData().tradingday(start_date, end_date)

    ################# update minute data #################    
    MinuteUpdateXquant(date_list,basic_minute_path,pool_manage_path).update_data()

    ################# update daily data #################
    DailyDataUpdateXquant(start_date=start_date,end_date=end_date,save_raw_flag=False,data_center_path=data_center_path).update_data() 
    

if __name__=='__main__':  
#    today = datetime.datetime.today().strftime('%Y%m%d')
#    today='20211011'
    start_date = today  #'20191125'
    end_date = today  #'20191125'
    print(today)    
    lm = link.LinkMessage()
    daily_data_update(start_date,end_date)
    flag = True
#    try:   
#        daily_data_update(start_date,end_date)
#        flag = True    
#    except:
#        flag = False
#        lm.sendMessage("{0} XQuant Data Update Flag: {1}".format(today,flag))
#        daily_data_update(start_date,end_date)
        
    lm.sendMessage("{0} XQuant Data Update Flag: {1}".format(today,flag))
    daily_data_update_flag(end_date,flag)