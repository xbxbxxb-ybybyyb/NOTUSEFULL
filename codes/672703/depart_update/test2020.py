import pandas as pd
import numpy as np
import os
import time
import sys
import numpy as np
import xgboost as xgb
from lightgbm import LGBMRegressor    
import lightgbm as lgb
import pickle
import pandas as pd
from sklearn.model_selection import train_test_split
class LgbReg():
    
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
    def learning_rate(self,n):
        if n > 6000:
            return 0.01 * np.exp(-(n-6000)/600) + 0.001
        elif n > 4000:
            return 0.02 * np.exp(-(n-4000)/600) + 0.001
        elif n > 2000:
            return 0.05 * np.exp(-(n-2000)/600) + 0.001
        else:
            return 0.1 * np.exp(-n/600) + 0.001
    def get_model(self, sample, factor_list):
        dates = sample['date'].unique().tolist()
        for l in [5]:
            dates_tmp = dates.copy()
            np.random.seed(1993)
            np.random.shuffle(dates_tmp)
            train_dates = dates_tmp[:-41]
            valid_dates = dates[-40:]
            label = self._label_name[:-2]+str(l)+'d'
            n_iters = 300
            train_x, train_y = sample[sample['date'].isin(train_dates)][factor_list], sample[sample['date'].isin(train_dates)][label]
            valid_x, valid_y = sample[sample['date'].isin(valid_dates)][factor_list], sample[sample['date'].isin(valid_dates)][label]
            model = LGBMRegressor(n_jobs=100, objective = 'huber',num_leaves=64, max_depth=6, learning_rate=0.1, 
                 n_estimators=n_iters, subsample_for_bin=50000, silent=False,
                 reg_lambda=10,reg_alpha=10, random_state=1605, first_metric_only=True,
                 feature_fraction=0.6, feature_fraction_seed=1504, bagging_fraction=0.6, bagging_fraction_seed=1504,
                 device='gpu', gpu_use_dp='true', gpu_device_id=0, gpu_platform_id=0)
            model.fit(train_x, train_y, early_stopping_rounds=20,verbose=50,
                   eval_set=[(valid_x, valid_y)],callbacks=[lgb.reset_parameter(learning_rate=self.learning_rate)])
            filename = self._model_path  +'model_'+str(l)+'.pkl'
            with open(filename, 'wb') as f:
                pickle.dump(obj =model,file= f)
        return
        

    def label_predict(self, sample_daily, factor_list):

        res = []       
        for l in [5]:
            filename = self._model_path  +'model_'+str(l)+'.pkl'
            with open(filename, 'rb') as f:
                model = pickle.load(file=f)
            test_x = sample_daily[factor_list]
            y_pred = model.predict(test_x)
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
    
    if retrain_flag == True:
        all_trading_days = sorted([e[:-4] for e in os.listdir(path_sample)])
        all_trading_days = [e for e in all_trading_days if e <= today_date]
        sample_required_dates = all_trading_days[-lookback_period_max-20 : ]
        sample_feature = []
   
        for day in sample_required_dates:
            df = pd.read_pickle(path_sample + day + '.pkl')
            sample_feature.append(df)
    
        training_sample = pd.concat(sample_feature)
      
        print('......................')   
    sample_daily = pd.read_pickle(path_sample+today_date+'.pkl')
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
        
close = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/close.pkl')
dates = list(close.index)
dates = [str(i.year)+str(i.month).zfill(2)+str(i.day).zfill(2) for i in dates]
train_start = '20180101'
date_start = '20200101'
date_end = '20200601'
step = 20
count = 0
lookback_period_max = 240
retrain_flag = True  
root_path = '/data/user/013546/AlphaDataCenter/'
suffix = 'test_lgb_own/'
model_config_list= [
            ('LgbReg','am','0930_1129_re_5d',5,240)
             ]
factor_list = pd.read_pickle('/data/group/800020/AlphaDataCenter/Sample/factor_list.pkl')
print('factor list num:',len(factor_list))
path_sample = '/data/group/800020/AlphaDataCenter/Sample/NormSample/'#
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