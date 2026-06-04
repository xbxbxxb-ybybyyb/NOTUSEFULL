import time
import shutil
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
pre_date = s.tradingday(today,-1)[0]
sample_date = pre_date
retrain_flag = True

for model_type in ['lf']:
    lm.sendMessage("@Dep %s Model and act Updating" % model_type)
    update_model_predict.update_model_predict(sample_date,retrain_flag,model_type,act_check=True)
    lm.sendMessage("@Dep %s Model and act Done" % model_type)
    
# save model
path_model = config_path.model_root_path + '/Models/'
path_model_his = config_path.model_root_path + '/Models_history/%s/' % today
try:
    os.system('mkdir %s' % path_model_his)
except:
    pass

os.system('cp -fr %s/* %s/' % (path_model,path_model_his))
lm.sendMessage("@Dep lf %s Model Saved" % today)  
    
    