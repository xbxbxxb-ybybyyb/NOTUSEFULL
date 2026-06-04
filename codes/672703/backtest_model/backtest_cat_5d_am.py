import pandas as pd
import numpy as np
import os
import time
import sys
sys.path.insert(0,'backtest_model/model/')
import warnings
warnings.filterwarnings("ignore")
from CatboostMultiClass_Model_R5d import *
import datetime
from xquant.factordata import FactorData


factorData = FactorData()
train_start = '20170901'
today = datetime.date.today().strftime('%Y%m%d')
dates = factorData.tradingday('20111102',today)
date_start = '20200101'
date_end = '20200515'
type_r = 'am'
count = 0
oos = 3
interval = 5
step = 5
lookback_period = 240
retrain_flag = True  
root_model_path = '/data/user/013546/AlphaDataCenter/Models/'+type_r+'/'
root_predict_path = '/data/user/013546/AlphaDataCenter/DailyPrediction/'+type_r+'/'
model_dict = {'CatboostMultiClass_Model_R5d':('bin_0930_1129_re_5d',5)}
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
    valid_dates = factorData.tradingday('20111102',today_date)
    check_dates = valid_dates[-oos-1-interval:-oos-1]


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
            params['weight'] = [-4, -3, 0, 3, 4, 4]
            params['time'] = type_r
            params['sample_path'] = path_sample
            params['check_dates'] = check_dates
            execstr = k+'(params)'
            print(execstr)
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
        params['weight'] = [-4, -3, 0, 3, 4, 4]
        params['time'] = type_r
        params['sample_path'] = path_sample
        params['check_dates'] = check_dates
        execstr = k+'(params)'
        model = eval(execstr)
        # model.revise_model_name(date_start+date_end)        
        t = time.time()
        pred = model.label_predict(sample_daily, factor_list)
        if not os.path.exists(model._prediction_path):
            os.makedirs(model._prediction_path)
        pred.to_csv(model._prediction_path + today_date +'.csv')
        print(model._modelname +'   predict finished' , today_date, time.time() - t)
