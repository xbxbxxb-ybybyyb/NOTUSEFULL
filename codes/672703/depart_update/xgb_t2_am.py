import numpy as np
import xgboost as xgb
import pickle
import pandas as pd

class XgboostRegression():
    
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
        import numpy as np
        np.random.seed(self._random_seed)
        np.random.shuffle(dates)

        train_dates = []
        train_dates.append(dates[:50])
        train_dates.append(dates[50:100])
        train_dates.append(dates[100:150])
        train_dates.append(dates[150:200])
        validation_dates = dates[200:]
        
        validation_set = sample[sample['date'].isin(validation_dates)].copy()  
        validation_x = validation_set[factor_list]
        validation_y = validation_set[self._label_name ]

        for j in range(4):
            train_set = sample[sample['date'].isin(train_dates[j])]  
            train_x = train_set[factor_list]
            train_y = train_set[self._label_name]
            train_dmatrix = xgb.DMatrix(train_x, train_y)
            valid_dmatrix = xgb.DMatrix(validation_x, validation_y)
            params = {'seed':1993,'eta': 0.1,
           'gamma': 1.0,'nthread': 100,
              'subsample':0.8,'colsample_bytree':0.8,'reg_alpha':100,
               'min_child_weight': 0.1, 'max_depth': 8,'tree_method':'gpu_hist'}
            maximize = False
            this_params = {}
            # if model_type == 'rank':
                # this_params = {'objective': 'rank:pairwise','eval_metric':'ndcg@200-'}
                # maximize = True
            # elif model_type =='reg':
                # this_params = {'objective':'reg:linear','eval_metric':'mae'}
            this_params = {'objective':'reg:linear','eval_metric':'mae'}
            params.update(this_params)
            xgb_model = xgb.train(params, train_dmatrix, num_boost_round=1000,maximize=maximize,early_stopping_rounds=100,
                                  evals=[(valid_dmatrix, 'validation')])
   
            filename = self._model_path  +'model_'+str(j)+'.pkl'
            with open(filename, 'wb') as f:
                pickle.dump(obj =xgb_model,file= f)
            print('scores:', xgb_model.best_score, xgb_model.best_iteration)
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
        prediction = res.mean(axis =1)                    
        return prediction
def update_model_predict(root_path='',path_sample=[],factor_list=[],
            today_date = '20200407',retrain_flag = True,lookback_period_max = 300,
            model_config_list = [
                    ('XgboostReg_Model','vwap','vwap_re_1d',1,240),
                    ('DeepFM_Model','vwap','vwap_re_1d',1,240),
                    ('Lr_Model','vwap','vwap_re_5d',5,240)
                        ],suffix=None):
    t = time.time()
    path_feature = '/data/group/800020/AlphaDataCenter/Sample/NormSample/'
    path_label = '/data/group/800020/AlphaDataCenter/Department/DepartSample/Sample/label/'
    this_label = pd.read_pickle('/data/user/013546/rubbish/sort_extreme_0930_1129_5d.pkl')
    if retrain_flag == True:
        all_trading_days = sorted([e[:-4] for e in os.listdir(path_label)])
        all_trading_days = [e for e in all_trading_days if e <= today_date]
        sample_required_dates = all_trading_days[-lookback_period_max-20 : ]
        sample_feature = []
        sample_label = []
        for day in sample_required_dates:
            df = pd.read_pickle(path_feature+ day + '.pkl')[['date','stock']+factor_list]
            sample_feature.append(df)
            df = pd.read_pickle(path_label+ day + '.pkl')
            sample_label.append(df)
        training_sample = pd.concat(sample_feature)
        training_sample = training_sample.merge(pd.concat(sample_label),on=['date','stock'],how='left')
        training_sample = training_sample.merge(this_label,on=['date','stock'],how='left')
        training_sample['sort_extreme_0930_1129_5d'] = training_sample['sort_extreme_0930_1129_5d'].fillna(0)
        print('......................')   
    sample_daily = pd.read_pickle(path_feature+today_date+'.pkl')
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
date_end = '20200630'
step = 20
count = 0
lookback_period_max = 240
retrain_flag = True  
root_path = '/data/user/013546/AlphaDataCenter/'
suffix = 'sort_extreme_'+date_start+'_'+date_end+'/'
model_config_list= [
            ('XgboostRegression','am','sort_extreme_0930_1129_5d',5,240)
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