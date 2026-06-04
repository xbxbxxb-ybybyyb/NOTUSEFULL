import pandas as pd
import numpy as np
import os
import time
import warnings
warnings.filterwarnings("ignore")
from XgboostReg_Model_GPU import *
from Lr_Model import *
# from Logistic_Model import *
from DeepFM_Model import *
import shutil
from xquant.xqutils.helper import link
lm = link.LinkMessage()


import datetime
close = pd.read_pickle('/data/group/800469/AlphaDataCenter/Basic/daily/close.pkl')
dates = list(close.index)
dates = [str(i.year)+str(i.month).zfill(2)+str(i.day).zfill(2) for i in dates]
#XgboostRegression_2020010120200820_Label_vwap_re_5d_1_TS
#date_start = '20200101'
date_start = '20200101'
date_end = '20200910'
step = 1
lookback_period = 240
gap_set = 5
factor_list = pd.read_pickle('/data/group/800469/AlphaDataCenter/Sample/factor_list.pkl')
dates = [i for i in dates if i>=date_start and i<=date_end]
# for today_date in dates:
label_test = '_TeamRep_2020'
count = 0
dates_train=[]
for i in range(1,len(dates)+1):
    ds = dates[i-1]    
    de = dates[i]
    today_date = ds
    next_month = pd.to_datetime(ds).replace(day=28) + datetime.timedelta(days=4)  # this will never fail
    last_day = next_month - datetime.timedelta(days=next_month.day)
    last_day= last_day.strftime('%Y%m%d')   
    # find gab, if gab_days>1 , or not the last day between months
    if pd.to_datetime(de).day - pd.to_datetime(ds).day > 1 or i == 1 \
    or ((pd.to_datetime(de).month - pd.to_datetime(ds).month >= 1) & (ds<last_day)):
        count+=1
        if count % step == 0:
            dates_train.append(ds)
            retrain_flag = True        
        else:
            retrain_flag = False        
        if len(dates_train)>1:
            print(ds,int(ds[-2:])-int(dates_train[-2][-2:]))
        else:
            print(ds)
    else:
        retrain_flag = False                           
    print('###########%s %s ############' % (today_date,str(retrain_flag)))    

    if retrain_flag == True:
        all_trading_days = sorted([e[:-4] for e in os.listdir('/data/group/800469/AlphaDataCenter/Sample/NormSample/')])
        all_trading_days = [e for e in all_trading_days if e <= today_date]
        sample_required_dates = all_trading_days[-lookback_period-20 : ]

        sample_list = []
        for day in sample_required_dates:
            sample_list.append(pd.read_pickle('/data/group/800469/AlphaDataCenter/Sample/NormSample/'+ day +'.pkl'))
        training_sample = pd.concat(sample_list)


        print('......................')
        # ######################### 5d label models
        gap_period = 5
        model_retrain_date = all_trading_days[-lookback_period- gap_period-1 :-gap_period-1]
        retrain_samples = training_sample[training_sample['date'].isin(model_retrain_date)]

        for model in [Lr_Model()]:
            model.revise_model_name(label_test)
            print(model._model_path)
            print(model._prediction_path)
            t = time.time()
            if not os.path.exists(model._model_path):
                os.makedirs(model._model_path)
            model.get_model(retrain_samples.copy(), factor_list)
            print(model._modelname +' re-train finished' , time.time() - t)



        ######################### 1d label models
        gap_period = 5
        model_retrain_date = all_trading_days[-lookback_period- gap_period:-gap_period-1]
        retrain_samples = training_sample[training_sample['date'].isin(model_retrain_date)]

        for model in [XgboostReg_Model(), DeepFM_Model()]:
            model.revise_model_name(label_test)
            print(model._model_path)
            print(model._prediction_path)
            t = time.time()
            if not os.path.exists(model._model_path):
                os.makedirs(model._model_path)
            model.get_model(retrain_samples.copy(), factor_list)
            print(model._modelname +' re-train finished' , time.time() - t)
            
            # model_record_path = model._model_path + '/update_record/%s/' % today_date
       


        #####################################################################################

    if True:
        sample_daily = pd.read_pickle('/data/group/800469/AlphaDataCenter/Sample/NormSample/'+ today_date +'.pkl')
        names = ['lr','xg','fm']
        for model in [Lr_Model(), XgboostReg_Model(),  DeepFM_Model()]:
            model.revise_model_name(label_test)
            print(model._model_path)
            print(model._prediction_path)
            t = time.time()
            pred = model.label_predict(sample_daily, factor_list)
            if not os.path.exists(model._prediction_path):
                os.makedirs(model._prediction_path)
            pred.to_csv(model._prediction_path + today_date +'.csv')
        