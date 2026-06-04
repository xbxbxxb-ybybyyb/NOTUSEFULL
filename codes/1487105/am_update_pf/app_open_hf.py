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
import open_portfolio_fix

s = FactorData()
today = datetime.date.today().strftime('%Y%m%d')
pre_date = s.tradingday(today,-2)[0]
sample_date = pre_date
retrain_flag = False

codes = ['5160803']#,'5160803','5160304'
# update valid stock
transaction_time = '0930hf'
open_capital = 8e8
stats_list = []
for pf_code in codes:    
    # get params
#    label_open = config_path.update_params[pf_code]['label_open']
#    label_update = config_path.update_params[pf_code]['label_update']
#    transaction_time = config_path.update_params[pf_code]['transaction_time']
#    open_capital = config_path.update_params[pf_code]['open_capital']
#    captial_fake = config_path.update_params[pf_code]['captial_fake']
#    mode_open = config_path.update_params[pf_code]['mode_open']
#    mode_portfolio = config_path.update_params[pf_code]['mode_portfolio']
#    contact = config_path.update_params[pf_code]['contact']
#    add_capital = config_path.update_params[pf_code]['add_capital']
#    benchmark = config_path.update_params[pf_code]['benchmark']
#    print(pf_code,config_path.update_params[pf_code])
    # doing 
    if True:
        open_portfolio_fix.half_open_portfolio(transaction_time,pf_code,open_capital,today, \
        mode=1,benchmark='500',test_label=False)
        stats = pf_generator_helper.FutureBias(today,pf_code)
        stats_list.append(stats)
        pd.concat(stats_list).to_excel(config_path.generate_pf_data_path+'/others/Future_bias_%s_%s.xlsx' % (today,pf_code))

    