import pandas as pd
import datetime as dt
from sklearn import linear_model
import pickle


class LinearRegression:
    
    def __init__(self, params):
        self._label_name = params['label_name']
        self._random_seed = 1990
        self._modelname = params['model_name']
        self._model_path = params['model_path']
        self._prediction_path = params['prediction_path']
        self._strategy_type = params['strategy_type']
        self._factor_list = params['factor_list']
        
    def get_model(self, sample, train_date):
        
        X_train = sample[self._factor_list]
        y_train = sample[self._label_name]
        model = linear_model.LinearRegression(fit_intercept=True, n_jobs=15)
        model.fit(X_train, y_train)
  
        filename = '{}/{}_{}_{}.pickle'.format(self._model_path, self._modelname, self._strategy_type, train_date)
        with open(filename, 'wb') as f:
            pickle.dump(obj=model, file=f)
        return

    def label_predict(self, sample_daily, train_date, today_date):
            
        filename = '{}/{}_{}_{}.pickle'.format(self._model_path, self._modelname, self._strategy_type, train_date)
        with open(filename, 'rb') as f:
            model = pickle.load(file=f)

        X_test = sample_daily[self._factor_list]
        y_pred = model.predict(X_test)

        infer_result = {}
        date_time = list(sample_daily['date'])[0]
        key = int(date_time.strftime("%Y%m%d%H%M%S"))
        infer_result[key] = {}
        intra_result = {'Code': list(sample_daily['stock']), 'predict': y_pred.flatten()}
        infer_result[key].update({'infer_result': intra_result})
        signal_name = '{}/signal_{}.pickle'.format(self._prediction_path, today_date)
        with open(signal_name, 'wb') as f:
            pickle.dump(obj=infer_result, file=f)
        return
