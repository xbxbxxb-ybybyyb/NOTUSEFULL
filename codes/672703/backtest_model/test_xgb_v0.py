import numpy as np
import xgboost as xgb
import pickle
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.utils import shuffle  
class XgboostReg_Model_V0():
    
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
        
        dates = sample['date'].unique().tolist()
        
        for j in range(4):
            print('model',j)
            np.random.seed(self._random_seed)
            sample = shuffle(sample,random_state=1993)
            X_in_sample = sample[:int(0.75*len(sample))][factor_list]
            y_in_sample = sample[:int(0.75*len(sample))][self._label_name]
            X_train, X_cv, y_train, y_cv = train_test_split(X_in_sample, y_in_sample, 
                test_size = 0.1, random_state = self._random_seed)
            dtrain = xgb.DMatrix(X_train, y_train)
            dval = xgb.DMatrix(X_cv, y_cv)
            params = {'seed':1993,'eta': 0.1,'max_depth':10,'col_samlple':0.8,'reg_alpha':10,'tree_method':'gpu_hist'}
            maximize = False
            this_params = {}
            this_params = {'objective':'reg:linear','eval_metric':'mae'}
            params.update(this_params)
            xgb_model = xgb.train(params, dtrain, num_boost_round=600,evals = [(dtrain,'train'),(dval,'val')] ,verbose_eval=100,maximize=maximize)
   
            filename = self._model_path  +'model_'+str(j)+'.pkl'
            with open(filename, 'wb') as f:
                pickle.dump(obj =xgb_model,file= f)
            filename = self._model_path  +'factors_'+str(j)+'.pkl'
        return
        

    def label_predict(self, sample_daily, factor_list):

        res = []            
        for j in range(4):
            filename = self._model_path  +'model_'+str(j)+'.pkl'
            with open(filename, 'rb') as f:
                model = pickle.load(file=f)
            test_x = sample_daily[factor_list]
            test_dmatrix = xgb.DMatrix(test_x)
            y_pred = model.predict(test_dmatrix)
            label_pred = pd.Series(data=y_pred,index=sample_daily['stock'].values)
            res.append(label_pred)
        res = pd.concat(res, axis=1)
        prediction = res                

        return prediction
import pandas as pd
import numpy as np
import os
import time
import sys
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
        sample_list = []
        for day in sample_required_dates:
            df = pd.read_pickle(path_sample+ day + '.pkl')
            # ll = '0930_1129'
            # df['label'] = df[[ll+'_re_1d',ll+'_re_3d',ll+'_re_5d']].mean(axis=1)
            sample_list.append(df)
        training_sample = pd.concat(sample_list)
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
date_start = '20190101'
date_end = '20200508'
step = 20
count = 0
lookback_period_max = 240
retrain_flag = True  
root_path = '/data/user/013546/AlphaDataCenter/'
suffix = 'test1/'
model_config_list= [
            ('XgboostReg_Model_V0','pm','1300_1459_re_5d',5,240)
             ]
factor_list = pd.read_pickle('/data/group/800020/AlphaDataCenter/HFSample/hfactor_list.pkl')
print('factor list num:',len(factor_list))
path_sample = '/data/group/800020/AlphaDataCenter/HFSample/NormSample/'#
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