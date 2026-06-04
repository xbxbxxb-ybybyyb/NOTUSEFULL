import pandas as pd
from sklearn import linear_model
import pickle
import numpy as np


class Lr_Model_IC():
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
        datelist = np.sort(np.unique(sample['date'].values))
        sample_valid = sample[sample['date']<datelist[-4]]
        X_train = sample_valid[factor_list]
        y_train = sample_valid[self._label_name]
        model = linear_model.LinearRegression(fit_intercept=True,n_jobs=15)
        # model.fit(X_train,y_train)
        
        IC = sample.groupby('date').apply(lambda x:x[factor_list].corrwith(x['vwap_re_1d'],method='pearson'))
        sign = np.sign(IC.mean())
        IC = IC*sign
        # print(IC.shape)
        ic_std_change = IC.iloc[-20:].std()/IC.iloc[-240:].std()
        ic_down = np.where(IC.values<0,IC.values,np.nan)
        ic_down = pd.DataFrame(ic_down,index=IC.index,columns=IC.columns)
        ic_down_std_change = ic_down.iloc[-20:].std()/ic_down.iloc[-240:].std()
        ind = np.where(~((ic_std_change>=1.2)&(ic_down_std_change>=1.2)))[0]
        print(len(ind))
        model.fit(X_train.iloc[:,ind],y_train)
        coef = model.coef_
        model.coef_ = np.zeros(len(factor_list))
        model.coef_[ind] = coef
        
        filename = self._model_path + 'model.pkl'
        with open(filename, 'wb') as f:
            pickle.dump(obj =model,file= f)

        return 


    def label_predict(self, sample_daily, factor_list):
            
        filename = self._model_path  +'model.pkl'
        with open(filename, 'rb') as f:
            model = pickle.load(file=f)
        # model.coef_[model.coef_>0.02] = 0.02
        # model.coef_[model.coef_<-0.02] = -0.02
        X_test = sample_daily[factor_list]
        y_pred = model.predict(X_test)
        label_pred = pd.Series(data=y_pred,index=sample_daily['stock'].values)
        return label_pred