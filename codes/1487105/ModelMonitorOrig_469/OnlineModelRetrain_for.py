import pandas as pd
import numpy as np
import os
import time
import warnings
warnings.filterwarnings("ignore")
from XgboostReg_Model import *
from Lr_Model import *
from Logistic_Model import *
from DeepFM_Model import *
import sys
sys.path.insert(0,'ModelMonitorOrig_469/')
from config_path import *

close = pd.read_pickle(data_root_path+'/AlphaDataCenter/Basic/daily/close.pkl')
dates = list(close.index)
dates = [str(i.year)+str(i.month).zfill(2)+str(i.day).zfill(2) for i in dates]

date_start = '20200117'
date_end = '20200123'
step = 5
count = 0
lookback_period = 240
# factor_list = (sorted([e[:-4] for e in os.listdir(data_root_path+'/AlphaDataCenter/NeutralizedFactors/IndustrySizeNeutralized/')]))
factor_list = pd.read_pickle(data_root_path+'/AlphaDataCenter/Sample/factor_list.pkl')
dates = [i for i in dates if i>=date_start and i<=date_end]

for today_date in dates:
    
    if count % step == 0:
        retrain_flag = True
    else:
        retrain_flag = False            
    print('###########%s %s############' % (today_date,str(retrain_flag)))

    if retrain_flag == True:
        all_trading_days = sorted([e[:-4] for e in os.listdir(data_root_path+'/AlphaDataCenter/Sample/NormSample/')])
        all_trading_days = [e for e in all_trading_days if e <= today_date]
        sample_required_dates = all_trading_days[-lookback_period-20 : ]

        sample_list = []
        for day in sample_required_dates:
            sample_list.append(pd.read_pickle(data_root_path+'/AlphaDataCenter/Sample/NormSample/'+ day +'.pkl'))
        training_sample = pd.concat(sample_list)


        print('......................')
        # ######################### 5d label models
        gap_period = 5
        model_retrain_date = all_trading_days[-lookback_period- gap_period-1 :-gap_period-1]
        retrain_samples = training_sample[training_sample['date'].isin(model_retrain_date)]

        for model in [Lr_Model()]:#, Logistic_Model()]:XgboostReg_Model(), 
            t = time.time()
            if not os.path.exists(model._model_path):
                os.mkdir(model._model_path)
            model.get_model(retrain_samples.copy(), factor_list)
            print(model._modelname +' re-train finished' , time.time() - t)



        ######################### 1d label models
        gap_period = 1
        model_retrain_date = all_trading_days[-lookback_period- gap_period:-gap_period-1]
        retrain_samples = training_sample[training_sample['date'].isin(model_retrain_date)]

        for model in [XgboostReg_Model()]:#, DeepFM_Model()
            t = time.time()
            if not os.path.exists(model._model_path):
                os.mkdir(model._model_path)
            model.get_model(retrain_samples.copy(), factor_list)
            print(model._modelname +' re-train finished' , time.time() - t)

        #####################################################################################


    sample_daily = pd.read_pickle(data_root_path+'/AlphaDataCenter/Sample/NormSample/'+ today_date +'.pkl')

    for model in [Lr_Model(), XgboostReg_Model()]:#  
        t = time.time()
        pred = model.label_predict(sample_daily, factor_list)
        if not os.path.exists(model._prediction_path):
            os.mkdir(model._prediction_path)
        pred.to_csv(model._prediction_path + today_date +'.csv')
        print(model._modelname +'   predict finished' , today_date, time.time() - t)

    count+=1