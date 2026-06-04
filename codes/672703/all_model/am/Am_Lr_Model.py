import pandas as pd
from sklearn import linear_model
import pickle


class Lr_Model():
    
    def __init__(self):
        self._label_name = 'industry_0930_1129_re_5d'    # 自己算的，未来5日收益率相对于行业平均的超额标准化
        self._random_seed = 1990
        self._modelname =  'LinearRegression_'+ self._label_name
        self._model_path = '/data/group/800020/AlphaDataCenter/Models/'+self._modelname+'/'
        self._prediction_path = '/data/group/800020/AlphaDataCenter/DailyPrediction/am/'+self._modelname+'/'

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