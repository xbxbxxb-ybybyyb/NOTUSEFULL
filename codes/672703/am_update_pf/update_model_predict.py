import pandas as pd
import numpy as np
import os
import time
import warnings
warnings.filterwarnings("ignore")
import sys
sys.path.insert(0,'am_update_pf/model/')
from Pm_XgboostReg_Model import *
from Pm_Lr_Model import *
from Pm_DeepFM_Model import *

# import datetime
# today = datetime.date.today()
# today = str(today.year)+str(today.month).zfill(2)+str(today.day).zfill(2)

def run(today):
    print('#################predict############')
    retrain_flag = False
    today_date = today
    lookback_period = 240
    # factor_list = (sorted([e[:-4] for e in os.listdir('/data/group/800020/AlphaDataCenter/NeutralizedFactors/IndustrySizeNeutralized/')]))
    # factor_list_hf = (sorted([e[:-4] for e in os.listdir\
    # ('/data/group/800020/AlphaDataCenter/NeutralizedHFactors/IndustrySizeNeutralized//')]))
    # factor_list.extend(factor_list_hf)
    factor_list = pd.read_pickle('/data/group/800020/AlphaDataCenter/Sample/factor_list.pkl')
    hfactor_list =  pd.read_pickle('/data/group/800020/AlphaDataCenter/HFSample/hfactor_list.pkl')
    hfactors = [i for i in hfactor_list if i not in factor_list]
    hfactors.sort()
    factor_list.extend(hfactors)    
    
    print('@ factor number:',len(factor_list))

    if retrain_flag == True:
        all_trading_days = sorted([e[:-4] for e in os.listdir('/data/group/800020/AlphaDataCenter/HFSample/NormSample/')])
        all_trading_days = [e for e in all_trading_days if e <= today_date]
        sample_required_dates = all_trading_days[-lookback_period-20 : ]

        sample_list = []
        for day in sample_required_dates:
            sample_list.append(pd.read_pickle('/data/group/800020/AlphaDataCenter/HFSample/NormSample/'+ day +'.pkl'))
        training_sample = pd.concat(sample_list)


        print('......................')
        # ######################### 5d label models
        gap_period = 5
        model_retrain_date = all_trading_days[-lookback_period- gap_period-1 :-gap_period-1]
        retrain_samples = training_sample[training_sample['date'].isin(model_retrain_date)]

        for model in [Lr_Model()]:
            t = time.time()
            if not os.path.exists(model._model_path):
                os.mkdir(model._model_path)
            model.get_model(retrain_samples.copy(), factor_list)
            print(model._modelname +' re-train finished' , time.time() - t)



        ######################### 1d label models
        gap_period = 1
        model_retrain_date = all_trading_days[-lookback_period- gap_period:-gap_period-1]
        retrain_samples = training_sample[training_sample['date'].isin(model_retrain_date)]

        for model in [XgboostReg_Model(), DeepFM_Model()]:
            t = time.time()
            if not os.path.exists(model._model_path):
                os.mkdir(model._model_path)
            model.get_model(retrain_samples.copy(), factor_list)
            print(model._modelname +' re-train finished' , time.time() - t)





        #####################################################################################


    sample_daily = pd.read_pickle('/data/group/800020/AlphaDataCenter/HFSample/NormSample/'+ today_date +'.pkl')

    for model in [Lr_Model(),  XgboostReg_Model(),  DeepFM_Model()]:
        t = time.time()
        pred = model.label_predict(sample_daily, factor_list)
        if not os.path.exists(model._prediction_path):
            os.mkdir(model._prediction_path)
        pred.to_csv(model._prediction_path + today_date +'.csv')
        print(model._modelname +'   predict finished' , today_date, time.time() - t)
