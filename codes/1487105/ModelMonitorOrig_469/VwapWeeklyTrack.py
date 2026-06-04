import pandas as pd
import numpy as np
import os
import time
import warnings
import datetime
warnings.filterwarnings("ignore")
#from XgboostReg_Model import *
from XgboostReg_Model import *
from Lr_Model import *
from DeepFM_Model import *


close = pd.read_pickle('/data/group/800469/AlphaDataCenter/Basic/daily/close.pkl')
dates = list(close.index)
dates = [str(i.year)+str(i.month).zfill(2)+str(i.day).zfill(2) for i in dates]

date_start = '20200706'
date_end = '20200706'
step = 4
count = 0
lookback_period = 240
# factor_list = (sorted([e[:-4] for e in os.listdir('/data/group/800469/AlphaDataCenter/NeutralizedFactors/IndustrySizeNeutralized/')]))
factor_list = pd.read_pickle('/data/group/800469/AlphaDataCenter/Sample/factor_list.pkl')
path_sample = '/data/group/800469/AlphaDataCenter/Sample/NormSample/'#  
dates = [i for i in dates if i>=date_start and i<=date_end]
dates.sort()
dates_train = []
label_test = '_WeelkyTrain_%s_' % date_start
for i in range(1,len(dates)):
    ds = dates[i-1]    
    de = dates[i]
    today_date = ds
    next_month = pd.to_datetime(ds).replace(day=28) + datetime.timedelta(days=4)  # this will never fail
    last_day = next_month - datetime.timedelta(days=next_month.day)
    last_day= last_day.strftime('%Y%m%d')   
    # find gab, if gab_days>1 , or not the last day between months
    if pd.to_datetime(de).day - pd.to_datetime(ds).day > 1 or i == 1 \
    or ((pd.to_datetime(de).month - pd.to_datetime(ds).month >= 1) & (ds<last_day)):
        retrain_flag = True
        dates_train.append(ds)
        if len(dates_train)>1:
            print(ds,int(ds[-2:])-int(dates_train[-2][-2:]))
        else:
            print(ds)
    else:
        retrain_flag = False

    print('###########%s %s############' % (today_date,str(retrain_flag)))
    count+=1


    if retrain_flag == True:
        all_trading_days = sorted([e[:-4] for e in os.listdir(path_sample)])
        all_trading_days = [e for e in all_trading_days if e <= today_date]
        sample_required_dates = all_trading_days[-lookback_period-20 : ]

        sample_list = []
        for day in sample_required_dates:
            sample_list.append(pd.read_pickle(path_sample+ day +'.pkl'))
        training_sample = pd.concat(sample_list)
        # training_sample[np.isinf[training_sample]] = np.nan
        # training_sample.fillna(0,inplace=True)

        print('......................')
        # ######################### 5d label models
        gap_period = 5
        model_retrain_date = all_trading_days[-lookback_period- gap_period-1 :-gap_period-1]
        retrain_samples = training_sample[training_sample['date'].isin(model_retrain_date)]

        for model in [Lr_Model(),XgboostReg_Model(), DeepFM_Model()]:
            model.revise_model_name(label_test+today_date)
            t = time.time()
            if not os.path.exists(model._model_path):
                os.makedirs(model._model_path)
            model.get_model(retrain_samples.copy(), factor_list)
            print(model._modelname +' re-train finished' , time.time() - t)



#        # ######################### 1d label models
#        gap_period = 5
#        model_retrain_date = all_trading_days[-lookback_period- gap_period:-gap_period-1]
#        retrain_samples = training_sample[training_sample['date'].isin(model_retrain_date)]

#        for model in [DeepFM_Model(),XgboostReg_Model()]:#XgboostReg_Model(), 
#            model.revise_model_name(label_test+today_date)
#            t = time.time()
#            if not os.path.exists(model._model_path):
#                os.makedirs(model._model_path)
#            model.get_model(retrain_samples.copy(), factor_list)
#            print(model._modelname +' re-train finished' , time.time() - t)

        #####################################################################################


    sample_daily = pd.read_pickle(path_sample+ today_date +'.pkl')

    for model in [Lr_Model(),XgboostReg_Model(), DeepFM_Model()]:#
        # model.revise_model_name('_update_test_'+dates_train[-1])  
        # model.revise_prediction_path('_updateGap5')
        model.revise_model_name(label_test+dates_train[-min(1,len(dates_train))])  
        # model.revise_prediction_path('_updateGap5')              
        t = time.time()
        pred = model.label_predict(sample_daily, factor_list)
        if not os.path.exists(model._prediction_path):
            os.makedirs(model._prediction_path)
        pred.to_csv(model._prediction_path + today_date +'.csv')
        
        
        print(model._modelname +'   predict finished' , today_date, time.time() - t)
