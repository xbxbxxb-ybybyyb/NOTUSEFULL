import numpy as np
import xgboost as xgb
import pickle
import pandas as pd

class XgboostReg_Model():
    
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
            xgb_model = xgb.XGBRegressor (
                      n_estimators=1000, nthread=100, reg_alpha = 100, gamma =1.0,
                      colsample_bytree= 0.8,subsample=0.8, seed=self._random_seed, 
                    min_child_weight = 0.1, max_depth=8, learning_rate=0.1,
                    tree_method='gpu_hist')
            xgb_model.fit(X=train_x, y=train_y, verbose=False, eval_set=[(train_x, train_y),(validation_x, validation_y)],
                     eval_metric=[ 'mae'], early_stopping_rounds = 100)
            filename = self._model_path  +'model_'+str(j)+'.pkl'
            with open(filename, 'wb') as f:
                pickle.dump(obj =xgb_model,file= f)
            print('scores:', xgb_model.best_score, xgb_model.best_iteration)
        
        return
        

    def label_predict(self, sample_daily, factor_list):
                    
        res = []            
        for j in range(0,4):
            filename = self._model_path  +'model_'+str(j)+'.pkl'
            with open(filename, 'rb') as f:
                model = pickle.load(file=f)
            X_test = sample_daily[factor_list]
            y_pred = model.predict(X_test)
            label_pred = pd.Series(data=y_pred,index=sample_daily['stock'].values)
            res.append(label_pred)
        res = pd.concat(res, axis=1)
        prediction = res
        return prediction