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