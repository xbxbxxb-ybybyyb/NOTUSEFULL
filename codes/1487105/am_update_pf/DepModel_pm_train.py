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
# latest trading day
sample_date = s.tradingday(today,-2)[-1]   
                
retrain_flag = True      
for model_type in ['pm']:
    lm.sendMessage("@Dep %s Model and act Updating" % model_type)
    update_model_predict.update_model_predict(sample_date,retrain_flag,model_type,act_check=True,pred_label=False)
    lm.sendMessage("@Dep %s Model and act Done" % model_type)




