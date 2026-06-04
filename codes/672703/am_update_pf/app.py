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
import update_valid_stock
import update_portfolio
from xquant.xqutils.helper import link
lm = link.LinkMessage()

today = datetime.datetime.today().strftime('%Y%m%d')
transaction_time = '1300'
pf_code = '5160701'
reb = True 
planb = True 
start_date = today 
end_date = today 
factor_flag = 1
mode = [0]
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
    lm.sendMessage("Factor Data Updated Done")
for m in mode:
    # update sample
    update_sample.update_sample(start_date,end_date,m)
    lm.sendMessage("Sample Updated Done")
# update model predict
update_model_predict.run(today)
time2 = time.time()
period = time2-time1
lm.sendMessage("Activation Updated done,time(min): {0}".format(str(period)))

# update valid stock
update_valid_stock.update_valid_stock(today,transaction_time,pool_stock_path=config_path.pool_stock_path)

# update portfolio
update_portfolio.update_portfolio(config_path.reb_path,today,transaction_time,pf_code,reb)
    