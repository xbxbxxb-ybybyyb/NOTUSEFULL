import os
import sys
import numpy as np
import xgboost as xgb
import pickle
import pandas as pd
import gc
import time


class XGBWrapActor:
    def __init__(self):
        self.random_seed = 1990
        self.model_name = self.__class__.__name__
        self._counts = 1
        self.rank_id = 1


    def prepare_data(self, data_params):
        self.train_x = pd.read_pickle("trainx.pkl")
        self.train_y = pd.read_pickle("trainy.pkl")
        self.model_path = "/home/appadmin"
        self.model_name = "xgb"
        # print(self.train_set.shape, self.train_x.shape, self.train_y.shape)



    def train(self, model_params):
        if False:
            print('model exist:', '{}/{}.pickle'.format(self.model_path, self.model_name))
        else:
            t1 = time.time()
            params = model_params["params"]
            model = {}
            for j in range(self._counts):
                model.update({j: None})
                print("j,",j)
                model[j] = xgb.XGBRegressor(maximize=model_params["maximize"], **params)
                model[j].fit(X=self.train_x, y=self.train_y, verbose=False, eval_set=[(self.train_x, self.train_y)], eval_metric=model_params["eval_metric"])

                filename = '{}/{}.pickle'.format(self.model_path, self.model_name)
                with open(filename, 'wb') as f:
                    pickle.dump(obj=model, file=f)
                print(time.time()-t1)
                del model[j]
                gc.collect()
                os.system("nvidia-smi")
            print("train model success! rank_id: {}".format(self.rank_id))
    
        return


if __name__=="__main__":
    """
    python3.6 
    xgboost==0.90
    V100S
    """
    data_params = {}
        
    model_params = {"params": {'n_estimators': 1000, 'seed': 1993, 'nthread': 1, 'gamma': 5.0, 'min_child_weight': 0.5,
                               'reg_alpha': 50, 'reg_lambda': 10, 'max_depth': 8, 'learning_rate': 0.05,
                               'subsample': 0.9,
                               'colsample_bytree': 0.9, 'tree_method': 'gpu_hist', 'n_gpus':1},
                    "maximize": False,
                    "eval_metric": ["mae"]
                    }
    
    for i in range(200):
        print(i, "*"*40)
        instance = XGBWrapActor()
        instance.prepare_data(data_params)
        instance.train(model_params)