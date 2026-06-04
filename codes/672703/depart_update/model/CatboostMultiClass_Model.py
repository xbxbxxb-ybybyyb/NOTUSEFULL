import numpy as np
import pickle
import pandas as pd
import copy
import os
import time
from sklearn.model_selection import train_test_split
import sys
import catboost


class CatboostMultiClass_Model():
    
    def __init__(self,params):
        self._label_name = params['label_name']
        self._random_seed = 1990
        self._modelname =  params['modelname']
        self._model_path = params['model_path']
        self._prediction_path = params['prediction_path']
        self._weight = params['weight']


    def revise_model_path(self, path):
        self._model_path = path
    
    def revise_label(self, label):
        self._label_name = label

    def revise_random_seed(self, seed):
        self._random_seed = seed

    def get_model(self, sample, factor_list):

        sample = sample[sample[self._label_name].values!=0]

        X_in_sample = sample.loc[:,factor_list]
        y_in_sample = sample.loc[:,self._label_name]
        X_train, X_cv, y_train, y_cv = train_test_split(X_in_sample, y_in_sample, 
            test_size = 0.1, random_state = self._random_seed, stratify = y_in_sample)

        model = catboost.CatBoostClassifier(iterations=3000,thread_count=-1,depth=5,
                                        eval_metric='MultiClassOneVsAll',
                                        random_seed = self._random_seed,
                                        learning_rate = 0.015,
                                        logging_level='Verbose', nan_mode='Forbidden',
                                        loss_function = 'MultiClassOneVsAll',
                                        early_stopping_rounds=20,
                                       )
        model.fit(X_train,y_train,eval_set=(X_cv, y_cv),plot=False,verbose=False)
        
        filename = self._model_path +'model.pkl'
        with open(filename, 'wb') as f:
            pickle.dump(obj =model,file= f)

        return

        

    def label_predict(self, sample_daily, factor_list):

        filename = self._model_path +'model.pkl'
        with open(filename, 'rb') as f:
            model = pickle.load(file=f)

        X = sample_daily[factor_list]
        y_pred = (np.array(self._weight)*model.predict_proba(X)).sum(axis=1)
        prediction = pd.Series(data=y_pred,index=sample_daily['stock'].values)
        return prediction
