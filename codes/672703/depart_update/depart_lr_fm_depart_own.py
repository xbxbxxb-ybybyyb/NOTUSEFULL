import numpy as np
import xgboost as xgb
import pickle
import pandas as pd
import xgboost as xgb
from lightgbm import LGBMRegressor ,LGBMRanker   
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from scipy.stats import norm
import sys
sys.path.insert(0,'depart_update/model')
from sklearn import linear_model
import pickle
import pandas as pd
from sklearn import linear_model
import pickle


class Lr_Model():
    
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
        sample = sample[~np.isnan(sample[self._label_name])]
#        sample = sample[sample[self._label_name].abs()<=3]
        dates = sample['date'].unique().tolist()
        X_train = sample[factor_list]
        y_train = sample[self._label_name]
        model = linear_model.LinearRegression(fit_intercept=True,n_jobs=15)
        model.fit(X_train,y_train)
        
        filename = self._model_path + 'model.pkl'
        with open(filename, 'wb') as f:
            pickle.dump(obj =model,file= f)
        return 
    def label_predict(self, sample_daily, factor_list):
            
        filename = self._model_path  +'model.pkl'
        with open(filename, 'rb') as f:
            model = pickle.load(file=f)
        
        X_test = sample_daily[factor_list]
        y_pred = model.predict(X_test)
        label_pred = pd.Series(data=y_pred,index=sample_daily['stock'].values)
        return label_pred
        
def update_model_predict(root_path='',path_sample=[],factor_list=[],
            today_date = '20200407',retrain_flag = True,lookback_period_max = 300,
            model_config_list = [
                    ('XgboostReg_Model','vwap','vwap_re_1d',1,240),
                    ('DeepFM_Model','vwap','vwap_re_1d',1,240),
                    ('Lr_Model','vwap','vwap_re_5d',5,240)
                        ],suffix=None):
    t = time.time()
    path_feature = '/data/group/800020/AlphaDataCenter/Department/DepartSample/Sample/feature/'
    path_label = '/data/group/800020/AlphaDataCenter/Department/DepartSample/Sample/label/'
    path_own_feature = '/data/group/800020/AlphaDataCenter/Sample/NormSample/'
    own_factors = pd.read_pickle('/data/user/013546/陈卓/factor300.pkl')
    depart_factors = pd.read_pickle('/data/group/800020/AlphaDataCenter/Department/DepartSample/factor_info_nn.pkl')['depart_day_factors']
    label = pd.read_pickle('/data/group/800020/AlphaExperiment/Test/label_vwap_am_keepna.pkl')
    label = pd.read_pickle('/data/user/013546/rubbish/vwap_ret_rank_norm.pkl')
    if retrain_flag == True:
        all_trading_days = sorted([e[:-4] for e in os.listdir(path_feature)])
        all_trading_days = [e for e in all_trading_days if e <= today_date]
        sample_required_dates = all_trading_days[-lookback_period_max-20 : ]
        sample_feature = []
        sample_label = []
        sample_own_feature = []
        for day in sample_required_dates:
            df = pd.read_pickle(path_feature+ day + '.pkl')[['date','stock']+depart_factors]
            sample_feature.append(df)
            df = pd.read_pickle(path_label+ day + '.pkl')
            sample_label.append(df)
            df = pd.read_pickle(path_own_feature+ day + '.pkl')[['date','stock']+own_factors]
            sample_own_feature.append(df)
        training_sample = pd.concat(sample_feature)
        training_sample = training_sample.merge(pd.concat(sample_label),on=['date','stock'],how='left')
        training_sample = training_sample.merge(pd.concat(sample_own_feature),on=['date','stock'],how='left')
        training_sample = training_sample[['date','stock']+factor_list].merge(label,on=['date','stock'],how='left')
        print('......................')   
    sample_daily = pd.read_pickle(path_feature+today_date+'.pkl')[['date','stock']+depart_factors]
    sample_daily_own = pd.read_pickle(path_own_feature+ today_date + '.pkl')[['date','stock']+own_factors]
    sample_daily = sample_daily.merge(sample_daily_own,on=['date','stock'],how='left')
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
        params['modelname'] = config[0]+'_'+params['label_name']
        params['model_path'] = root_model_path + params['modelname']+'/'
        params['prediction_path'] = root_predict_path + params['modelname']+'/'
        params['sample_path'] = path_sample
        execstr = config[0]+'(params)'
        model = eval(execstr)
        if retrain_flag == True:
            gap_period = config[3]
            model_retrain_date = all_trading_days[-config[4]- gap_period-1 :-gap_period-1]
            retrain_samples = training_sample[training_sample['date'].isin(model_retrain_date)]
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
close = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/close.pkl')
dates = list(close.index)
dates = [str(i.year)+str(i.month).zfill(2)+str(i.day).zfill(2) for i in dates]
train_start = '20180101'
date_start = '20200101'
date_end = '20200717'
step = 5
count = 0
lookback_period_max = 240
retrain_flag = True  
root_path = '/data/user/013546/AlphaDataCenter/'
suffix = 'depart_depart_own300_5step_ranknorm_'+date_start+'_'+date_end+'/'
model_config_list= [
            ('Lr_Model','vwap','vwap_re_5d',5,240)
             ]
factor_list0 = pd.read_pickle('/data/group/800020/AlphaDataCenter/Department/DepartSample/factor_info_nn.pkl')['depart_day_factors']
factor_list1 = pd.read_pickle('/data/user/013546/陈卓/factor300.pkl')
factor_list = sorted(list(set(factor_list0+factor_list1)))
print('factor list num:',len(factor_list))
path_sample = '/data/group/800020/AlphaDataCenter/Department/DepartSample/Sample/feature/'#
dates = [i for i in dates if i>=date_start and i<=date_end]
for today_date in dates:
    if count % step == 0:
        retrain_flag = True
    else: 
        retrain_flag = False          
    print('###########%s %s############' % (today_date,str(retrain_flag)))
    count+=1                            
    update_model_predict(root_path=root_path,path_sample=path_sample,factor_list=factor_list,
                today_date = today_date,retrain_flag = retrain_flag,
                lookback_period_max = lookback_period_max,
                model_config_list = model_config_list,suffix=suffix)