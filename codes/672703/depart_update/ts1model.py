import numpy as np
import xgboost as xgb
import pickle
import pandas as pd

class XgbRegTSOneModel():
    
    def __init__(self,params):

        self._label_name = params['label_name']
        self._random_seed = 1990
        self._modelname =  params['model_name']
        self._model_path = params['model_path']
        self._prediction_path = params['prediction_path']

    def revise_model_path(self, path):
        self._model_path = path
    
    def revise_label(self, label):
        self._label_name = label

    def revise_random_seed(self, seed):
        self._random_seed = seed
        
        
    def get_model(self, sample, factor_list):
        
        dates = pd.to_datetime(sample['date'].unique().tolist())
        amt = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/amt.pkl')
        amt_rank = amt.sum(axis=1).loc[dates].rank(pct=True)
        amt_index = amt_rank[(amt_rank>0.9)|(amt_rank<0.1)].index.tolist()
        dates = sorted(list(set(dates)-set(amt_index)))
        sample = sample[sample['date'].isin(dates)]
#        train_dates = dates[:200]
#        validation_dates = dates[200:]
#        print(train_dates)
#        drop_dates = pd.to_datetime(['2020-02-26','2020-02-27','2020-03-02','2020-03-04','2020-03-06'])
#        train_dates = sorted(list(set(train_dates)-set(drop_dates)))
#        validation_dates = sorted(list(set(dates)-set(train_dates)))
#        print(len(train_dates),len(validation_dates))
#        validation_set = sample[sample['date'].isin(validation_dates)].copy()  
#        validation_x = validation_set[factor_list]
#        validation_y = validation_set[self._label_name]
#        train_set = sample[sample['date'].isin(train_dates)].copy()  
#        train_x = train_set[factor_list]
#        train_y = train_set[self._label_name]
#        xgb_model = xgb.XGBRegressor (
#                    n_estimators=1000, nthread=100, min_child_weight = 0.1,reg_alpha = 10, gamma =1.0,
#                    tree_method='gpu_hist', gpu_id=0,
#                  colsample_bytree= 0.8, colsample_bylevel= 0.8, subsample=0.8 , seed=self._random_seed,  max_depth=8, learning_rate=0.1 )

#        xgb_model.fit(X=train_x, y=train_y, verbose=False, eval_set=[(train_x, train_y),(validation_x, validation_y)],
#                 eval_metric=[ 'mae'], early_stopping_rounds = 20)
#        print('scores:', xgb_model.best_score, xgb_model.best_iteration)
        xgb_model = xgb.XGBRegressor (
                    n_estimators=60, nthread=100, min_child_weight = 0.1,reg_alpha = 10, gamma =1.0,
                    tree_method='gpu_hist', gpu_id=0,
                  colsample_bytree= 0.8, colsample_bylevel= 0.8, subsample=0.8 , seed=self._random_seed,  max_depth=8, learning_rate=0.1 )

        xgb_model.fit(X=sample[factor_list], y=sample[self._label_name], verbose=False,
                 eval_metric=[ 'mae'])
        filename = self._model_path  +'model.pkl'
        with open(filename, 'wb') as f:
            pickle.dump(obj =xgb_model,file= f)
        
        return
        

    def label_predict(self, sample_daily, factor_list):
                    
        res = []            
        filename = self._model_path  +'model.pkl'
        with open(filename, 'rb') as f:
            model = pickle.load(file=f)
        X_test = sample_daily[factor_list]
        y_pred = model.predict(X_test)
        label_pred = pd.Series(data=y_pred,index=sample_daily['stock'].values)
        res.append(label_pred)
        res = pd.concat(res, axis=1)
        prediction = res
        return prediction
