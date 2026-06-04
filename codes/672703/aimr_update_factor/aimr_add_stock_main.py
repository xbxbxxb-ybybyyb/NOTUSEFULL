from xquant.compute.aimr import AIMR
import json
import pandas as pd
import os 
import datetime
from xquant.factordata import FactorData
s = FactorData()
print("start")
start_end_date = {}
today = datetime.date.today().strftime('%Y%m%d')
today = s.tradingday(today,-1)[0]
start_end_date['start_date'] = '20190701'
start_end_date['end_date'] = '20200618'
path= '/data/group/800020/AlphaExperiment/Transit/update_factor/'
if not os.path.exists(path):
    os.makedirs(path)
pd.to_pickle(start_end_date,path+'start_end_date.pkl')
factor_dict=pd.read_pickle(path+'factor_dict.pkl')

params = {
    "parallel_list": list(factor_dict.keys()),   
    "tag":"xquant",
    "cpu":24,
    "gpu":0,
    "memory":100000
}

AIMR.runTasks('aimr_update_factor/aimr_add_stock_factor.py',json.dumps(params))