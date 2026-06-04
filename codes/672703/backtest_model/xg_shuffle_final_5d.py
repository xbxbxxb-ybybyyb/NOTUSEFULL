import pandas as pd
import numpy as np
import os
import time
import sys
import warnings
warnings.filterwarnings("ignore")
import numpy as np
import xgboost as xgb
import pickle
import pandas as pd

class XgboostReg_Model():
    
    def __init__(self,params):

        self._label_name = params['label_name']
        self._random_seed = 1990
        self._modelname =  params['modelname']
        self._model_path = params['model_path']
        self._prediction_path = params['prediction_path']

    def revise_model_path(self, path):
        self._model_path = path
    
    def revise_label(self, label):
        self._label_name = label

    def revise_random_seed(self, seed):
        self._random_seed = seed

    def get_model(self, sample, factor_list):
        dates = pd.to_datetime(sample['date'].values).unique().tolist()
        for j in range(4):
            np.random.seed(self._random_seed)
            np.random.shuffle(dates)
            train_dates =dates[:200]
            validation_dates = dates[200:]
            validation_set = sample[sample['date'].isin(validation_dates)].copy()  
            validation_x = validation_set[factor_list]
            validation_y = validation_set[self._label_name ]
            train_set = sample[sample['date'].isin(train_dates)].copy()
            train_x = train_set[factor_list]
            train_y = train_set[self._label_name]
            print(j)
            print(len(train_dates),len(validation_dates))
            print(len(train_x),len(validation_x))
            xgb_model = xgb.XGBRegressor (
                n_estimators=1000, nthread=100, reg_alpha = 100, gamma =1.0,
                colsample_bytree= 0.8,subsample=0.8, seed=self._random_seed, 
                min_child_weight = 0.1, max_depth=12, learning_rate=0.1,
                tree_method='gpu_hist')
            xgb_model.fit(X=train_x, y=train_y, verbose=False, eval_set=[(train_x, train_y),(validation_x, validation_y)],
                     eval_metric=[ 'mae'], early_stopping_rounds = 100)
            filename = self._model_path  +'model_'+str(j)+'.pkl'
            with open(filename, 'wb') as f:
                pickle.dump(obj =xgb_model,file= f)
            print('scores:', xgb_model.best_score, xgb_model.best_iteration)
        return
        

    def label_predict(self, sample_daily, factor_list):
                    
        res = []            
        for j in range(0,4):
            filename = self._model_path  +'model_'+str(j)+'.pkl'
            with open(filename, 'rb') as f:
                model = pickle.load(file=f)
            X_test = sample_daily[factor_list]
            y_pred = model.predict(X_test)
            label_pred = pd.Series(data=y_pred,index=sample_daily['stock'].values)
            res.append(label_pred)
        prediction = pd.concat(res, axis=1)
        return prediction
from datetime import datetime

close = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/close.pkl')
dates = list(close.index)
dates = [str(i.year)+str(i.month).zfill(2)+str(i.day).zfill(2) for i in dates]
train_start = '20180101'
date_start = '20190701'
date_end = '20200101'
step = 20
count = 0
lookback_period = 240
t = 'pm'
w = [1/3,1/3,1/3]
time_w = '1300_1459'
need_combine = [time_w+'_re_1d',time_w+'_re_3d',time_w+'_re_5d']
com_col = time_w+'_re_com'
need_label = time_w+'_re_5d'
need_label = com_col
w = 5
need_label = time_w+'_re_'+str(w)+'d'
root_model_path = '/data/user/013546/AlphaDataCenter/Models/'+t+'/'+'weekday_t/shuffle_final/'
root_predict_path = '/data/user/013546/AlphaDataCenter/DailyPrediction/'+t+'/'+'weekday_t/shuffle_final/'
model_dict = {'XgboostReg_Model':(need_label,w)}
print(model_dict)
factor_list = pd.read_pickle('/data/group/800020/AlphaDataCenter/HFSample/hfactor_list.pkl')
path_sample = '/data/group/800020/AlphaDataCenter/HFSample/NormSample/'#
dates = [i for i in dates if i>=date_start and i<=date_end]
week_flag = False 
for today_date in dates:
    retrain_flag = False
    if week_flag == True:
        retrain_flag = (count==0) | ((datetime.strptime(today_date,'%Y%m%d').weekday()+1)==5)
    else:
        retrain_flag = count%step==0         
    print('###########%s %s############' % (today_date,str(retrain_flag)))
    count+=1
    all_trading_days = sorted([e[:-4] for e in os.listdir(path_sample)])
    all_trading_days = [e for e in all_trading_days if e <= today_date]
    if retrain_flag == True:
        
        sample_required_dates = all_trading_days[-lookback_period-20 : ]

        sample_list = []
        for day in sample_required_dates:
            if day<train_start:
                continue
            df = pd.read_pickle(path_sample+ day +'.pkl')
            sample_list.append(df)
        training_sample = pd.concat(sample_list)
        training_sample[com_col] = (training_sample[need_combine]*w).sum(axis=1)
        # training_sample[np.isinf[training_sample]] = np.nan
        # training_sample.fillna(0,inplace=True)

        print('......................')
        

        for k,v in model_dict.items():
            gap_period = v[1]
            model_retrain_date = all_trading_days[-lookback_period- gap_period-1 :-gap_period-1]
            params={}
            params['label_name'] = v[0]
            params['modelname'] = k+'_'+params['label_name']
            params['model_path'] = root_model_path + params['modelname']+'/'+date_start+'_'+date_end+'/'
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
        params['model_path'] = root_model_path + params['modelname']+'/'+date_start+'_'+date_end+'/'
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
