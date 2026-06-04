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
today = datetime.date.today().strftime('%Y%m%d')
pre_date = s.tradingday(today,-2)[0]
sample_date = pre_date
retrain_flag = False
#print('start update sample from',sample_date,'to',sample_date)
#for i in range(3,6):
#    update_sample.update_sample(sample_date, sample_date, mode=i)
#print('start update model predict value',sample_date)
#for model_type in ['vwap','am']:
#    update_model_predict.update_model_predict(sample_date,retrain_flag,model_type)
codes = ['5160503','5160304']#,'5160803','5160304'
# update valid stock
transaction_time = '0930'
update_valid_stock.update_valid_stock(today,transaction_time,\
pool_stock_path=config_path.pool_stock_path,test_label=True)
lm.sendMessage("@AM Valid Stock Updated done")
stats_list = []
for pf_code in codes:    
    # get params
    label_open = config_path.update_params[pf_code]['label_open']
    label_update = config_path.update_params[pf_code]['label_update']
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
        open_portfolio.open_portfolio(transaction_time,pf_code,open_capital,today,mode=mode_open,benchmark=benchmark)
        stats = pf_generator_helper.FutureBias(today,pf_code)
        stats_list.append(stats)
    if label_update:
        update_portfolio.update_portfolio(captial_fake,config_path.reb_path,today,transaction_time,pf_code,\
            mode=mode_portfolio,benchmark=benchmark)
        act_str = pf_generator_helper.get_act_stat(today,transaction_time,benchmark=benchmark)
        print("@%s act&weight stat: " % pf_code +act_str+','+today)
        lm.sendMessage("@%s act&weight stat: " % pf_code +act_str+','+today)

if len(stats_list)>0:
    pd.concat(stats_list).to_excel(config_path.generate_pf_data_path+'/others/Future_bias_%s.xlsx' % today)