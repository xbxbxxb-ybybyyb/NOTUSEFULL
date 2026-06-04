import numpy as np
import xgboost as xgb
import pickle
import pandas as pd

class XgbSP():
    
    def __init__(self,params):

        self._label_name = params['label_name']
        self._random_seed = 1990
        self._modelname =  params['modelname']
        self._model_path = params['model_path']
        self._prediction_path = params['prediction_path']
        self._counts = 4 
    def revise_model_path(self, path):
        self._model_path = path
    
    def revise_label(self, label):
        self._label_name = label

    def revise_random_seed(self, seed):
        self._random_seed = seed

    def get_model(self, sample, factor_list):
        
        dates = sample['date'].unique().tolist()
        num = int(len(dates)/self._counts)
        np.random.seed(1993)
        np.random.shuffle(dates)
        
        train_dates = []
        for i in range(4):
            train_dates.append(dates[i*num:(i+1)*num])
       
        for j in range(4):
            train_set = sample[sample['date'].isin(train_dates[j])]  
            train_x = train_set[factor_list]
            train_y = train_set[self._label_name]
            maximize = False 
            params = {'n_estimators':1200, 'seed':1993,'nthread':100,'gamma':1.0,'min_child_weight':0.1, 'reg_alpha':500,'reg_lambda':10,
                    'max_depth':5,'learning_rate':0.1,'subsample':0.8,'colsample_bytree':0.8,'tree_method':'gpu_hist'}

            xgb_model = xgb.XGBRegressor (maximize=maximize,**params)
            xgb_model.fit(X=train_x, y=train_y, verbose=False, eval_set=[(train_x, train_y)],
                     eval_metric=['mae'])
            
            filename = self._model_path  +'model_'+str(j)+'.pkl'
            with open(filename, 'wb') as f:
                pickle.dump(obj =xgb_model,file= f)
        
        return
        

    def label_predict(self, sample_daily, factor_list):

        res = []            
        for j in range(4):
            filename = self._model_path  +'model_'+str(j)+'.pkl'
            with open(filename, 'rb') as f:
                model = pickle.load(file=f)
            model.get_booster().set_param({'predictor':'cpu_predictor'})
            test_x = sample_daily[factor_list]
            y_pred = model.predict(test_x)
            label_pred = pd.Series(data=y_pred,index=sample_daily['stock'].values)
            res.append(label_pred)
        res = pd.concat(res, axis=1)
        prediction = res.mean(axis =1)                    
        return prediction