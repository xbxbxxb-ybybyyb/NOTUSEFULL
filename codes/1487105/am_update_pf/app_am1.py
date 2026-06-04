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
from config_path import *
from xquant.xqutils.helper import link
lm = link.LinkMessage()
from xquant.factordata import FactorData
s = FactorData()
today = datetime.date.today().strftime('%Y%m%d')
pre_date = s.tradingday(today,-2)[0]
sample_date = pre_date
retrain_flag = False
print('start update sample from',sample_date,'to',sample_date)
for i in range(3,6):
    update_sample.update_sample(sample_date, sample_date, mode=i)
print('start update model predict value',sample_date)
for model_type in ['vwap','vwap300','lf']:
    update_model_predict.update_model_predict(sample_date,retrain_flag,model_type)
lm.sendMessage("@AM act done")


weight500  = s.hset('INDEX',today,'ZZ500',1)
lm.sendMessage('ZZ500:'+str(weight500['weight'].sum()))

weight500  = s.hset('INDEX',today,'HS300',1)
lm.sendMessage('HS300:'+str(weight500['weight'].sum()))


#start_date = today
#end_date = today
#trade_date_list = s.tradingday(start_date,end_date)
#def get_price_type(transaction_time='1300',transaction_period=120):
#    d = '20140102'
#    df = pd.read_pickle(basic_data_path+'minute/Amount/'+d+'.pkl').loc[d+transaction_time+'00':].iloc[:transaction_period]
#    return df.index[0].strftime('%H%M')+'_'+df.index[-1].strftime('%H%M')
#def get_predict(trade_date_list):
#    factor_custom_info = pd.read_pickle(factor_custom_path)
#    for today_date in trade_date_list:
#        model_list = ['LinearRegression','XgboostRegression']
#        timepoint_list = ['0930']
#        model_config_dict_fix={t:[(m,t,get_price_type(t,30)+'_re_5d',5,240) for m in model_list] for t in timepoint_list}
#        for k,v in model_config_dict_fix.items():
#            for model_config in v:
#                factor_list = factor_custom_info[k][model_config[0]]['factors']
#                update_model_predict.update_single_model(model_root_path,model_config[0],k,
#                        model_config[2],model_config[3],train_window=model_config[4],sample_flag=True,factor_list=factor_list,
#                    today_date=today_date,train_flag=retrain_flag,act_check=True)
#get_predict(trade_date_list)
#lm.sendMessage("@AM hf act done")