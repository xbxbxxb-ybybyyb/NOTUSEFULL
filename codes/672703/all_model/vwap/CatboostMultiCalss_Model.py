import numpy as np
import pickle
import pandas as pd
import copy
import os
import time
from sklearn.model_selection import train_test_split
from sklearn import decomposition
import sys
import catboost

class CatboostMultiCalss_Model():
    
    def __init__(self):

        self._label_name = 'bin_vwap_re_1d'
        self._random_seed = 2019
        self._modelname =  'CatboostMultiCalss_'+ self._label_name
        self._model_path = '/data/group/800020/AlphaDataCenter/Models/'+self._modelname+'/'
        self._prediction_path = '/data/group/800020/AlphaDataCenter/DailyPrediction/'+self._modelname+'/'
        self._myfile_path = '/data/group/800020/AlphaDataCenter/AlphaExperiment/Test/'

    def revise_model_path(self, path):
        self._model_path = path
    
    def revise_label(self, label):
        self._label_name = label

    def revise_random_seed(self, seed):
        self._random_seed = seed

    def get_model(self, sample, factor_list):
        
        factor_list1= pd.read_excel(self._myfile_path + 'myfactor.xlsx',header=None).fillna(0)
        factor_list1= factor_list1.values.reshape((1,factor_list1.size))
        factor_list1 = factor_list1[factor_list1!=0].astype('str').tolist()
        factor_exist = sample.columns.tolist()
        factor_list1 = list(set(factor_list1)&set(factor_exist))

        sample = sample[sample[self._label_name].values!=0]

        X_in_sample = data_train.loc[:,factor_list1]
        y_in_sample = data_train.loc[:,self._label_name]
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

        factor_list1= pd.read_excel(self._myfile_path + 'myfactor.xlsx',header=None).fillna(0)
        factor_list1= factor_list1.values.reshape((1,factor_list1.size))
        factor_list1 = factor_list1[factor_list1!=0].astype('str').tolist()
        factor_exist = sample_daily.columns.tolist()
        factor_list1 = list(set(factor_list1)&set(factor_exist))
        
        filename = self._model_path +'model.pkl'
        with open(filename, 'rb') as f:
            model = pickle.load(file=f)

        X = sample_daily[factor_list1]
        weight = [-6,-2,0,0,0,10]
        y_pred = (np.array(weight)*model.predict_proba(X)).sum(axis=1)
        prediction = pd.Series(data=y_pred,index=sample_daily['stock'].values)
        return prediction
