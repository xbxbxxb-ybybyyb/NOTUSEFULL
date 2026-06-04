import pandas as pd
import numpy as np
import os
import time
import sys
import warnings
warnings.filterwarnings("ignore")
sys.path.insert(0,'backtest_model/model/')
from XgboostReg_Model import *
from Lr_Model import *
from DeepFM_Model import *
from CatboostMultiClass_Model import *

close = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/close.pkl')
dates = list(close.index)
dates = [str(i.year)+str(i.month).zfill(2)+str(i.day).zfill(2) for i in dates]
train_start = '20170901'
date_start = '20190101'
date_end = '20200226'
t = 'pm'
step = 20
count = 0
lookback_period = 300
root_model_path = '/data/user/013546/AlphaDataCenter/Models/'+t+'/'+'chenz_factors/'
root_predict_path = '/data/user/013546/AlphaDataCenter/DailyPrediction/'+t+'/'+'chenz_factors/'
myfile_path = '/data/group/800020/AlphaExperiment/Test/'
transaction_time = '1300_1459_re_1d'
model_dict={'XgboostReg_Model':(transaction_time,1),
            'DeepFM_Model':(transaction_time,1),
            'CatboostMultiClass_Model':('bin_'+transaction_time,1),
            'Lr_Model':('industry_1300_1459_re_5d',5)}
model_dict = {'CatboostMultiClass_Model':('bin_'+transaction_time,1)}
factor_list = pd.read_pickle('/data/group/800020/AlphaDataCenter/HFSample/hfactor_list.pkl')
factor_list1= pd.read_excel(myfile_path + 'myfactor.xlsx',header=None).fillna(0)
factor_list1= factor_list1.values.reshape((1,factor_list1.size))
factor_daily_all = factor_list1[factor_list1!=0].astype('str').tolist()
factor_daily_cut = pd.read_excel(myfile_path+'daily_10_cut.xlsx',header=None)[0].tolist()
factor_daily = list(set(factor_daily_all) - set(factor_daily_cut))

factor_13 = pd.read_excel(myfile_path + 'factor_13_new.xlsx',header=None)[0].tolist()
factor_13_list = list(set(factor_13))

factor_list_all = list(set(factor_13_list)) + list(set(factor_daily))
factor_list = list(set(factor_list_all)&set(factor_list))
path_sample = '/data/group/800020/AlphaDataCenter/HFSample/NormSample/'#
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
            df = pd.read_pickle(path_sample+ day +'.pkl')
            sample_list.append(df)
        training_sample = pd.concat(sample_list)
        # training_sample[np.isinf[training_sample]] = np.nan
        # training_sample.fillna(0,inplace=True)

        print('......................')
        

        for k,v in model_dict.items():
            params={}
            params['label_name'] = v[0]
            params['modelname'] = k+'_'+params['label_name']
            params['model_path'] = root_model_path + params['modelname']+'/'
            params['prediction_path'] = root_predict_path + params['modelname']+'/'
            params['weight'] = [-6, 0, 0, 0, 2, 10]
            execstr = k+'(params)'
            model = eval(execstr)
            
            gap_period = v[1]
            model_retrain_date = all_trading_days[-lookback_period- gap_period-1 :-gap_period-1]
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
        params={}
        params['label_name'] = v[0]
        params['modelname'] = k+'_'+params['label_name']
        params['model_path'] = root_model_path + params['modelname']+'/'
        params['prediction_path'] = root_predict_path + params['modelname']+'/'
        params['weight'] = [-6, 0, 0, 0, 2, 10]
        execstr = k+'(params)'
        model = eval(execstr)
        # model.revise_model_name(date_start+date_end)        
        t = time.time()
        pred = model.label_predict(sample_daily, factor_list)
        if not os.path.exists(model._prediction_path):
            os.makedirs(model._prediction_path)
        pred.to_csv(model._prediction_path + today_date +'.csv')
        print(model._modelname +'   predict finished' , today_date, time.time() - t)
