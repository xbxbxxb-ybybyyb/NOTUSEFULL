import numpy as np
import xgboost as xgb
import pickle
import pandas as pd
import xgboost as xgb
from lightgbm import LGBMRegressor ,LGBMRanker   
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from scipy.stats import norm
from scipy import stats
class LgbReg():
    
    def __init__(self,params):

        self._label_name = params['label_name']
        self._random_seed = 1990
        self._modelname =  params['modelname']
        self._model_path = params['model_path']
        self._prediction_path = params['prediction_path']
        self._count = 3
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
        np.random.seed(self._random_seed)
        np.random.shuffle(dates)
        
        num_dates = int(len(dates)/self._count)
        for j in range(self._count):
            this_sample = sample[sample['date'].isin(dates[j*num_dates:(j+1)*num_dates])]
            train_x, validation_x, train_y, validation_y = train_test_split(this_sample[factor_list], this_sample[self._label_name], 
                test_size = 0.1, random_state = self._random_seed)
            model = LGBMRegressor(n_jobs=24, num_leaves=64, max_depth=6, 
            learning_rate=0.1, n_estimators=2000, silent=False,metric='rmse',
                 reg_lambda=1000,random_state=1605, 
                first_metric_only=True,
                 feature_fraction=0.8, feature_fraction_seed=1504, 
                bagging_fraction=0.8, bagging_fraction_seed=1504)
            model.fit(train_x, train_y, callbacks=[lgb.reset_parameter(learning_rate=lambda n: 0.1 * np.exp(-n/600) + 0.001)],    
                      eval_set=[(validation_x, validation_y)],early_stopping_rounds=40)
            filename = self._model_path  +'model_'+str(j)+'.pkl'
            with open(filename, 'wb') as f:
                pickle.dump(obj = model,file= f)
            print('scores:', model.best_score_, model.best_iteration_)
        return
        

    def label_predict(self, sample_daily, factor_list):
        res = []            
        for j in range(self._count):
            filename = self._model_path  +'model_'+str(j)+'.pkl'
            with open(filename, 'rb') as f:
                model = pickle.load(file=f)
            test_x = sample_daily[factor_list]
            y_pred = model.predict(test_x,num_iteration=model.best_iteration_)
            label_pred = pd.Series(data=y_pred,index=sample_daily['stock'].values)
            res.append(label_pred)
        res = pd.concat(res, axis=1)
        prediction = res.mean(axis =1)    
        return prediction