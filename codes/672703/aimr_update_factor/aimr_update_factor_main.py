from xquant.compute.aimr import AIMR
import json
import pandas as pd
import datetime
from xquant.factordata import FactorData
s = FactorData()
print("start")
start_end_date = {}
today = datetime.date.today().strftime('%Y%m%d')
today = s.tradingday(today,-1)[0]
start_end_date['start_date'] = today
start_end_date['end_date'] = today
pd.to_pickle(start_end_date,'/data/group/800020/AlphaDataCenter/Transit/update_factor/start_end_date.pkl')
import numpy as np
import pandas as pd
from itertools import chain
factor_dict = pd.read_pickle('/data/group/800020/AlphaDataCenter/Transit/update_factor/factor_dict.pkl')
factor_list = list(chain.from_iterable(factor_dict.values()))
multiprocess_factor = ['CSTurnpureCorrRet','CSTurnpureCorrRetSharp','IdeaReverser5d','Min5LastHourMFI5d','Min5LastHalfHourRVI','Min5LastHalfHourVolStd5d',
'Min5LastHalfHourVR','Min5LastHalfHourVR5dCut','Min5LastHalfHourVRSI10d','Min5LastHourElder20d','Min5LastHourElder5dSharp',
'Min5LongShortRatioCut5d','PriceBiasDividStd60','PriceBiasZscore60','ReCorr20','RetCorrTurnDelayPure']
factor_list = sorted(list(set(factor_list)-set(multiprocess_factor)))
np.random.seed(1993)
np.random.shuffle(factor_list)
factor_dict_new = {}
num = 20
count = int(len(factor_list)/num)+1
for i in range(num):
    factor_dict_new[i] = sorted(list(set(factor_list[i*count:(i+1)*count])-set(['MinIdx300Corr','MinIdx500Corr'])))
pd.to_pickle(factor_dict_new,'/data/group/800020/AlphaDataCenter/Transit/update_factor/aimr_factor_dict.pkl')
params = {
    "parallel_list": list(factor_dict_new.keys()),   
    "tag":"xquant",
    "cpu":12,
    "gpu":0,
    "memory":100000
}

AIMR.runTasks('aimr_update_factor/aimr_update_factor.py',json.dumps(params))