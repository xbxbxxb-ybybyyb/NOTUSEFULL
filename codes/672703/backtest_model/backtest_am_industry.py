import pandas as pd
import numpy as np
import os
import time
import sys
import warnings
warnings.filterwarnings("ignore")
sys.path.insert(0,'backtest_model/model/')
from XgboostGPU_Model import *
close = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/close.pkl')
dates = list(close.index)
dates = [str(i.year)+str(i.month).zfill(2)+str(i.day).zfill(2) for i in dates]
train_start = '20180101'
date_start = '20190701'
date_end = '20191231'
step = 20
count = 0
lookback_period = 240
t = 'am'
w = [1/3,1/3,1/3]
time_w = '0930_1129'
need_combine = [time_w+'_re_1d',time_w+'_re_3d',time_w+'_re_5d']
com_col = time_w+'_re_com_nowinsard_13mdp'
root_model_path = '/data/user/013546/AlphaDataCenter/Models/'+t+'/'
root_predict_path = '/data/user/013546/AlphaDataCenter/DailyPrediction/'+t+'/'
label_path_sample = '/data/group/800020/AlphaExperiment/Factor/Sample/NormSample/'
need_label = com_col
need_label = 'industry_0930_1129_combine'
model_dict = {'XgboostReg_Model':(need_label,5)}
factor_list = pd.read_pickle('/data/group/800020/AlphaDataCenter/Sample/factor_list.pkl')
path_sample = '/data/group/800020/AlphaDataCenter/Sample/NormSample/'#
dates = [i for i in dates if i>=date_start and i<=date_end]

for today_date in dates:
    
    if count % step == 0:
        retrain_flag = True
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
            if day<train_start:
                continue
            df = pd.read_pickle(path_sample+ day +'.pkl')[['date','stock']+factor_list]
            label = pd.read_pickle(label_path_sample + day +'.pkl')
            df = df.merge(label,on=['date','stock'],how='left')
            sample_list.append(df)
        training_sample = pd.concat(sample_list)
        training_sample[com_col] = (training_sample[need_combine]*w).sum(axis=1)
        # training_sample = training_sample.merge(label_sample[[need_label]],left_on=['date','stock'],right_index=True,how='left')
        # training_sample[np.isinf[training_sample]] = np.nan
        # training_sample.fillna(0,inplace=True)

        print('......................')
        

        for k,v in model_dict.items():
            gap_period = v[1]
            model_retrain_date = all_trading_days[-lookback_period- gap_period-1 :-gap_period-1]
            params={}
            params['label_name'] = v[0]
            params['modelname'] = k+'_'+params['label_name']
            params['model_path'] = root_model_path + params['modelname']+'/' +model_retrain_date[-1]+'/'
            if not os.path.exists(params['model_path']):
                os.makedirs(params['model_path'])
            params['prediction_path'] = root_predict_path + params['modelname']+'/'
            execstr = k+'(params)'
            model = eval(execstr)
            

            retrain_samples = training_sample[training_sample['date'].isin(model_retrain_date)]
            # model.revise_model_name(date_start+date_end)
            t = time.time()
            if not os.path.exists(model._model_path):
                os.makedirs(model._model_path)
            model.get_model(retrain_samples.copy(), factor_list)
            print(model._modelname +' re-train finished' , time.time() - t)


        #####################################################################################

    
    sample_daily = pd.read_pickle(path_sample+ today_date +'.pkl')

    for k,v in model_dict.items():#
        gap_period = v[1]
        model_retrain_date = all_trading_days[-lookback_period- gap_period-1 :-gap_period-1]
        params={}
        params['label_name'] = v[0]
        params['modelname'] = k+'_'+params['label_name']
        params['model_path'] = root_model_path + params['modelname']+'/'+model_retrain_date[-1]+'/'
        params['prediction_path'] = root_predict_path + params['modelname']+'/'
        execstr = k+'(params)'
        model = eval(execstr)
        # model.revise_model_name(date_start+date_end)        
        t = time.time()
        pred = model.label_predict(sample_daily, factor_list)
        if not os.path.exists(model._prediction_path):
            os.makedirs(model._prediction_path)
        pred.to_csv(model._prediction_path + today_date +'.csv')
        print(model._modelname +'   predict finished' , today_date, time.time() - t)
