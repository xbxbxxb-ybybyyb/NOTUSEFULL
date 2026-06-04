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
import sys
sys.path.insert(0,'ModelMonitorOrig_469/')
from config_path import *
import shutil
from xquant.xqutils.helper import link
lm = link.LinkMessage()


import datetime
today = datetime.date.today()
today = str(today.year)+str(today.month).zfill(2)+str(today.day).zfill(2)
#today = '20210720' #@

retrain_flag = False#True #pm train yestaday
predict_label = True#not retrain_flag #nigh predict today

from xquant.factordata import FactorData
s = FactorData()
date_begin = '20200101'
result1 = s.tradingday(date_begin, today)
today_date = '20210927'#result1[-1]

print('@',today_date)
lookback_period = 240

factor_list = pd.read_pickle(data_root_path+'/AlphaDataCenter/Sample/factor_list.pkl')

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

    for model in [Lr_Model()]:
        t = time.time()
        if not os.path.exists(model._model_path):
            os.mkdir(model._model_path)
        model.get_model(retrain_samples.copy(), factor_list)
        print(model._modelname +' re-train finished' , time.time() - t)



    ######################### 1d label models
    gap_period = 5
    model_retrain_date = all_trading_days[-lookback_period- gap_period:-gap_period-1]
    retrain_samples = training_sample[training_sample['date'].isin(model_retrain_date)]

    for model in [XgboostReg_Model(), DeepFM_Model()]:
        t = time.time()
        if not os.path.exists(model._model_path):
            os.mkdir(model._model_path)
        model.get_model(retrain_samples.copy(), factor_list)
        print(model._modelname +' re-train finished' , time.time() - t)
        
        # model_record_path = model._model_path + '/update_record/%s/' % today_date
   


    #####################################################################################

if predict_label:
    sample_daily = pd.read_pickle(data_root_path+'/AlphaDataCenter/Sample/NormSample/'+ today_date +'.pkl')
    names = ['lr','xg','fm']
    count=0
    for model in [Lr_Model(), XgboostReg_Model(),  DeepFM_Model()]:
        t = time.time()
        pred = model.label_predict(sample_daily, factor_list)
        if not os.path.exists(model._prediction_path):
            os.mkdir(model._prediction_path)
        pred.to_csv(model._prediction_path + today_date +'.csv')
        
        act_stat = pred.describe()

        act_stat = round(act_stat,2)
        act_stat = act_stat.astype('str')
        act_stat_ = act_stat.to_dict()

        act_dict_str = ''
        for key, value in act_stat_.items():
            act_dict_str=act_dict_str+key+':'+value+', '        
        lm.sendMessage("Vwap,%s,  %s" % (names[count],act_dict_str))
        
        print(model._modelname +'   predict finished' , today_date, time.time() - t)
        count+=1