def update_model_predict(root_path='',path_sample=[],factor_list=[],
            today_date = '20200407',retrain_flag = True,lookback_period_max = 300,
            model_config_list = [
                    ('XgboostReg_Model','vwap','vwap_re_1d',1,240),
                    ('DeepFM_Model','vwap','vwap_re_1d',1,240),
                    ('Lr_Model','vwap','vwap_re_5d',5,240)
                        ],suffix=None):
    t = time.time()
    path_feature = path_sample
    if retrain_flag == True:
        all_trading_days = sorted([e[:-4] for e in os.listdir(path_feature)])
        all_trading_days = [e for e in all_trading_days if e <= today_date]
        sample_required_dates = all_trading_days[-lookback_period_max-20 : ]
        sample_feature = []
        sample_label = []
        for day in sample_required_dates:
            df = pd.read_pickle(path_feature+ day + '.pkl')
            sample_feature.append(df)
        training_sample = pd.concat(sample_feature)
        print('......................')   
    sample_daily = pd.read_pickle(path_feature+today_date+'.pkl')
    global model_path
    for config in model_config_list:
        print(config)
        excess = config[1]
        root_model_path = root_path+'Models/'+excess+'/'
        root_predict_path = root_path+'/DailyPrediction/'+excess+'/'
        if not suffix is None:
            root_model_path += suffix
            root_predict_path += suffix
        params={}
        params['label_name'] = config[2]
        params['weight'] = [-6,-2,0,0,0,10]
        params['time'] = excess
        params['model_name'] = config[0]+'_'+params['label_name']
        if retrain_flag:
            model_path = root_model_path + params['model_name']+'/'+today_date+'/'
        params['model_path'] = model_path
        params['prediction_path'] = root_predict_path + params['model_name']+'/'
        params['sample_path'] = path_sample
        execstr = config[0]+'(params)'
        model = eval(execstr)
        if retrain_flag == True:
   
            gap_period = config[3]
            model_retrain_date = all_trading_days[-config[4]- gap_period-1 :-gap_period-1]
            retrain_samples = training_sample[training_sample['date'].isin(model_retrain_date)]
            retrain_samples = retrain_samples[~np.isnan(retrain_samples[params['label_name']])]
       
            t = time.time()
            if not os.path.exists(model._model_path):
                os.makedirs(model._model_path)
            model.get_model(retrain_samples.copy(), factor_list)
            print(model._modelname +' re-train finished' , time.time() - t)
        
        pred = model.label_predict(sample_daily, factor_list)
        if not os.path.exists(model._prediction_path):
            os.makedirs(model._prediction_path)
        pred.to_csv(model._prediction_path + today_date +'.csv')
        print(model._modelname +'   predict finished' , today_date, time.time() - t)
import time
import os
import sys
#sys.path.insert(0,'depart_update/model/')
#from XgbRegTSFourModel import *
#from XgbRegTSOneModel import *
close = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/close.pkl')
dates = list(close.index)
dates = [str(i.year)+str(i.month).zfill(2)+str(i.day).zfill(2) for i in dates]
train_start = '20180101'
date_start = '20200221'
date_end = '20200324'
step = 20
count = 0
lookback_period_max = 240
retrain_flag = False  
week_flag = True 
root_path = '/data/user/013546/AlphaDataCenter/'
suffix = 'onemodel2_'+date_start+'_'+date_end+'/'
model_config_list= [
    ('XgbRegTSOneModel','vwap','vwap_re_5d',5,240)
             ]
model_path = ''
factor_list = pd.read_pickle('/data/group/800020/AlphaDataCenter/Sample/factor_list.pkl')
rubbish = ['Vwap_Close_Range_Diff', 'LongBear', 'LongBull', 
'BollingerDown20d', 'ShortBear', 'BollingerUp20d', 
 'ShortBull', 'RankNetProfitDps']
factor_list = sorted(list(set(factor_list)-set(rubbish)))
print('factor list num:',len(factor_list))
path_sample = '/data/group/800020/AlphaDataCenter/Sample/NormSample/'#
dates = [i for i in dates if i>=date_start and i<=date_end]
from datetime import datetime
for today_date in dates:
    week = datetime.strptime(today_date,'%Y%m%d').weekday()
    if week_flag:
        cond = ((count==0) or(week==4))
    else:
        cond = (count%step==0)
    if cond:
        retrain_flag = True
    else: 
        retrain_flag = False          
    print('###########%s %s############' % (today_date,str(retrain_flag)))
    count+=1                            
    update_model_predict(root_path=root_path,path_sample=path_sample,factor_list=factor_list,
                today_date = today_date,retrain_flag = retrain_flag,
                lookback_period_max = lookback_period_max,
                model_config_list = model_config_list,suffix=suffix)