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
from sklearn.model_selection import train_test_split
class XgbRegOne():
    
    def __init__(self,params):

        self._label_name = params['label_name']
        self._random_seed = 1990
        self._modelname =  params['modelname']
        self._model_path = '/data/group/800020/AlphaDataCenter/Models/'+self._modelname+'/'
        self._prediction_path = '/data/group/800020/AlphaDataCenter/DailyPrediction/pm/'+self._modelname+'/'


    def revise_model_path(self, path):
        self._model_path = path
    
    def revise_label(self, label):
        self._label_name = label

    def revise_random_seed(self, seed):
        self._random_seed = seed

    def get_model(self, sample, factor_list):
        train_x, validation_x, train_y, validation_y = train_test_split(sample[factor_list], 
                    sample[self._label_name], 
            test_size = 0.1, random_state = self._random_seed)
        xgb_model = xgb.XGBRegressor (
            n_estimators=1000, nthread=100, reg_alpha = 100, gamma =1.0,
            colsample_bytree= 0.8,subsample=0.8, seed=self._random_seed, 
            min_child_weight = 0.1, max_depth=8, learning_rate=0.1,
            tree_method='gpu_hist')
        xgb_model.fit(X=train_x, y=train_y, verbose=False, eval_set=[(train_x, train_y),(validation_x, validation_y)],
                 eval_metric=[ 'mae'], early_stopping_rounds = 100)
        filename = self._model_path  +'model.pkl'
        with open(filename, 'wb') as f:
            pickle.dump(obj =xgb_model,file= f)
        print('scores:', xgb_model.best_score, xgb_model.best_iteration)
        return
        

    def label_predict(self, sample_daily, factor_list):
        filename = self._model_path  +'model.pkl'
        with open(filename, 'rb') as f:
            model = pickle.load(file=f)
        model.get_booster().set_param({'predictor':'cpu_predictor'})
        X_test = sample_daily[factor_list]
        y_pred = model.predict(X_test)
        label_pred = pd.Series(data=y_pred,index=sample_daily['stock'].values)
        return label_pred