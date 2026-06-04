from xquant.compute.aimr import AIMR
import json
import pandas as pd
import datetime
from xquant.factordata import FactorData
import sys 
sys.path.insert(0,'update_factor/')
from config_path import *
s = FactorData()
print("start")
#start_end_date = {}
#today = datetime.date.today().strftime('%Y%m%d')
#today = s.tradingday(today,-1)[0]
#start_end_date['start_date'] = today
#start_end_date['end_date'] = today
#pd.to_pickle(start_end_date,update_date_path)
#import numpy as np
#import pandas as pd
#from itertools import chain
#update_date_path = '/data/group/800020/AlphaDataCenter/Transit/update_factor/start_end_date.pkl'
#factor_dict_ori = '/data/group/800020/AlphaDataCenter/Transit/update_factor/factor_dict.pkl'
#aimr_factor_dict_path = '/data/group/800020/AlphaDataCenter/Transit/update_factor/aimr_factor_dict.pkl'
#multi_factor_dict_path = '/data/group/800020/AlphaDataCenter/Transit/update_factor/multi_factor_dict.pkl'
#factor_dict = pd.read_pickle(factor_dict_ori)
#factor_list = list(chain.from_iterable(factor_dict.values()))
#multiprocess_factor = ['CSTurnpureCorrRet','CSTurnpureCorrRetSharp','IdeaReverser5d','Min5LastHourMFI5d','Min5LastHalfHourRVI','Min5LastHalfHourVolStd5d',
#'Min5LastHalfHourVR','Min5LastHalfHourVR5dCut','Min5LastHalfHourVRSI10d','Min5LastHourElder20d','Min5LastHourElder5dSharp',
#'Min5LongShortRatioCut5d','PriceBiasDividStd60','PriceBiasZscore60','ReCorr20','RetCorrTurnDelayPure']
#factor_list = sorted(list(set(factor_list)-set(multiprocess_factor)))
#np.random.seed(1993)
#np.random.shuffle(factor_list)
#factor_dict_new = {}
#num = 20
#count = int(len(factor_list)/num)+1
#for i in range(num):
#    factor_dict_new[i] = sorted(list(set(factor_list[i*count:(i+1)*count])-set(['MinIdx300Corr','MinIdx500Corr'])))
#pd.to_pickle(factor_dict_new,aimr_factor_dict_path)
#multi_factors_dict = {}
#multi_factors_dict[0] = multiprocess_factor[:8]
#multi_factors_dict[1] = multiprocess_factor[8:11]
#multi_factors_dict[2] = multiprocess_factor[11:]
#pd.to_pickle(multi_factors_dict,multi_factor_dict_path)
factor_dict_new = pd.read_pickle(aimr_factor_dict_path)
print(list(factor_dict_new.keys()))
print('update:',today)
params = {
    "parallel_list": list(factor_dict_new.keys()),   
    "tag":"xquant",
    "cpu":8,
    "gpu":0,
    "memory":100000
}

AIMR.runTasks('update_factor/aimr_exec.py',json.dumps(params))