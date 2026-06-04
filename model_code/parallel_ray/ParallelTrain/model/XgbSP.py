import os
import numpy as np
import xgboost as xgb
import pickle
import pandas as pd
import gc


class XgbSP:

    def __init__(self, params):

        self._label_name = params['label_name']
        self._random_seed = 1990
        self._modelname = params['model_name']
        self._model_path = params['model_path']
        self._prediction_path = params['prediction_path']
        self._strategy_type = params['strategy_type']
        self._factor_list = params['factor_list']
        self._train_date_stock = None
        self._valid_date_stock = None
        self._counts = 1

    def revise_model_path(self, path):
        self._model_path = path

    def revise_label(self, label):
        self._label_name = label

    def revise_random_seed(self, seed):
        self._random_seed = seed

    def get_model(self, sample, train_date):

        dates = sample['date'].unique().tolist()
        num = int(len(dates) / self._counts)
        np.random.seed(1993)
        np.random.shuffle(dates)

        train_dates = dates.copy()

        model = {}
        j = 0
        model.update({j: None})
        train_set = sample[sample['date'].isin(train_dates)]
        train_x = train_set[self._factor_list]
        train_y = train_set[self._label_name]
        maximize = False
        params = {'n_estimators': 100, 'seed': 1993, 'nthread': 10, 'gamma': 5.0, 'min_child_weight': 0.5,
                  'reg_alpha': 50, 'reg_lambda': 10,
                  'max_depth': 8, 'learning_rate': 0.05, 'subsample': 0.9, 'colsample_bytree': 0.9,
                  'tree_method': 'gpu_hist'}

        model[j] = xgb.XGBRegressor(maximize=maximize, **params)
        model[j].fit(X=train_x, y=train_y, verbose=False, eval_set=[(train_x, train_y)], eval_metric=['mae'])

        filename = '{}/{}_{}_{}.pickle'.format(self._model_path, self._modelname, self._strategy_type, train_date)
        with open(filename, 'wb') as f:
            pickle.dump(obj=model, file=f)
        del model  # 2019/8/7 添加，显式地删掉模型，目的是为了释放显存
        gc.collect()
        return

    def label_predict(self, sample_daily, train_date, today_date):
        res = []
        filename = '{}/{}_{}_{}.pickle'.format(self._model_path, self._modelname, self._strategy_type, train_date)
        with open(filename, 'rb') as f:
            model_dict = pickle.load(file=f)
        for j in range(self._counts):
            model = model_dict[j]

            model.get_booster().set_param({'predictor': 'cpu_predictor'})
            test_x = sample_daily[self._factor_list]
            y_pred = model.predict(test_x)
            label_pred = pd.Series(data=y_pred, index=sample_daily['stock'].values)
            res.append(label_pred)
        res = pd.concat(res, axis=1)
        y_pred = res.mean(axis=1).values

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
