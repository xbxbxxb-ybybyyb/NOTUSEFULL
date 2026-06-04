import pandas as pd
import numpy as np
import os
import time
import warnings
warnings.filterwarnings("ignore")
from Pm_XgboostReg_Model import *
from Pm_Lr_Model import *
from Pm_DeepFM_Model import *
from Pm_CatboostMultiCalss_Model import *
import datetime
today = datetime.date.today()
today = str(today.year)+str(today.month).zfill(2)+str(today.day).zfill(2)

print(today)
today_date = today#

factor_list = pd.read_pickle('/data/group/800020/AlphaDataCenter/Sample/factor_list.pkl')
hfactor_list =  pd.read_pickle('/data/group/800020/AlphaDataCenter/HFSample/hfactor_list.pkl')
hfactors = [i for i in hfactor_list if i not in factor_list]
hfactors.sort()
factor_list.extend(hfactors)
print('@ factor number:',len(factor_list))
path_sample = '/data/group/800020/AlphaDataCenter/HFSample/NormSample/'
all_trading_days = sorted([e[:-4] for e in os.listdir(path_sample)])
all_trading_days = [e for e in all_trading_days if e <= today_date]
lookback_period = 300
sample_required_dates = all_trading_days[-lookback_period-20 : ]
retrain_flag = False
def update_model(sample,model_list,today_date,lookback_period = 300,gap_period = 1):
    print('......................')
    
    model_retrain_date = all_trading_days[-lookback_period- gap_period-1 :-gap_period-1]
    retrain_samples = training_sample[training_sample['date'].isin(model_retrain_date)]

    for model in model_list:
        t = time.time()
        if not os.path.exists(model._model_path):
            os.makedirs(model._model_path)
        model.get_model(retrain_samples.copy(), factor_list)
        print(model._modelname +' re-train finished' , time.time() - t)
    #####################################################################################

if retrain_flag:
    training_sample = []
    for day in sample_required_dates:
        training_sample.append(pd.read_pickle(path_sample+ day +'.pkl'))
    training_sample = pd.concat(training_sample)
    update_model(training_sample,[XgboostReg_Model(),DeepFM_Model()],today_date,lookback_period = 240,gap_period = 5)
    update_model(training_sample,[Lr_model],today_date,lookback_period = 240,gap_period = 1)
    update_model(training_sample,[CatboostMultiCalss_Model],today_date,lookback_period = 300,gap_period = 1)
sample_daily = pd.read_pickle(path_sample+ today_date +'.pkl')
for model in [Lr_Model(), XgboostReg_Model(), DeepFM_Model(),CatboostMultiCalss_Model()]:#
         
    t = time.time()
    pred = model.label_predict(sample_daily, factor_list)
    if not os.path.exists(model._prediction_path):
        os.makedirs(model._prediction_path)
    pred.to_csv(model._prediction_path + today_date +'.csv')
    print(model._modelname +'   predict finished' , today_date, time.time() - t)


    