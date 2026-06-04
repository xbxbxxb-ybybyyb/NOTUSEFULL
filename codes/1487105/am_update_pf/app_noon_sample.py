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
today = datetime.datetime.today().strftime('%Y%m%d')
#####################################

transaction_time = '1300'
planb = True 
start_date = today 
end_date = today 
sample_date = today
factor_flag = 1
mode = [0]
codes = ['5160803']
transaction_time = '1300'

retrain_flag = False

if transaction_time == '1300':
    if factor_flag==1:
        # update minute Kline data
        if planb == True:
            os.system('python3 am_update_pf/am_data_planb.py')
        else:
            update_basic_data.update_basic_data(start_date,end_date)
        # update daily basic data
        update_tool.update_tool()
        # update hf factor
        update_factor.update_hfactor(start_date,end_date)
        lm.sendMessage("@Factor Data Updated Done")
    for m in mode:
        # update sample
        update_sample.update_sample(start_date,end_date,m)
        lm.sendMessage("@Sample Updated Done")



