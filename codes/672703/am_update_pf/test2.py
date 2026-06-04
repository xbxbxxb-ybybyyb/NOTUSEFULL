import numpy as np
import xgboost as xgb
import pickle
import pandas as pd

class XgboostReg_Model():
    
    def __init__(self):

        self._label_name = '1300_1459_re_1d'
        self._random_seed = 1990
        self._modelname =  'XgboostRegression_'+ self._label_name
        self._model_path = '/data/group/800020/AlphaDataCenter/Models/'+self._modelname+'/'
        self._prediction_path = '/data/group/800020/AlphaDataCenter/DailyPrediction/pm/'+self._modelname+'/'

    def revise_model_path(self, path):
        self._model_path = path
    
    def revise_label(self, label):
        self._label_name = label

    def revise_random_seed(self, seed):
        self._random_seed = seed

    def get_model(self, sample, factor_list):
        model_type = 'reg'
        
        dates = sample['date'].unique().tolist()

        np.random.shuffle(dates)

        train_dates = []
        train_dates.append(dates[50:100])
        validation_dates = dates[200:]
        validation_set = sample[sample['date'].isin(validation_dates)].copy()  
        validation_x = validation_set[factor_list]
        validation_y = validation_set[self._label_name ]

        for j in range(1):
            train_set = sample[sample['date'].isin(train_dates[j])]  
            train_x = train_set[factor_list]
            train_y = train_set[self._label_name]
            train_dmatrix = xgb.DMatrix(train_x, train_y)
            valid_dmatrix = xgb.DMatrix(validation_x, validation_y)
            params = {'seed':1993,'eta': 0.1,
           'gamma': 1.0,'nthread': 30,
              'subsample':0.8,'colsample_bytree':0.8,'reg_alpha':100,
               'min_child_weight': 0.1, 'max_depth': 8}
            maximize = False
            this_params = {}
            if model_type == 'rank':
                this_params = {'objective': 'rank:pairwise','eval_metric':'ndcg@200-'}
                maximize = True
            elif model_type =='reg':
                this_params = {'objective':'reg:linear','eval_metric':'mae'}
            params.update(this_params)
            xgb_model = xgb.train(params, train_dmatrix, num_boost_round=1000,maximize=maximize,early_stopping_rounds=100,
                                  evals=[(valid_dmatrix, 'validation')])
   
            filename = self._model_path  +'model_'+str(1)+'.pkl'
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

import pandas as pd
import numpy as np
import os
import time


# import datetime
# today = datetime.date.today()
# today = str(today.year)+str(today.month).zfill(2)+str(today.day).zfill(2)

def run(today,retrain_flag=True):
    print('#################predict############')
    today_date = today
    lookback_period = 240
    # factor_list = (sorted([e[:-4] for e in os.listdir('/data/group/800020/AlphaDataCenter/NeutralizedFactors/IndustrySizeNeutralized/')]))
    # factor_list_hf = (sorted([e[:-4] for e in os.listdir\
    # ('/data/group/800020/AlphaDataCenter/NeutralizedHFactors/IndustrySizeNeutralized//')]))
    # factor_list.extend(factor_list_hf)
    factor_list = pd.read_pickle('/data/group/800020/AlphaDataCenter/Sample/factor_list.pkl')
    hfactor_list =  pd.read_pickle('/data/group/800020/AlphaDataCenter/HFSample/hfactor_list.pkl')
    hfactors = [i for i in hfactor_list if i not in factor_list]
    hfactors.sort()
    factor_list.extend(hfactors)    
    
    print('@ factor number:',len(factor_list))

    if retrain_flag == True:
        all_trading_days = sorted([e[:-4] for e in os.listdir('/data/group/800020/AlphaDataCenter/HFSample/NormSample/')])
        all_trading_days = [e for e in all_trading_days if e <= today_date]
        sample_required_dates = all_trading_days[-lookback_period-20 : ]

        sample_list = []
        for day in sample_required_dates:
            sample_list.append(pd.read_pickle('/data/group/800020/AlphaDataCenter/HFSample/NormSample/'+ day +'.pkl'))
        training_sample = pd.concat(sample_list)


        print('......................')
        # ######################### 5d label models
        gap_period = 5
        model_retrain_date = all_trading_days[-lookback_period- gap_period-1 :-gap_period-1]
        retrain_samples = training_sample[training_sample['date'].isin(model_retrain_date)]
       
        for model in [XgboostReg_Model()]:
            t = time.time()
            if not os.path.exists(model._model_path):
                os.mkdir(model._model_path)
            model.get_model(retrain_samples.copy(), factor_list)
            print(model._modelname +' re-train finished' , time.time() - t)
import datetime 
today = datetime.datetime.today().strftime('%Y%m%d')
run('20200317')



