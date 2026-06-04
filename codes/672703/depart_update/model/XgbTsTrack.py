import numpy as np
import xgboost as xgb
import pickle
import pandas as pd

class XgbTsTrack():
    
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
        dates = sample['date'].unique().tolist()
        dates = sorted(dates)
        for i in range(4):
            train_dates = dates[i*60:(i+1)*60]
            validation_dates = sorted(list(set(dates)-set(train_dates)))
            validation_set = sample[sample['date'].isin(validation_dates)].copy()  
            validation_x = validation_set[factor_list]
            validation_y = validation_set[self._label_name]
            train_set = sample[sample['date'].isin(train_dates)].copy()  
            train_x = train_set[factor_list]
            train_y = train_set[self._label_name]
            xgb_model = xgb.XGBRegressor (
                        n_estimators=1000, nthread=24, min_child_weight = 0.1,reg_alpha = 10, gamma =1.0,
                        tree_method='gpu_hist', gpu_id=0,
                      colsample_bytree= 0.8, colsample_bylevel= 0.8, subsample=0.8 , seed=self._random_seed,  max_depth=8, learning_rate=0.1 )

            xgb_model.fit(X=train_x, y=train_y, verbose=False, eval_set=[(train_x, train_y),(validation_x, validation_y)],
                     eval_metric=[ 'mae'], early_stopping_rounds = 20)
            filename = self._model_path  +'model_'+str(i)+'.pkl'
            with open(filename, 'wb') as f:
                pickle.dump(obj =xgb_model,file= f)
            print('scores:', xgb_model.best_score, xgb_model.best_iteration)
        return
        

    def label_predict(self, sample_daily, factor_list):
                    
        res = []    
        for i in range(4):
            filename = self._model_path  +'model_'+str(i)+'.pkl'
            with open(filename, 'rb') as f:
                model = pickle.load(file=f)
            X_test = sample_daily[factor_list]
            y_pred = model.predict(X_test)
            label_pred = pd.Series(data=y_pred,index=sample_daily['stock'].values)
            res.append(label_pred)
        res = pd.concat(res, axis=1)
        prediction = res
        return prediction