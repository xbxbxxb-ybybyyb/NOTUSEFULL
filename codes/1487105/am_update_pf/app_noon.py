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
    # update model predict
    print('start update model predict value',sample_date)
    update_model_predict.update_model_predict(sample_date,retrain_flag,model_type='pm')    
    time2 = time.time()
    period = time2-time1
    lm.sendMessage("@Activation Updated done,time(s): {0}".format(str(period)))


# update valid stock

update_valid_stock.update_valid_stock(today,transaction_time,pool_stock_path=config_path.pool_stock_path)
lm.sendMessage("@Noon Valid Stock Updated done")
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
#    if label_open:
#        open_portfolio.open_portfolio(transaction_time,pf_code,open_capital,today,mode=mode_open,benchmark=benchmark)
#        stats = pf_generator_helper.FutureBias(today,pf_code)
#        stats_list.append(stats)
    if label_update:
        update_portfolio.update_portfolio(captial_fake,config_path.reb_path,today,transaction_time,pf_code,\
            mode=mode_portfolio,benchmark=benchmark)
        act_str = pf_generator_helper.get_act_stat(today,transaction_time)
        print("@%s act&weight stat: " % pf_code +act_str+','+today)
        lm.sendMessage("@%s act&weight stat: " % pf_code +act_str+','+today)
if len(stats_list)>0:
    pd.concat(stats_list).to_excel(config_path.generate_pf_data_path+'/others/Future_bias_%s.xlsx' % today)