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
print('start update sample from',sample_date,'to',sample_date)
for i in range(3,6):
    update_sample.update_sample(sample_date, sample_date, mode=i)
print('start update model predict value',sample_date)
for model_type in ['vwap','am']:
    update_model_predict.update_model_predict(sample_date,retrain_flag,model_type)
lm.sendMessage("@AM act done")