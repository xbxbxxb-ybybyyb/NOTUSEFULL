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

        self._label_name = '1300_1459_re_1d'
        self._random_seed = 1990
        self._modelname =  params['modelname']
        self._model_path = params['model_path']
        self._prediction_path = params['prediction_path']
    def unifier_sample_set(self,sample_set,factor_list,label,pct_label,ratio):
        tmp = sample_set.groupby('date')['stock'].count()
        stock_nums = int(tmp.mean())
        min_counts = int(1/2*stock_nums)
        invalid_dates = tmp[tmp<min_counts].index.tolist()
        sample_set_valid = sample_set[~ sample_set['date'].isin(invalid_dates)]
        sample_set_valid = sample_set_valid[(sample_set_valid[pct_label]>=(1-ratio))|(sample_set_valid[pct_label]<=ratio)]
        X = sample_set_valid[factor_list]
        y = sample_set_valid[label]
        return X,y
    def train_test_split(self,dates,date_shuffle=True,random_seed=1993,n_splits=4,size=100):
        train_dates = []
        if(date_shuffle==True):
            np.random.seed(random_seed)
            np.random.shuffle(dates)
            num = int(size/n_splits)
            for i in range(n_splits):
                train_dates.append(dates[i*num:(i+1)*num])
            validation_dates = dates[size:]
        return train_dates,validation_dates
    def revise_model_path(self, path):
        self._model_path = path
    
    def revise_label(self, label):
        self._label_name = label

    def revise_random_seed(self, seed):
        self._random_seed = seed
    def train(self,train_x,train_y,validation_x,validation_y):  
        train_dmatrix = xgb.DMatrix(train_x, train_y)
        valid_dmatrix = xgb.DMatrix(validation_x, validation_y)
        params = {'nthread': 100, 
              'max_depth': 10,  
              'eta': 0.1,  
              # 'silent': True,  
              # 'gamma': 0, 
              'colsample_bytree': 0.5,
              # 'alpha': 0,  
              # 'lambda': 0,  
              # 'seed': 1993,
              'tree_method':'gpu_hist',
               'predictor':'gpu_predictor'
              }
        maximize = False
        this_params = {'objective':'reg:linear','eval_metric':'mae'}
        params.update(this_params)
        xgb_model = xgb.train(params, train_dmatrix,maximize=maximize,early_stopping_rounds=30,num_boost_round=1000,
                              evals=[(valid_dmatrix, 'validation')],verbose_eval=50)
        return xgb_model
    def get_model(self, sample, factor_list):
        dates = pd.to_datetime(sample['date'].values).unique().tolist()
        train_dates_list,validation_dates = self.train_test_split(dates,n_splits=4,size=200)
        for i in range(len(train_dates_list)):
            train_dates = train_dates_list[i]
            validation_set = sample[sample['date'].isin(validation_dates)].copy()  
            validation_x = validation_set[factor_list]
            validation_y = validation_set[self._label_name ]
            train_set = sample[sample['date'].isin(train_dates)].copy()
            train_x = train_set[factor_list]
            train_y = train_set[self._label_name]
            xgb_model = self.train(train_x,train_y,validation_x,validation_y)
            filename = self._model_path  +'model_'+str(i)+'.pkl'
            with open(filename, 'wb') as f:
                pickle.dump(obj =xgb_model,file= f)
            print('scores:', xgb_model.best_score, xgb_model.best_iteration)
        return
        

    def label_predict(self, sample_daily, factor_list):
                    
        res = []            
        for i in range(0,4):
            filename = self._model_path  +'model_'+str(i)+'.pkl'
            with open(filename, 'rb') as f:
                model = pickle.load(file=f)
            X_test = sample_daily[factor_list]
            y_pred = model.predict(xgb.DMatrix(X_test))
            label_pred = pd.Series(data=y_pred,index=sample_daily['stock'].values)
            res.append(label_pred)
        prediction = pd.concat(res, axis=1)
        return prediction
     
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger()
logger.addHandler(logging.FileHandler('/data/user/013546/rubbish/log/mdp5.log', 'a'))
print = logger.info
close = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/close.pkl')
dates = list(close.index)
dates = [str(i.year)+str(i.month).zfill(2)+str(i.day).zfill(2) for i in dates]
train_start = '20180101'
date_start = '20190701'
date_end = '20200327'
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
w = 1
need_label = time_w+'_re_'+str(w)+'d'
root_model_path = '/data/user/013546/AlphaDataCenter/Models/'+t+'/'+'depart/ori1/'
root_predict_path = '/data/user/013546/AlphaDataCenter/DailyPrediction/'+t+'/'+'depart/ori1/'
model_dict = {'XgboostReg_Model':(need_label,w)}
print(model_dict)
path_sample = '/data/group/800020/AlphaExperiment/Final_Sample/HFSample/'#
dates = [i for i in dates if i>=date_start and i<=date_end]
week_flag = False 

factor_list = pd.read_pickle('/data/group/800020/AlphaExperiment/Final_Sample/depart_hfactor_list.pkl')
for today_date in dates:
  
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
