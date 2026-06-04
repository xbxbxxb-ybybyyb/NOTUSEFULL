import pandas as pd
from sklearn import linear_model
import pickle


class Lr_Model():
    
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
        
        X_train = sample[factor_list]
        y_train = sample[self._label_name]
        model = linear_model.LinearRegression(fit_intercept=True,n_jobs=15)
        model.fit(X_train,y_train)
        
        filename = self._model_path + 'model.pkl'
        with open(filename, 'wb') as f:
            pickle.dump(obj =model,file= f)
        return 


    def label_predict(self, sample_daily, factor_list):
            
        filename = self._model_path  +'model.pkl'
        with open(filename, 'rb') as f:
            model = pickle.load(file=f)
        
        X_test = sample_daily[factor_list]
        y_pred = model.predict(X_test)
        label_pred = pd.Series(data=y_pred,index=sample_daily['stock'].values)
        return label_pred