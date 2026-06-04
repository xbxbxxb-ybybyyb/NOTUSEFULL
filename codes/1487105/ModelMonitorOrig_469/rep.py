import pandas as pd
import numpy as np
import os
import time
import warnings
warnings.filterwarnings("ignore")
from XgboostReg_Model_GPU import *
from Lr_Model import *
from Logistic_Model import *
from DeepFM_Model import *

close = pd.read_pickle('/data/group/800469/AlphaDataCenter/Basic/daily/close.pkl')
dates = list(close.index)
dates = [str(i.year)+str(i.month).zfill(2)+str(i.day).zfill(2) for i in dates]

date_start = '20201001'
date_end = '20201016'
step = 1
count = 0
lookback_period = 240
# factor_list = (sorted([e[:-4] for e in os.listdir('/data/group/800469/AlphaDataCenter/NeutralizedFactors/IndustrySizeNeutralized/')]))
factor_list = pd.read_pickle('/data/group/800469/AlphaDataCenter/Sample/factor_list.pkl')
dates = [i for i in dates if i>=date_start and i<=date_end]
dates_train=[]
for i in range(1,len(dates)+1):
    ds = dates[i-1]    
    # if ds in ['20200103']:
    #     continue
    de = dates[i]
    today_date = ds
    
    year = today_date[:4]
    if year>='2020':
        step = 1
    print(year,step)
    # find gab, if gab_days>1 , or not the last day between months
    if i==1 or (pd.to_datetime(de) - pd.to_datetime(ds)).days > 1:
        count+=1
        if step == 1:
            delta = 0
        else:
            delta = 1
        if count % step == delta:
            dates_train.append(ds)
            retrain_flag = True        
        else:
            retrain_flag = False
    else:
        retrain_flag = False                                   
    print('###########%s %s############ %s %s ' % (today_date,str(retrain_flag),str(count),str(step)))


    if retrain_flag == True:
        all_trading_days = sorted([e[:-4] for e in os.listdir('/data/group/800469/AlphaDataCenter/Sample/NormSample/')])
        all_trading_days = [e for e in all_trading_days if e <= today_date]
        sample_required_dates = all_trading_days[-lookback_period-20 : ]

        sample_list = []
        for day in sample_required_dates:
            sample_list.append(pd.read_pickle('/data/group/800469/AlphaDataCenter/Sample/NormSample/'+ day +'.pkl'))
        training_sample = pd.concat(sample_list)


        print('......................')

        ######################### 5d label models
        gap_period = 5
        model_retrain_date = all_trading_days[-lookback_period-gap_period-1 : -gap_period-1]
        retrain_samples = training_sample[training_sample['date'].isin(model_retrain_date)]

        for model in [Lr_Model()]:#, DeepFM_Model()
      
            model.revise_model_name('_repp_')
            print(model._model_path)
            print(model._prediction_path)              
            t = time.time()
            if not os.path.exists(model._model_path):
                os.makedirs(model._model_path)
            model.get_model(retrain_samples.copy(), factor_list)
            print(model._modelname +' re-train finished' , time.time() - t)

        #####################################################################################


    sample_daily = pd.read_pickle('/data/group/800469/AlphaDataCenter/Sample/NormSample/'+ today_date +'.pkl')

    for model in [Lr_Model()]:#  
        model.revise_model_name('_repp_')
        print(model._model_path)
        print(model._prediction_path)
        t = time.time()
        pred = model.label_predict(sample_daily, factor_list)
        if not os.path.exists(model._prediction_path):
            os.makedirs(model._prediction_path)
        pred.to_csv(model._prediction_path + today_date +'.csv')
        print(model._modelname +'   predict finished' , today_date, time.time() - t)
