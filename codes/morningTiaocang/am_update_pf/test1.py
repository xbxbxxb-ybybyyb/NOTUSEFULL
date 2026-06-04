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
t1 = time.time()
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


stats_list = []
for pf_code in codes:
    
    # get params
    label_open = config_path.update_params[pf_code]['label_open']
    label_update = config_path.update_params[pf_code]['label_update']
    if transaction_time != '1300':
        transaction_time = config_path.update_params[pf_code]['transaction_time']
    open_capital = config_path.update_params[pf_code]['open_capital']
    captial_fake = config_path.update_params[pf_code]['captial_fake']
    mode_open = config_path.update_params[pf_code]['mode_open']
    mode_portfolio = config_path.update_params[pf_code]['mode_portfolio']
    contact = config_path.update_params[pf_code]['contact']
    add_capital = config_path.update_params[pf_code]['add_capital']
    benchmark = config_path.update_params[pf_code]['benchmark']
    print(pf_code,config_path.update_params[pf_code])
    # doing 
    if label_open:
        print(time.tiem())
        open_portfolio.open_portfolio(transaction_time,pf_code,open_capital,today,mode=mode_open,benchmark=benchmark)
        print(time.time())
        stats = pf_generator_helper.FutureBias(today,pf_code)
        print(time.time())
        stats_list.append(stats)

if len(stats_list)>0:
    df = pd.concat(stats_list)#.to_excel(config_path.generate_pf_data_path+'/others/Future_bias_%s.xlsx' % today)
    print(df)

t2 = time.time()
print(t2-t1)
